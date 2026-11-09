"""МатрСум-11: интеграция модулей ввода, обработки и вывода.

Для вещественной матрицы n x m находит сумму элементов только тех
столбцов, которые содержат хотя бы один нулевой элемент.

Модуль ввода и модуль вывода работают в основном процессе, модуль
обработки запускается отдельным процессом; обмен идёт JSON-файлами
(см. docs/integration.md).
"""
import argparse
import os
import subprocess
import sys
import tempfile

import input_module
import mapping
import output_module
import protocol
from errors import (InputDataError, IntegrationError, ModuleTimeoutError,
                    ModuleUnavailableError)

DEFAULT_TIMEOUT = 30.0

EXIT_SUCCESS = 0
EXIT_DATA_ERROR = 1
EXIT_INTEGRATION_ERROR = 2

PROCESSING_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "processing_module.py")


def run_processing_subprocess(request_path, response_path, timeout,
                              script=PROCESSING_SCRIPT):
    """Запускает модуль обработки отдельным процессом с тайм-аутом."""
    command = [sys.executable, script,
               "--request", request_path, "--response", response_path]
    try:
        completed = subprocess.run(command, capture_output=True,
                                   text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ModuleTimeoutError(
            f"модуль обработки не ответил за {timeout:g} с") from None
    except OSError as exc:
        raise ModuleUnavailableError(
            f"не удалось запустить модуль обработки: {exc}") from None
    if completed.returncode not in (protocol.EXIT_OK,
                                    protocol.EXIT_REPORTED_ERROR):
        details = completed.stderr.strip() or "без сообщения"
        raise ModuleUnavailableError(
            f"модуль обработки завершился с кодом "
            f"{completed.returncode}: {details}")


def integrate(data, workdir, timeout=DEFAULT_TIMEOUT,
              runner=run_processing_subprocess):
    """Передаёт данные модулю обработки и возвращает OutputData.

    runner(request_path, response_path, timeout) — способ вызова модуля
    обработки; в тестах заменяется заглушкой.
    """
    request_path = os.path.join(workdir, "request.json")
    response_path = os.path.join(workdir, "response.json")
    protocol.dump_json(request_path, mapping.input_to_request(data))

    runner(request_path, response_path, timeout)
    return mapping.response_to_output(protocol.load_json(response_path))


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="тайм-аут модуля обработки, с")
    parser.add_argument("--workdir",
                        help="каталог для файлов обмена (по умолчанию "
                             "временный)")
    return parser


def main(argv=None, read=input, write=print, write_err=None,
         runner=run_processing_subprocess):
    """Точка входа. Возвращает код завершения."""
    if write_err is None:
        def write_err(text):
            print(text, file=sys.stderr)
    args = build_parser().parse_args(argv)
    try:
        data = input_module.read_matrix(read)
        if args.workdir:
            os.makedirs(args.workdir, exist_ok=True)
            result = integrate(data, args.workdir, timeout=args.timeout,
                               runner=runner)
        else:
            with tempfile.TemporaryDirectory() as workdir:
                result = integrate(data, workdir, timeout=args.timeout,
                                   runner=runner)
    except InputDataError as exc:
        write_err(f"Ошибка данных: {exc}")
        return EXIT_DATA_ERROR
    except IntegrationError as exc:
        write_err(f"Ошибка интеграции: {exc}")
        return EXIT_INTEGRATION_ERROR
    output_module.show(result, write)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
