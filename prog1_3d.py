def parse_vector(user_input: str):
    try:
        vec = eval(user_input)
        if isinstance(vec, (list, tuple)) and len(vec) == 3:
            return [float(x) for x in vec]
    except (ValueError, SyntaxError):
        pass
    return None

def get_vector(prompt: str):
    while True:
        user_input = input(prompt)
        vec = parse_vector(user_input)
        if vec is not None:
            return vec
        print("Вводите ровно 3 числа в формате [x, y, z], например: [1, 2, 3]")

def add_vectors(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]

def vector_length(v):
    return (v[0]**2 + v[1]**2 + v[2]**2) ** 0.5

A = get_vector("Введите координаты точки A [x, y, z]: ")
u = get_vector("Введите вектор u [x, y, z]: ")
v = get_vector("Введите вектор v [x, y, z]: ")

r = add_vectors(u, v)
B = add_vectors(A, r)
length = vector_length(r)

print("\n--- Результаты ---")
print(f"Точка A: {A}")
print(f"Вектор u: {u}")
print(f"Вектор v: {v}")
print(f"Результирующий вектор r (u + v): {r}")
print(f"Итоговая позиция B (A + r): {B}")
print(f"Длина пути (|r|): {length:.4f}")
