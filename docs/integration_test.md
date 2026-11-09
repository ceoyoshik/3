# Тестирование интеграции

Запуск: `python -m unittest discover -s tests -v`
Результат: **68 тестов, все пройдены**. Покрытие строк `src/`: **97 %**
(порог CI — 85 %).

## 1. Тестовые сценарии

| ID | Сценарий | Тест | Ожидаемый результат | Итог |
| --- | --- | --- | --- | --- |
| IT-01 | Драйвер отправляет 9 наборов из `cases.json` модулю обработки | `ProcessingDriverTests.test_cases_from_json` | столбцы и сумма совпадают с эталоном | пройден |
| IT-02 | Ответ обработки проходит проверку протокола | `test_response_is_valid_message` | сообщение `sum_response` корректно | пройден |
| IT-03 | Ввод → JSON-файлы → обработка, вывод — заглушка | `Step2InputProcessingTests.test_input_to_processing_with_output_stub` | `OutputStub` получает столбцы (2, 3) и сумму 23 | пройден |
| IT-04 | Создаются оба файла обмена | `test_exchange_files_are_created` | `request.json`, `response.json` | пройден |
| IT-05 | Все наборы через файлы обмена | `test_all_cases_through_json_files` | совпадение с эталоном | пройден |
| IT-06 | Полный запуск, модуль обработки как процесс | `Step3FullSystemTests.test_full_run_with_subprocess` | вывод «…2, 3» и «23.000», код 0 | пройден |
| IT-07 | Нет столбцов с нулём | `test_no_zero_columns` | сообщение «нет», сумма 0.000 | пройден |
| IT-08 | Десятичная запятая | `test_decimal_comma_end_to_end` | запятая нормализуется | пройден |
| IT-09 | Сохранение файлов обмена (`--workdir`) | `test_workdir_keeps_json_files` | файлы созданы | пройден |
| IT-10 | Ошибка ввода | `test_bad_input_returns_data_error` | код 1, текст «Ошибка данных» | пройден |
| IT-11 | Матрица 200 × 200 | `test_big_matrix` | верные столбец и сумма | пройден |
| IT-12 | Модуль обработки не найден | `test_module_script_missing` | `ModuleUnavailableError` | пройден |
| IT-13 | Модуль завершился сбоем | `test_module_crash` | `ModuleUnavailableError`, «кодом 5» | пройден |
| IT-14 | Модуль не создал ответ | `test_module_exits_without_response` | `ModuleUnavailableError` | пройден |
| IT-15 | Повтор после сбоя | `test_retry_after_unavailable` | вторая попытка успешна | пройден |
| IT-16 | Все попытки неудачны | `test_all_attempts_fail` | 3 попытки, затем исключение | пройден |
| IT-17 | Тайм-аут модуля | `test_timeout` | `ModuleTimeoutError` | пройден |
| IT-18 | Тайм-аут в `main` | `test_main_reports_timeout_with_exit_code` | код 2, «не ответил» | пройден |
| IT-19 | Модуль сообщает о некорректных данных | `test_processing_reports_invalid_data` | `InputDataError` | пройден |
| IT-20 | Мусор в файле ответа | `test_garbage_in_response_file` | `ProtocolError` | пройден |
| IT-21 | Неверный тип ответа | `test_wrong_response_type` | `ProtocolError` | пройден |
| IT-22 | Ответ с версией 2.0 | `test_response_with_new_major_version` | `VersionConflictError` | пройден |
| IT-23 | Запрос с версией 3.1 | `test_processing_rejects_new_request_version` | `VersionConflictError` | пройден |
| IT-24 | Нет файла запроса | `test_missing_request_file_for_module` | код 3 | пройден |
| IT-25 | Повреждённый файл запроса | `test_broken_request_file_gives_error_response` | код 10, сообщение `error` | пройден |
| IT-26 | Запуск без файла модуля обработки | `test_orchestrator_starts_without_processing_module` | код 2, «Ошибка интеграции» | пройден |

## 2. Граничные случаи

Матрица 1 × 1 с нулём, «минус ноль», одна строка, один столбец, все
столбцы с нулями, отрицательные и дробные числа, `nan`/`inf`/`1e999`,
размер 0, −1, 1001, нецелый размер, лишние пробелы, прерванный ввод,
`true` вместо числа в JSON, константа `NaN` в JSON, неверный формат версии.

## 3. Число тестов по группам

| Группа | Файл | Тестов |
| --- | --- | --- |
| Обработка и драйвер (шаг 1) | `test_processing.py` | 11 |
| Протокол, файлы обмена, mapping | `test_protocol_mapping.py` | 19 |
| Ввод | `test_input.py` | 8 |
| Вывод | `test_output.py` | 5 |
| Шаг 2 | `test_step2_integration.py` | 3 |
| Шаг 3 | `test_step3_system.py` | 7 |
| Исключительные ситуации | `test_exceptions.py` | 15 |
| **Итого** | | **68** |

## 4. Выявленные при отладке проблемы и их устранение

| № | Дефект | Где найден | Исправление |
| --- | --- | --- | --- |
| 1 | Наивный ввод принимает `float("nan")` и `float("inf")` как числа | отладка шага 2 | проверка `math.isfinite` в модуле ввода и в протоколе |
| 2 | Наивное форматирование печатает «-0.000» для малых отрицательных сумм | отладка шага 3 | замена на `0.000` в `format_number` |
| 3 | На Python 3.11 и старше `sum()` десяти значений 0.1 даёт 0.9999999999999999, на 3.12 — 1.0 (результат зависит от версии) | шаг 1 | `math.fsum` — одинаковый точный результат на всех версиях |
| 4 | Стандартный `json` по умолчанию принимает и пишет константу `NaN` | шаг 2 | `allow_nan=False` при записи, `parse_constant` при чтении |
| 5 | Ввод «1,5» отвергается функцией `float` | шаг 2 | нормализация запятой |
