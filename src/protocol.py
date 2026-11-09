"""Протокол обмена между модулями: JSON-сообщения (версия 1.x).

Формат сообщения (конверт)::

    {"version": "1.0", "type": "...", "payload": {...}}

Типы сообщений: matrix_request (ввод -> обработка),
sum_response (обработка -> вывод) и error (сообщение об ошибке).
"""
import json
import math
import os
import re

from errors import (InputDataError, ModuleUnavailableError, ProtocolError,
                    VersionConflictError)

PROTOCOL_VERSION = "1.0"
SUPPORTED_MAJOR = 1

MSG_REQUEST = "matrix_request"
MSG_RESPONSE = "sum_response"
MSG_ERROR = "error"

ERR_INVALID_DATA = "invalid_data"
ERR_PROTOCOL = "protocol_error"
ERR_VERSION = "version_conflict"

MAX_DIM = 1000

# Коды завершения модуля обработки (часть интерфейса между модулями)
EXIT_OK = 0
EXIT_REPORTED_ERROR = 10  # в файл ответа записано сообщение error
EXIT_FAILURE = 3          # модуль не смог даже записать ответ


def is_number(value):
    """Конечное число (int или float), не bool."""
    return (isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value))


def is_int(value):
    """Целое число, не bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def build_request(rows, cols, matrix):
    """Собирает сообщение matrix_request."""
    return {
        "version": PROTOCOL_VERSION,
        "type": MSG_REQUEST,
        "payload": {
            "rows": rows,
            "cols": cols,
            "matrix": [list(row) for row in matrix],
        },
    }


def build_response(zero_columns, total):
    """Собирает сообщение sum_response (номера столбцов с 1)."""
    return {
        "version": PROTOCOL_VERSION,
        "type": MSG_RESPONSE,
        "payload": {"zero_columns": list(zero_columns), "sum": total},
    }


def build_error(code, message):
    """Собирает сообщение об ошибке."""
    return {
        "version": PROTOCOL_VERSION,
        "type": MSG_ERROR,
        "payload": {"code": code, "message": message},
    }


def check_version(version):
    """Проверяет совместимость версии протокола (major должен совпасть)."""
    if not isinstance(version, str):
        raise ProtocolError("поле version должно быть строкой")
    parts = version.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ProtocolError(f"неверный формат версии: {version!r}")
    if int(parts[0]) != SUPPORTED_MAJOR:
        raise VersionConflictError(
            f"несовместимая версия протокола {version}, "
            f"поддерживается {SUPPORTED_MAJOR}.x")


def raise_from_error(payload):
    """Превращает сообщение error в соответствующее исключение."""
    code = payload.get("code")
    message = str(payload.get("message", "причина не указана"))
    if code == ERR_INVALID_DATA:
        raise InputDataError(message)
    if code == ERR_VERSION:
        raise VersionConflictError(message)
    raise ProtocolError(message)


def validate_envelope(message, expected_type):
    """Проверяет конверт сообщения и возвращает payload."""
    if not isinstance(message, dict):
        raise ProtocolError("сообщение должно быть JSON-объектом")
    for key in ("version", "type", "payload"):
        if key not in message:
            raise ProtocolError(f"в сообщении нет поля {key!r}")
    check_version(message["version"])
    payload = message["payload"]
    if not isinstance(payload, dict):
        raise ProtocolError("поле payload должно быть объектом")
    if message["type"] == MSG_ERROR and expected_type != MSG_ERROR:
        raise_from_error(payload)
    if message["type"] != expected_type:
        raise ProtocolError(
            f"ожидался тип {expected_type!r}, получен {message['type']!r}")
    return payload


def parse_request(message):
    """Проверяет matrix_request и возвращает матрицу (список строк)."""
    payload = validate_envelope(message, MSG_REQUEST)
    rows, cols = payload.get("rows"), payload.get("cols")
    matrix = payload.get("matrix")
    if not (is_int(rows) and is_int(cols)):
        raise ProtocolError("rows и cols должны быть целыми числами")
    if not isinstance(matrix, list):
        raise ProtocolError("matrix должна быть списком строк")
    if not (1 <= rows <= MAX_DIM and 1 <= cols <= MAX_DIM):
        raise InputDataError(f"размеры должны быть от 1 до {MAX_DIM}")
    if len(matrix) != rows:
        raise InputDataError(
            f"rows={rows}, но в matrix строк: {len(matrix)}")
    for index, row in enumerate(matrix, start=1):
        if not isinstance(row, list) or len(row) != cols:
            raise InputDataError(
                f"строка {index} не содержит {cols} элементов")
        if not all(is_number(value) for value in row):
            raise InputDataError(
                f"строка {index} содержит нечисловое значение")
    return [[float(value) for value in row] for row in matrix]


def parse_response(message):
    """Проверяет sum_response, возвращает (номера столбцов, сумма)."""
    payload = validate_envelope(message, MSG_RESPONSE)
    columns, total = payload.get("zero_columns"), payload.get("sum")
    if not isinstance(columns, list) or not all(map(is_int, columns)):
        raise ProtocolError("zero_columns должен быть списком целых")
    if not is_number(total):
        raise ProtocolError("sum должна быть конечным числом")
    return columns, float(total)


def _reject_constant(name):
    raise ProtocolError(f"недопустимая константа в JSON: {name}")


def _compact_arrays(text):
    """Склеивает массивы чисел в одну строку (строки матрицы читаемее)."""
    return re.sub(
        r"\[\s*([^\[\]{}]*?)\s*\]",
        lambda found: "[" + re.sub(r"\s*\n\s*", " ", found.group(1)) + "]",
        text)


def dump_json(path, message):
    """Атомарно записывает сообщение в файл обмена."""
    temp_path = path + ".tmp"
    try:
        text = json.dumps(message, ensure_ascii=False, indent=2,
                          allow_nan=False)
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(_compact_arrays(text) + "\n")
        os.replace(temp_path, path)
    except ValueError as exc:
        raise ProtocolError(f"сообщение нельзя записать: {exc}") from None
    except OSError as exc:
        raise ModuleUnavailableError(
            f"не удалось записать файл обмена: {exc}") from None


def load_json(path):
    """Читает сообщение из файла обмена."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle, parse_constant=_reject_constant)
    except FileNotFoundError:
        raise ModuleUnavailableError(
            f"файл обмена не найден: {path}") from None
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProtocolError(f"некорректный JSON: {exc}") from None
    except OSError as exc:
        raise ModuleUnavailableError(
            f"не удалось прочитать файл обмена: {exc}") from None
