"""Шаг 3 интеграции: все три модуля, обработка запускается процессом."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import helpers
import matrsum
import output_module


class Step3FullSystemTests(unittest.TestCase):
    """Шаг 3: все три модуля, обработка запускается как процесс."""

    def run_main(self, lines, argv=()):
        out, err = [], []
        code = matrsum.main(list(argv), read=helpers.Reader(lines),
                            write=out.append, write_err=err.append)
        return code, "\n".join(out), "\n".join(err)

    def test_full_run_with_subprocess(self):
        code, out, err = self.run_main(
            ["3", "4", "1 0 2 5", "3 4 0 6", "7 8 9 1"])
        self.assertEqual(code, matrsum.EXIT_SUCCESS)
        self.assertEqual(err, "")
        self.assertIn("2, 3", out)
        self.assertTrue(out.endswith("23.000"))

    def test_no_zero_columns(self):
        code, out, _ = self.run_main(["2", "2", "1 2", "3 4"])
        self.assertEqual(code, matrsum.EXIT_SUCCESS)
        self.assertIn("нет", out)

    def test_decimal_comma_end_to_end(self):
        code, out, _ = self.run_main(["2", "2", "0 1,5", "2 2,25"])
        self.assertEqual(code, matrsum.EXIT_SUCCESS)
        self.assertTrue(out.endswith("2.000"))

    def test_workdir_keeps_json_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = os.path.join(tmp, "exchange")
            code, _, _ = self.run_main(
                ["1", "2", "0 5"], argv=["--workdir", workdir])
            self.assertEqual(code, matrsum.EXIT_SUCCESS)
            self.assertTrue(os.path.exists(
                os.path.join(workdir, "request.json")))
            self.assertTrue(os.path.exists(
                os.path.join(workdir, "response.json")))

    def test_bad_input_returns_data_error(self):
        code, out, err = self.run_main(["2", "abc"])
        self.assertEqual(code, matrsum.EXIT_DATA_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка данных", err)

    def test_output_module_receives_integrated_result(self):
        data = helpers.input_stub([[0.0, 1.0 / 3.0], [0.0, 2.0 / 3.0]])
        with tempfile.TemporaryDirectory() as tmp:
            result = matrsum.integrate(data, tmp)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            output_module.show(result)
        self.assertIn("0.000", buffer.getvalue())

    def test_big_matrix(self):
        size = 200
        matrix = [[float(i + 1)] * size for i in range(size)]
        matrix[0][0] = 0.0
        data = helpers.input_stub(matrix)
        with tempfile.TemporaryDirectory() as tmp:
            result = matrsum.integrate(data, tmp)
        self.assertEqual(result.columns, (1,))
        self.assertAlmostEqual(result.total, sum(range(2, size + 1)))


if __name__ == "__main__":
    unittest.main()
