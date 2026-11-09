"""Тесты обработки исключительных ситуаций при интеграции (уровень 3)."""
import contextlib
import functools
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import helpers
import matrsum
import protocol
from errors import (InputDataError, ModuleTimeoutError,
                    ModuleUnavailableError, ProtocolError,
                    VersionConflictError)


def write_script(directory, body):
    path = os.path.join(directory, "fake_module.py")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


class ExceptionTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = helpers.input_stub([[0.0, 1.0], [2.0, 3.0]])

    def integrate(self, runner, **kwargs):
        return matrsum.integrate(self.data, self.tmp.name, runner=runner,
                                 **kwargs)

    # ----- недоступность модуля -----

    def test_module_script_missing(self):
        runner = functools.partial(
            matrsum.run_processing_subprocess,
            script=os.path.join(self.tmp.name, "нет_такого.py"))
        with self.assertRaises(ModuleUnavailableError):
            self.integrate(runner)

    def test_module_crash(self):
        script = write_script(self.tmp.name, "raise SystemExit(5)\n")
        runner = functools.partial(matrsum.run_processing_subprocess,
                                   script=script)
        with self.assertRaises(ModuleUnavailableError) as ctx:
            self.integrate(runner)
        self.assertIn("кодом 5", str(ctx.exception))

    def test_module_exits_without_response(self):
        script = write_script(self.tmp.name, "pass\n")
        runner = functools.partial(matrsum.run_processing_subprocess,
                                   script=script)
        with self.assertRaises(ModuleUnavailableError):
            self.integrate(runner)

    def test_retry_after_unavailable(self):
        calls = []

        def flaky(request_path, response_path, timeout):
            calls.append(1)
            if len(calls) == 1:
                raise ModuleUnavailableError("сбой запуска")
            helpers.inprocess_runner(request_path, response_path, timeout)

        result = self.integrate(flaky, attempts=2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.columns, (1,))

    def test_all_attempts_fail(self):
        calls = []

        def broken(request_path, response_path, timeout):
            calls.append(1)
            raise ModuleUnavailableError("сбой")

        with self.assertRaises(ModuleUnavailableError):
            self.integrate(broken, attempts=3)
        self.assertEqual(len(calls), 3)

    # ----- тайм-аут -----

    def test_timeout(self):
        script = write_script(self.tmp.name,
                              "import time\ntime.sleep(5)\n")
        runner = functools.partial(matrsum.run_processing_subprocess,
                                   script=script)
        with self.assertRaises(ModuleTimeoutError):
            self.integrate(runner, timeout=0.3, attempts=1)

    def test_main_reports_timeout_with_exit_code(self):
        script = write_script(self.tmp.name,
                              "import time\ntime.sleep(5)\n")
        runner = functools.partial(matrsum.run_processing_subprocess,
                                   script=script)
        errors = []
        code = matrsum.main(
            ["--timeout", "0.3"], read=helpers.Reader(["1", "1", "0"]),
            write=lambda text: None, write_err=errors.append, runner=runner)
        self.assertEqual(code, matrsum.EXIT_INTEGRATION_ERROR)
        self.assertIn("не ответил", errors[0])

    # ----- некорректные данные -----

    def test_processing_reports_invalid_data(self):
        def bad_request(request_path, response_path, timeout):
            message = protocol.build_request(5, 2, [[0.0, 1.0]])
            protocol.dump_json(request_path, message)
            helpers.inprocess_runner(request_path, response_path, timeout)

        with self.assertRaises(InputDataError):
            self.integrate(bad_request)

    def test_garbage_in_response_file(self):
        def garbage(request_path, response_path, timeout):
            with open(response_path, "w", encoding="utf-8") as handle:
                handle.write("это не JSON")

        with self.assertRaises(ProtocolError):
            self.integrate(garbage)

    def test_wrong_response_type(self):
        def wrong_type(request_path, response_path, timeout):
            protocol.dump_json(response_path, protocol.build_request(
                1, 1, [[0]]))

        with self.assertRaises(ProtocolError):
            self.integrate(wrong_type)

    # ----- конфликт версий -----

    def test_response_with_new_major_version(self):
        def future(request_path, response_path, timeout):
            helpers.inprocess_runner(request_path, response_path, timeout)
            with open(response_path, encoding="utf-8") as handle:
                message = json.load(handle)
            message["version"] = "2.0"
            protocol.dump_json(response_path, message)

        with self.assertRaises(VersionConflictError):
            self.integrate(future)

    def test_processing_rejects_new_request_version(self):
        def new_client(request_path, response_path, timeout):
            message = protocol.load_json(request_path)
            message["version"] = "3.1"
            protocol.dump_json(request_path, message)
            helpers.inprocess_runner(request_path, response_path, timeout)

        with self.assertRaises(VersionConflictError):
            self.integrate(new_client)

    def test_missing_request_file_for_module(self):
        response = os.path.join(self.tmp.name, "r.json")
        with contextlib.redirect_stderr(io.StringIO()):
            code = helpers.processing_module.main(
                ["--request", os.path.join(self.tmp.name, "нет.json"),
                 "--response", response])
        self.assertEqual(code, protocol.EXIT_FAILURE)

    def test_broken_request_file_gives_error_response(self):
        request = os.path.join(self.tmp.name, "q.json")
        response = os.path.join(self.tmp.name, "r.json")
        with open(request, "w", encoding="utf-8") as handle:
            handle.write("{")
        code = helpers.processing_module.main(
            ["--request", request, "--response", response])
        self.assertEqual(code, protocol.EXIT_REPORTED_ERROR)
        self.assertEqual(protocol.load_json(response)["type"],
                         protocol.MSG_ERROR)

    def test_orchestrator_starts_without_processing_module(self):
        """Отсутствие модуля обработки — ошибка интеграции, а не сбой."""
        src_copy = os.path.join(self.tmp.name, "src")
        shutil.copytree(
            helpers.SRC_DIR, src_copy,
            ignore=shutil.ignore_patterns("__pycache__",
                                          "processing_module.py"))
        completed = subprocess.run(
            [sys.executable, os.path.join(src_copy, "matrsum.py")],
            input="1\n1\n0\n", capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, matrsum.EXIT_INTEGRATION_ERROR)
        self.assertIn("Ошибка интеграции", completed.stderr)



if __name__ == "__main__":
    unittest.main()
