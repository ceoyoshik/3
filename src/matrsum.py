"""МатрСум-11: интеграция модулей (шаг 2: ввод и обработка).

Для вещественной матрицы n x m находит сумму элементов только тех
столбцов, которые содержат хотя бы один нулевой элемент.

Модуль ввода и модуль вывода работают в основном процессе, модуль
обработки запускается отдельным процессом; обмен идёт JSON-файлами
(см. docs/integration.md).
"""
import os
import subprocess
import sys

import mapping
import protocol
from errors import ModuleTimeoutError, ModuleUnavailableError

DEFAULT_TIMEOUT = 10.0

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
