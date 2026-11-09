"""Тесты протокола обмена (JSON) и сопоставления данных."""
import os
import tempfile
import unittest

import helpers
import mapping
import protocol
from errors import (InputDataError, ModuleUnavailableError, ProtocolError,
                    VersionConflictError)


class EnvelopeTests(unittest.TestCase):

    def test_request_roundtrip(self):
        request = protocol.build_request(2, 2, [[1, 0], [2, 3]])
        self.assertEqual(protocol.parse_request(request),
                         [[1.0, 0.0], [2.0, 3.0]])

    def test_missing_field(self):
        request = protocol.build_request(1, 1, [[0]])
        del request["payload"]
        with self.assertRaises(ProtocolError):
            protocol.parse_request(request)

    def test_bad_version_format(self):
        for version in ("1", "1.x", 1, "1.0.0", ""):
            request = protocol.build_request(1, 1, [[0]])
            request["version"] = version
            with self.subTest(version=version):
                with self.assertRaises(ProtocolError):
                    protocol.parse_request(request)

    def test_minor_version_is_compatible(self):
        request = protocol.build_request(1, 1, [[0]])
        request["version"] = "1.7"
        self.assertEqual(protocol.parse_request(request), [[0.0]])

    def test_major_version_conflict(self):
        request = protocol.build_request(1, 1, [[0]])
        request["version"] = "2.0"
        with self.assertRaises(VersionConflictError):
            protocol.parse_request(request)

    def test_bool_is_not_a_number(self):
        request = protocol.build_request(1, 1, [[True]])
        with self.assertRaises(InputDataError):
            protocol.parse_request(request)

    def test_size_out_of_range(self):
        request = protocol.build_request(0, 1, [])
        with self.assertRaises(InputDataError):
            protocol.parse_request(request)

    def test_non_integer_size(self):
        request = protocol.build_request(1.5, 1, [[0]])
        with self.assertRaises(ProtocolError):
            protocol.parse_request(request)

    def test_error_message_becomes_exception(self):
        cases = [(protocol.ERR_INVALID_DATA, InputDataError),
                 (protocol.ERR_VERSION, VersionConflictError),
                 (protocol.ERR_PROTOCOL, ProtocolError)]
        for code, exception in cases:
            message = protocol.build_error(code, "текст")
            with self.subTest(code=code):
                with self.assertRaises(exception):
                    protocol.parse_response(message)

    def test_response_validation(self):
        bad = protocol.build_response(["a"], 1.0)
        with self.assertRaises(ProtocolError):
            protocol.parse_response(bad)
        bad = protocol.build_response([1], float("inf"))
        with self.assertRaises(ProtocolError):
            protocol.parse_response(bad)


class FileExchangeTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "msg.json")

    def test_write_and_read(self):
        message = protocol.build_request(1, 2, [[0, 1.5]])
        protocol.dump_json(self.path, message)
        self.assertEqual(protocol.load_json(self.path), message)
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_missing_file_means_unavailable(self):
        with self.assertRaises(ModuleUnavailableError):
            protocol.load_json(self.path)

    def test_broken_json(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{не json")
        with self.assertRaises(ProtocolError):
            protocol.load_json(self.path)

    def test_nan_constant_rejected_on_read(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write('{"version": "1.0", "payload": NaN}')
        with self.assertRaises(ProtocolError):
            protocol.load_json(self.path)

    def test_nan_rejected_on_write(self):
        message = protocol.build_request(1, 1, [[float("nan")]])
        with self.assertRaises(ProtocolError):
            protocol.dump_json(self.path, message)

    def test_unwritable_directory(self):
        bad_path = os.path.join(self.tmp.name, "нет", "msg.json")
        with self.assertRaises(ModuleUnavailableError):
            protocol.dump_json(bad_path, protocol.build_request(1, 1, [[0]]))


class MappingTests(unittest.TestCase):

    def test_input_to_request_maps_fields(self):
        data = helpers.input_stub([[1.0, 0.0, 2.0], [3.0, 4.0, 5.0]])
        payload = mapping.input_to_request(data)["payload"]
        self.assertEqual((payload["rows"], payload["cols"]), (2, 3))
        self.assertEqual(payload["matrix"], data.matrix)

    def test_columns_become_one_based(self):
        response = mapping.processing_to_response([0, 2], 5)
        payload = response["payload"]
        self.assertEqual(payload["zero_columns"], [1, 3])
        self.assertIsInstance(payload["sum"], float)

    def test_response_to_output(self):
        response = mapping.processing_to_response([1], 2.5)
        output = mapping.response_to_output(response)
        self.assertEqual(output.columns, (2,))
        self.assertEqual(output.total, 2.5)


if __name__ == "__main__":
    unittest.main()
