def read_vector(name="вектор"):
    while True:
        try:
            vals = input(f"Введите координаты {name} (через пробел, например '1 2'): ").strip().split()
            if len(vals) != 2:
                print("Ошибка: нужно ровно 2 числа.")
                continue
            return [float(x) for x in vals]
        except ValueError:
            print("Ошибка: введите корректные числа.")

def read_matrix(name="матрица"):
    print(f"Ввод {name} в формате [[a, b], [c, d]]:")
    while True:
        s = input("Введите матрицу: ").strip()
        try:
            matrix = eval(s)

            if not isinstance(matrix, list) or len(matrix) != 2:
                raise ValueError("Матрица должна содержать ровно 2 строки.")
            for i, row in enumerate(matrix):
                if not isinstance(row, list) or len(row) != 2:
                    raise ValueError(f"Строка {i+1} должна содержать ровно 2 элемента.")
                for j, val in enumerate(row):
                    if not isinstance(val, (int, float)):
                        raise ValueError(f"Элемент [{i}][{j}] должен быть числом.")

            return [[float(x) for x in row] for row in matrix]

        except (ValueError, SyntaxError) as e:
            print(f"Ошибка ввода: {e}")
            print("Пример корректного ввода: [[1.0, 2.0], [3.0, 4.0]]")

def mat_vec_mult(mat, vec):
    x = mat[0][0] * vec[0] + mat[0][1] * vec[1]
    y = mat[1][0] * vec[0] + mat[1][1] * vec[1]
    return [x, y]

def mat_mult(A, B):

    C = [[0, 0], [0, 0]]
    for i in range(2):
        for j in range(2):
            C[i][j] = A[i][0]*B[0][j] + A[i][1]*B[1][j]
    return C

def print_vector(vec, label="Вектор"):
    print(f"{label}: [{vec[0]:.4f}, {vec[1]:.4f}]")

def print_matrix(mat, label="Матрица"):
    print(f"{label}:")
    for row in mat:
        print(f"  [{row[0]:.4f}, {row[1]:.4f}]")


x = read_vector("исходного вектора x")
R = read_matrix("матрицы преобразования R")
S = read_matrix("матрицы преобразования S")


x1 = mat_vec_mult(R, x)
x2 = mat_vec_mult(S, x1)


T = mat_mult(S, R)
x_check = mat_vec_mult(T, x)

print("\n--- Результаты вычислений ---")
print_vector(x, "Исходный вектор x")
print_matrix(R, "Матрица R")
print_matrix(S, "Матрица S")
print_vector(x1, "Промежуточный вектор x1 = R*x")
print_vector(x2, "Итоговый вектор x2 = S*x1")
print_matrix(T, "Общая матрица преобразования T = S*R")
print_vector(x_check, "Проверка: T*x (должно совпадать с x2)")

eps = 1e-9
diff = [(x2[0] - x_check[0]), (x2[1] - x_check[1])]
if abs(diff[0]) < eps and abs(diff[1]) < eps:
    print("\nПроверка пройдена: T*x совпадает с x2.")
else:
    print("\nПроверка не пройдена: есть расхождение.")
    print(f"Расхождения: [{diff[0]:.2e}, {diff[1]:.2e}]")
