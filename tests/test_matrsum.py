import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import matrsum  # noqa: E402


class ColumnSumTests(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(matrsum.column_sum([[1.0, 0.0], [2.0, 3.0]]),
                         ([1], 3.0))

    def test_no_zero(self):
        self.assertEqual(matrsum.column_sum([[1.0, 2.0]]), ([], 0))


if __name__ == "__main__":
    unittest.main()
