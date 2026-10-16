def get_positive_int(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
            print("Введите целое положительное число.")
        except ValueError:
            print("Необходимо ввести целое число.")
def get_vector(size, name):
    vector = []
    print(f"\nВведите элементы вектора {name}:")
    for i in range(size):
        while True:
            try:
                value = float(input(f"{name}[{i}]: "))
                vector.append(value)
                break
            except ValueError:
                print("Введите число.")

    return vector


def get_matrix(rows, cols):
    matrix = []

    print("\nВведите элементы матрицы W:")
    for i in range(rows):
        row = []
        print(f"Строка {i + 1}:")
        for j in range(cols):
            while True:
                try:
                    value = float(input(f"W[{i}][{j}]: "))
                    row.append(value)
                    break
                except ValueError:
                    print("Введите число.")
        matrix.append(row)

    return matrix


def dense_layer(x, W, b):
    if len(W) != len(b):
        raise ValueError(
            "Количество строк матрицы W должно совпадать "
            "с размерностью вектора b."
        )

    if any(len(row) != len(x) for row in W):
        raise ValueError(
            "Количество столбцов матрицы W должно "
            "совпадать с размерностью вектора x."
        )

    z = []
    for i in range(len(W)):
        total = 0
        for j in range(len(x)):
            total += W[i][j] * x[j]
        z.append(total + b[i])

    return z


print("=== Симулятор полносвязного слоя нейросети ===")

N = get_positive_int("Введите размерность N вектора x: ")
M = get_positive_int("Введите размерность M выходного вектора: ")

x = get_vector(N, "x")
W = get_matrix(M, N)
b = get_vector(M, "b")

try:
    z = dense_layer(x, W, b)

    print("\n--- Результаты ---")
    print(f"Размерность N: {N}")
    print(f"Размерность M: {M}")
    print(f"Вектор признаков x: {x}")
    print("Матрица весов W:")
    for row in W:
        print(row)
    print(f"Вектор смещения b: {b}")
    print(f"Выходной вектор z = Wx + b: {z}")

except ValueError as error:
    print(f"Ошибка размерностей: {error}")
