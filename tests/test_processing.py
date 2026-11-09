"""Модульные тесты модуля обработки и драйвер шага 1 (риск R1)."""
import unittest

import helpers
import processing_module
import protocol


class ProcessingUnitTests(unittest.TestCase):

    def test_find_zero_columns(self):
        matrix = [[1.0, 0.0, 3.0], [4.0, 5.0, 0.0]]
        self.assertEqual(processing_module.find_zero_columns(matrix), [1, 2])

    def test_empty_matrix(self):
        self.assertEqual(processing_module.find_zero_columns([]), [])

    def test_sum_uses_exact_summation(self):
        # sum() на Python <= 3.11 даёт 0.9999999999999999, fsum() — 1.0
        matrix = [[0.1]] * 10 + [[0.0]]
        _, total = processing_module.sum_zero_columns(matrix)
        self.assertEqual(total, 1.0)


class ProcessingDriverTests(unittest.TestCase):
    """Шаг 1: модуль обработки проверяется драйвером через JSON."""

    def test_cases_from_json(self):
        for case in helpers.load_cases():
            with self.subTest(case["name"]):
                response = helpers.processing_driver(case["matrix"])
                self.assertEqual(response["type"], protocol.MSG_RESPONSE)
                payload = response["payload"]
                self.assertEqual(payload["zero_columns"],
                                 case["zero_columns"])
                self.assertAlmostEqual(payload["sum"], case["sum"])

    def test_response_is_valid_message(self):
        response = helpers.processing_driver([[0, 1], [2, 3]])
        columns, total = protocol.parse_response(response)
        self.assertEqual(columns, [1])
        self.assertEqual(total, 2.0)


class ProcessingErrorTests(unittest.TestCase):

    def test_wrong_dimensions_give_error_message(self):
        request = protocol.build_request(3, 2, [[1, 2], [3, 4]])
        response = processing_module.handle_request(request)
        self.assertEqual(response["type"], protocol.MSG_ERROR)
        self.assertEqual(response["payload"]["code"],
                         protocol.ERR_INVALID_DATA)

    def test_ragged_matrix(self):
        request = protocol.build_request(2, 2, [[1, 2], [3]])
        response = processing_module.handle_request(request)
        self.assertEqual(response["payload"]["code"],
                         protocol.ERR_INVALID_DATA)

    def test_non_numeric_value(self):
        request = protocol.build_request(1, 2, [[1, "a"]])
        response = processing_module.handle_request(request)
        self.assertEqual(response["payload"]["code"],
                         protocol.ERR_INVALID_DATA)

    def test_incompatible_version(self):
        request = protocol.build_request(1, 1, [[0]])
        request["version"] = "2.0"
        response = processing_module.handle_request(request)
        self.assertEqual(response["payload"]["code"], protocol.ERR_VERSION)

    def test_not_an_object(self):
        response = processing_module.handle_request([1, 2, 3])
        self.assertEqual(response["payload"]["code"], protocol.ERR_PROTOCOL)

    def test_wrong_message_type(self):
        request = protocol.build_request(1, 1, [[0]])
        request["type"] = "something_else"
        response = processing_module.handle_request(request)
        self.assertEqual(response["payload"]["code"], protocol.ERR_PROTOCOL)


if __name__ == "__main__":
    unittest.main()
