"""Общие настройки тестов: путь к src/, заглушки и драйверы."""
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(os.path.dirname(TESTS_DIR), "src")
DATA_DIR = os.path.join(TESTS_DIR, "data")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import mapping  # noqa: E402
import processing_module  # noqa: E402
import protocol  # noqa: E402


def load_cases():
    """Тестовые наборы из tests/data/cases.json."""
    path = os.path.join(DATA_DIR, "cases.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


class Reader:
    """Подменяет input(): отдаёт заранее заданные строки."""

    def __init__(self, lines):
        self.lines = list(lines)

    def __call__(self, prompt=""):
        if not self.lines:
            raise EOFError
        return self.lines.pop(0)


# ---------- Драйвер (шаг 1): имитирует модуль ввода ----------
def processing_driver(matrix):
    """Драйвер: отправляет модулю обработки JSON-запрос, возвращает ответ.

    Заменяет ещё не подключённый модуль ввода (риск R1).
    """
    rows, cols = len(matrix), len(matrix[0])
    request = protocol.build_request(rows, cols, matrix)
    return processing_module.handle_request(request)


# ---------- Заглушки (шаги 2-3) ----------
class OutputStub:
    """Заглушка модуля вывода: запоминает полученные данные."""

    def __init__(self):
        self.received = None

    def __call__(self, result):
        self.received = result


def input_stub(matrix):
    """Заглушка модуля ввода: фиксированная матрица без консоли."""
    return mapping.InputData(n=len(matrix), m=len(matrix[0]), matrix=matrix)


def inprocess_runner(request_path, response_path, timeout):
    """Заглушка запуска: модуль обработки вызывается как функция."""
    processing_module.process_files(request_path, response_path)
