"""МатрСум-11: сумма элементов столбцов матрицы, содержащих нуль."""

# Количество знаков после запятой при выводе результата
PRECISION = 3


def column_sum(matrix):
    """Возвращает (номера столбцов с нулём, сумма их элементов)."""
    columns = [j for j in range(len(matrix[0]))
               if any(row[j] == 0 for row in matrix)]
    return columns, sum(row[j] for row in matrix for j in columns)


def main():
    n = int(input("Количество строк n: "))
    m = int(input("Количество столбцов m: "))
    matrix = [list(map(float, input().split())) for _ in range(n)]
    columns, total = column_sum(matrix)
    print("Столбцы с нулём:", [j + 1 for j in columns])
    print(f"Сумма: {total:.{PRECISION}f}")


if __name__ == "__main__":
    main()
