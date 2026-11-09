"""Шаг 2 интеграции: ввод + обработка через JSON-файлы (вывод — заглушка)."""
import os
import tempfile
import unittest

import helpers
import input_module
import matrsum


class Step2InputProcessingTests(unittest.TestCase):
    """Шаг 2: ввод + обработка, модуль вывода заменён заглушкой."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_input_to_processing_with_output_stub(self):
        stub = helpers.OutputStub()
        reader = helpers.Reader(["3", "4", "1 0 2 5", "3 4 0 6", "7 8 9 1"])
        data = input_module.read_matrix(reader)
        result = matrsum.integrate(data, self.tmp.name,
                                   runner=helpers.inprocess_runner)
        stub(result)
        self.assertEqual(stub.received.columns, (2, 3))
        self.assertAlmostEqual(stub.received.total, 23.0)

    def test_exchange_files_are_created(self):
        data = helpers.input_stub([[0, 1], [2, 3]])
        matrsum.integrate(data, self.tmp.name,
                          runner=helpers.inprocess_runner)
        names = sorted(os.listdir(self.tmp.name))
        self.assertEqual(names, ["request.json", "response.json"])

    def test_all_cases_through_json_files(self):
        for case in helpers.load_cases():
            with self.subTest(case["name"]):
                data = helpers.input_stub(case["matrix"])
                result = matrsum.integrate(
                    data, self.tmp.name, runner=helpers.inprocess_runner)
                self.assertEqual(list(result.columns), case["zero_columns"])
                self.assertAlmostEqual(result.total, case["sum"])


if __name__ == "__main__":
    unittest.main()
