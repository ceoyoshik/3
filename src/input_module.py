"""Модуль ввода: чтение матрицы n x m с консоли и проверка данных."""
import math

from errors import InputDataError
from mapping import InputData
from protocol import MAX_DIM


def parse_size(text, name):
    """Разбирает размерность матрицы (целое от 1 до MAX_DIM)."""
    text = text.strip()
    try:
        value = int(text)
    except ValueError:
        raise InputDataError(
            f"{name} должно быть целым числом, получено {text!r}") from None
    if not 1 <= value <= MAX_DIM:
        raise InputDataError(f"{name} должно быть от 1 до {MAX_DIM}")
    return value


def parse_row(text, m, index):
    """Разбирает строку матрицы: ровно m вещественных чисел."""
    tokens = text.split()
    if len(tokens) != m:
        raise InputDataError(
            f"строка {index}: ожидалось {m} элементов, "
            f"получено {len(tokens)}")
    row = []
    for token in tokens:
        try:
            value = float(token.replace(",", "."))
        except ValueError:
            raise InputDataError(
                f"строка {index}: {token!r} не является числом") from None
        if not math.isfinite(value):
            raise InputDataError(
                f"строка {index}: значение {token!r} недопустимо")
        row.append(value)
    return row


def _ask(read, prompt):
    try:
        return read(prompt)
    except EOFError:
        raise InputDataError("ввод прерван: данные закончились") from None


def read_matrix(read=input):
    """Запрашивает размеры и элементы, возвращает InputData."""
    n = parse_size(_ask(read, "Количество строк n: "), "n")
    m = parse_size(_ask(read, "Количество столбцов m: "), "m")
    matrix = []
    for i in range(1, n + 1):
        line = _ask(read, f"Строка {i} ({m} чисел через пробел): ")
        matrix.append(parse_row(line, m, i))
    return InputData(n=n, m=m, matrix=matrix)
