"""Модуль обработки: сумма элементов столбцов, содержащих нуль.

Может использоваться как библиотека (handle_request) и как отдельная
программа, обменивающаяся с остальной системой JSON-файлами::

    python processing_module.py --request req.json --response resp.json
"""
import argparse
import math
import sys

import mapping
import protocol
from errors import (InputDataError, IntegrationError, ProtocolError,
                    VersionConflictError)


def find_zero_columns(matrix):
    """Индексы (с 0) столбцов, где есть хотя бы один нулевой элемент."""
    if not matrix:
        return []
    return [j for j in range(len(matrix[0]))
            if any(row[j] == 0 for row in matrix)]


def sum_zero_columns(matrix):
    """Возвращает (индексы столбцов с нулём, сумма их элементов)."""
    columns = find_zero_columns(matrix)
    total = math.fsum(row[j] for row in matrix for j in columns)
    return columns, total


def handle_request(request):
    """Обрабатывает matrix_request, всегда возвращает сообщение-ответ."""
    try:
        matrix = protocol.parse_request(request)
        columns, total = sum_zero_columns(matrix)
        return mapping.processing_to_response(columns, total)
    except VersionConflictError as exc:
        return protocol.build_error(protocol.ERR_VERSION, str(exc))
    except InputDataError as exc:
        return protocol.build_error(protocol.ERR_INVALID_DATA, str(exc))
    except ProtocolError as exc:
        return protocol.build_error(protocol.ERR_PROTOCOL, str(exc))


def process_files(request_path, response_path):
    """Читает запрос, пишет ответ. True, если ответ не является error."""
    try:
        response = handle_request(protocol.load_json(request_path))
    except ProtocolError as exc:
        response = protocol.build_error(protocol.ERR_PROTOCOL, str(exc))
    protocol.dump_json(response_path, response)
    return response["type"] != protocol.MSG_ERROR


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--request", required=True,
                        help="файл с сообщением matrix_request")
    parser.add_argument("--response", required=True,
                        help="файл для сообщения-ответа")
    args = parser.parse_args(argv)
    try:
        ok = process_files(args.request, args.response)
    except IntegrationError as exc:
        print(f"Модуль обработки: {exc}", file=sys.stderr)
        return protocol.EXIT_FAILURE
    return protocol.EXIT_OK if ok else protocol.EXIT_REPORTED_ERROR


if __name__ == "__main__":
    sys.exit(main())
