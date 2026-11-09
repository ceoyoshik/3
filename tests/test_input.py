"""Тесты модуля ввода."""
import unittest

import helpers
import input_module
from errors import InputDataError


class InputTests(unittest.TestCase):

    def test_read_matrix(self):
        reader = helpers.Reader(["2", "3", "1 0 2", "3 4 5"])
        data = input_module.read_matrix(reader)
        self.assertEqual((data.n, data.m), (2, 3))
        self.assertEqual(data.matrix, [[1.0, 0.0, 2.0], [3.0, 4.0, 5.0]])

    def test_decimal_comma_is_normalized(self):
        reader = helpers.Reader(["1", "2", "1,5 0"])
        self.assertEqual(input_module.read_matrix(reader).matrix,
                         [[1.5, 0.0]])

    def test_extra_spaces_are_ignored(self):
        reader = helpers.Reader([" 1 ", " 2 ", "  3    0  "])
        self.assertEqual(input_module.read_matrix(reader).matrix,
                         [[3.0, 0.0]])

    def test_bad_sizes(self):
        for text in ("0", "-1", "abc", "", "1.5", "1001"):
            with self.subTest(text=text):
                with self.assertRaises(InputDataError):
                    input_module.parse_size(text, "n")

    def test_wrong_number_of_elements(self):
        with self.assertRaises(InputDataError):
            input_module.parse_row("1 2", 3, 1)

    def test_not_a_number(self):
        with self.assertRaises(InputDataError):
            input_module.parse_row("1 abc", 2, 1)

    def test_nan_and_inf_rejected(self):
        for token in ("nan", "inf", "-inf", "1e999"):
            with self.subTest(token=token):
                with self.assertRaises(InputDataError):
                    input_module.parse_row(token, 1, 1)

    def test_input_interrupted(self):
        with self.assertRaises(InputDataError):
            input_module.read_matrix(helpers.Reader(["2", "2", "1 2"]))


if __name__ == "__main__":
    unittest.main()
