"""Сопоставление объектов данных (mapping) между модулями.

Структуры данных модулей:

* модуль ввода     -> InputData(n, m, matrix);
* модуль обработки -> (индексы столбцов с 0, сумма);
* модуль вывода    -> OutputData(columns, total).

Правила преобразования см. docs/integration.md (таблица соответствия).
"""
from dataclasses import dataclass
from typing import List, Tuple

import protocol


@dataclass(frozen=True)
class InputData:
    """Результат работы модуля ввода."""
    n: int
    m: int
    matrix: List[List[float]]


@dataclass(frozen=True)
class OutputData:
    """Данные, которые принимает модуль вывода."""
    columns: Tuple[int, ...]
    total: float


def input_to_request(data):
    """InputData -> matrix_request (n -> rows, m -> cols)."""
    return protocol.build_request(data.n, data.m, data.matrix)


def processing_to_response(zero_columns, total):
    """Результат обработки -> sum_response.

    Индексы столбцов приводятся от нумерации с 0 к нумерации с 1,
    сумма приводится к float.
    """
    return protocol.build_response([j + 1 for j in zero_columns],
                                   float(total))


def response_to_output(message):
    """sum_response -> OutputData (список -> кортеж, число -> float)."""
    columns, total = protocol.parse_response(message)
    return OutputData(columns=tuple(columns), total=total)
