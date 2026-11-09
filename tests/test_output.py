"""Тесты модуля вывода."""
import unittest

import output_module
from mapping import OutputData


class OutputTests(unittest.TestCase):

    def test_format_with_columns(self):
        text = output_module.format_result(OutputData((2, 3), 23.0))
        self.assertEqual(text, "Столбцы с нулевым элементом: 2, 3\n"
                               "Сумма элементов этих столбцов: 23.000")

    def test_format_without_columns(self):
        text = output_module.format_result(OutputData((), 0.0))
        self.assertIn("нет", text)
        self.assertTrue(text.endswith("0.000"))

    def test_precision_is_three_digits(self):
        self.assertEqual(output_module.format_number(1 / 3), "0.333")
        self.assertEqual(output_module.format_number(12), "12.000")

    def test_negative_zero_is_not_printed(self):
        self.assertEqual(output_module.format_number(-0.0001), "0.000")
        self.assertEqual(output_module.format_number(-0.0), "0.000")

    def test_show_uses_write(self):
        lines = []
        output_module.show(OutputData((1,), 1.0), lines.append)
        self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
