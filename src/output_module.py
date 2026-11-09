"""Модуль вывода: форматирование и печать результата."""

# Количество знаков после запятой при выводе результата (требование ТЗ)
PRECISION = 3


def format_number(value, precision=PRECISION):
    """Число с заданной точностью; «-0.000» заменяется на «0.000»."""
    rounded = round(value, precision)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.{precision}f}"


def format_result(result, precision=PRECISION):
    """Строка с результатом для OutputData."""
    total = format_number(result.total, precision)
    if result.columns:
        columns = ", ".join(str(number) for number in result.columns)
        return (f"Столбцы с нулевым элементом: {columns}\n"
                f"Сумма элементов этих столбцов: {total}")
    return f"Столбцов с нулевым элементом нет.\nСумма элементов: {total}"


def show(result, write=print):
    """Выводит результат (write можно подменить в тестах)."""
    write(format_result(result))
