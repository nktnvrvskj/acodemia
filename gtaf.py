import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import json
import csv
import copy

# ============================================================
# НАСТРОЙКИ И ДАННЫЕ
# ============================================================

root = tk.Tk()
root.title("Редактор графов — FR-1–FR-11")
root.geometry("1250x820")
root.minsize(950, 650)

R = 22
MAX_VERTICES = 100
MAX_EDGES = 500

vertices = {}
edges = []
next_vertex_id = 1
next_edge_id = 1

directed = True
allow_multiple = False
allow_loops = False

mode = "vertex"
selected_vertex = None
selected_edge = None
edge_start = None
dragging = None
drag_offset = (0, 0)

undo_stack = []
edge_items = {}
vertex_items = {}

# ============================================================
# ИНТЕРФЕЙС
# ============================================================

main = ttk.Frame(root, padding=6)
main.pack(fill="both", expand=True)

toolbar = ttk.Frame(main)
toolbar.pack(fill="x", pady=(0, 6))

canvas_frame = ttk.Frame(main)
canvas_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(
    canvas_frame,
    bg="white",
    highlightthickness=1,
    highlightbackground="#cccccc"
)
canvas.pack(side="left", fill="both", expand=True)

yscroll = ttk.Scrollbar(
    canvas_frame,
    orient="vertical",
    command=canvas.yview
)
yscroll.pack(side="right", fill="y")
canvas.configure(yscrollcommand=yscroll.set)

right = ttk.Frame(main)
right.pack(fill="x", pady=(6, 0))

status_var = tk.StringVar(value="Режим: Вершина")
info_var = tk.StringVar()
lemma_var = tk.StringVar()

graph_type_var = tk.StringVar(value="Ориентированный")
multi_var = tk.BooleanVar(value=False)
loops_var = tk.BooleanVar(value=False)

mode_buttons = {}

for label, value in [
    ("Вершина", "vertex"),
    ("Ребро", "edge"),
    ("Перемещение", "move"),
    ("Удалить", "delete"),
    ("Выбор", "select"),
]:
    btn = ttk.Button(
        toolbar,
        text=label,
        command=lambda m=value: set_mode(m)
    )
    btn.pack(side="left", padx=2)
    mode_buttons[value] = btn

ttk.Separator(
    toolbar,
    orient="vertical"
).pack(side="left", fill="y", padx=7)

ttk.Label(toolbar, text="Тип графа:").pack(side="left", padx=2)

graph_type = ttk.Combobox(
    toolbar,
    textvariable=graph_type_var,
    values=["Неориентированный", "Ориентированный"],
    state="readonly",
    width=21
)
graph_type.pack(side="left", padx=3)

ttk.Checkbutton(
    toolbar,
    text="Кратные рёбра",
    variable=multi_var,
    command=lambda: change_options()
).pack(side="left", padx=5)

ttk.Checkbutton(
    toolbar,
    text="Петли",
    variable=loops_var,
    command=lambda: change_options()
).pack(side="left", padx=5)

ttk.Label(
    right,
    textvariable=status_var
).pack(anchor="w", pady=(0, 4))

notebook = ttk.Notebook(right)
notebook.pack(fill="both", expand=True)

info_tab = ttk.Frame(notebook, padding=8)
adj_tab = ttk.Frame(notebook, padding=5)
inc_tab = ttk.Frame(notebook, padding=5)

notebook.add(info_tab, text="Степени и проверки")
notebook.add(adj_tab, text="Матрица смежности")
notebook.add(inc_tab, text="Матрица инцидентности")

ttk.Label(
    info_tab,
    textvariable=info_var,
    justify="left",
    anchor="nw"
).pack(fill="both", expand=True)

ttk.Label(
    info_tab,
    textvariable=lemma_var,
    justify="left",
    anchor="nw"
).pack(fill="x", pady=(8, 0))


def create_matrix_table(parent):
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(frame, show="headings")

    sy = ttk.Scrollbar(
        frame, orient="vertical", command=tree.yview
    )
    sx = ttk.Scrollbar(
        frame, orient="horizontal", command=tree.xview
    )

    tree.configure(
        yscrollcommand=sy.set,
        xscrollcommand=sx.set
    )

    tree.grid(row=0, column=0, sticky="nsew")
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    return tree


adj_tree = create_matrix_table(adj_tab)
inc_tree = create_matrix_table(inc_tab)

# Кнопка применения заполненной матрицы
ttk.Button(
    adj_tab,
    text="Построить граф по матрице",
    command=lambda: apply_adjacency_matrix()
).pack(anchor="w", pady=5)
# ============================================================
# ОТМЕНА ДЕЙСТВИЙ
# ============================================================

def snapshot():
    return {
        "vertices": copy.deepcopy(vertices),
        "edges": copy.deepcopy(edges),
        "next_vertex_id": next_vertex_id,
        "next_edge_id": next_edge_id,
        "directed": directed,
        "allow_multiple": allow_multiple,
        "allow_loops": allow_loops,
    }


def remember():
    undo_stack.append(snapshot())
    if len(undo_stack) > 100:
        undo_stack.pop(0)


def undo():
    global vertices, edges
    global next_vertex_id, next_edge_id
    global directed, allow_multiple, allow_loops
    global selected_vertex, selected_edge, edge_start, dragging

    if not undo_stack:
        status_var.set("Отмена недоступна")
        return

    state = undo_stack.pop()

    vertices = state["vertices"]
    edges = state["edges"]
    next_vertex_id = state["next_vertex_id"]
    next_edge_id = state["next_edge_id"]
    directed = state["directed"]
    allow_multiple = state["allow_multiple"]
    allow_loops = state["allow_loops"]

    graph_type_var.set(
        "Ориентированный" if directed
        else "Неориентированный"
    )
    multi_var.set(allow_multiple)
    loops_var.set(allow_loops)

    selected_vertex = None
    selected_edge = None
    edge_start = None
    dragging = None

    refresh()


def change_options():
    global allow_multiple, allow_loops

    allow_multiple = multi_var.get()
    allow_loops = loops_var.get()
    refresh()


def change_graph_type(event=None):
    global directed

    new_value = graph_type_var.get() == "Ориентированный"

    if new_value == directed:
        return

    remember()
    directed = new_value
    refresh()


graph_type.bind("<<ComboboxSelected>>", change_graph_type)


def set_mode(new_mode):
    global mode, selected_vertex
    global selected_edge, edge_start, dragging

    mode = new_mode
    selected_vertex = None
    selected_edge = None
    edge_start = None
    dragging = None

    names = {
        "vertex": "Вершина",
        "edge": "Ребро",
        "move": "Перемещение",
        "delete": "Удаление",
        "select": "Выбор",
    }

    status_var.set("Режим: " + names[mode])
    refresh()


# ============================================================
# ПОИСК ВЕРШИН И РЁБЕР
# ============================================================

def vertex_at(x, y):
    for v, (vx, vy) in reversed(list(vertices.items())):
        if (x - vx) ** 2 + (y - vy) ** 2 <= R ** 2:
            return v
    return None


def edge_key(a, b):
    if directed:
        return (a, b)
    return (min(a, b), max(a, b))


def edge_exists(a, b):
    key = edge_key(a, b)
    return any(
        edge_key(e["a"], e["b"]) == key
        for e in edges
    )


def point_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)

    t = (
        (px - x1) * dx + (py - y1) * dy
    ) / (dx * dx + dy * dy)

    t = max(0, min(1, t))

    qx = x1 + t * dx
    qy = y1 + t * dy

    return math.hypot(px - qx, py - qy)


def edge_at(x, y):
    for edge in reversed(edges):
        a, b = edge["a"], edge["b"]

        if a not in vertices or b not in vertices:
            continue

        x1, y1 = vertices[a]
        x2, y2 = vertices[b]

        if a == b:
            if math.hypot(x - x1, y - (y1 - 2 * R)) < R + 8:
                return edge["id"]
            continue

        if point_segment_distance(
            x, y, x1, y1, x2, y2
        ) < 9:
            return edge["id"]

    return None


# ============================================================
# ДОБАВЛЕНИЕ И УДАЛЕНИЕ
# ============================================================

def delete_edge(edge_id):
    global selected_edge

    for i, edge in enumerate(edges):
        if edge["id"] == edge_id:
            remember()
            edges.pop(i)
            selected_edge = None
            refresh()
            return


def delete_vertex(v):
    global selected_vertex, selected_edge, edge_start

    if v not in vertices:
        return

    remember()
    del vertices[v]

    edges[:] = [
        e for e in edges
        if e["a"] != v and e["b"] != v
    ]

    selected_vertex = None
    selected_edge = None
    edge_start = None

    refresh()


def add_vertex(x, y):
    global next_vertex_id

    if len(vertices) >= MAX_VERTICES:
        messagebox.showwarning(
            "Ограничение",
            f"Максимум {MAX_VERTICES} вершин."
        )
        return

    if vertex_at(x, y) is not None:
        return

    for vx, vy in vertices.values():
        if math.hypot(x - vx, y - vy) < 2 * R + 5:
            status_var.set("Слишком близко к другой вершине")
            return

    remember()

    v = next_vertex_id
    next_vertex_id += 1
    vertices[v] = (x, y)

    refresh()


def add_edge(a, b):
    global next_edge_id

    if a not in vertices or b not in vertices:
        return

    if a == b and not allow_loops:
        status_var.set("Петли отключены")
        return

    if not allow_multiple and edge_exists(a, b):
        status_var.set("Такое ребро уже существует")
        return

    if len(edges) >= MAX_EDGES:
        messagebox.showwarning(
            "Ограничение",
            f"Максимум {MAX_EDGES} рёбер."
        )
        return

    remember()

    edges.append({
        "id": next_edge_id,
        "a": a,
        "b": b
    })

    next_edge_id += 1
    refresh()

# ============================================================
# РАСЧЁТ СТЕПЕНЕЙ
# ============================================================

def calculate_degrees():
    degree = {v: 0 for v in vertices}
    in_degree = {v: 0 for v in vertices}
    out_degree = {v: 0 for v in vertices}

    for edge in edges:
        a, b = edge["a"], edge["b"]

        if a not in vertices or b not in vertices:
            continue

        if directed:
            out_degree[a] += 1
            in_degree[b] += 1
            degree[a] += 1
            degree[b] += 1
        else:
            if a == b:
                degree[a] += 2
            else:
                degree[a] += 1
                degree[b] += 1

    return degree, in_degree, out_degree


# ============================================================
# МАТРИЦА СМЕЖНОСТИ
# ============================================================

def adjacency_matrix():
    ids = list(vertices.keys())
    matrix = [[0 for _ in ids] for _ in ids]
    index = {v: i for i, v in enumerate(ids)}

    for edge in edges:
        a, b = edge["a"], edge["b"]

        if a not in index or b not in index:
            continue

        i, j = index[a], index[b]

        if directed:
            matrix[i][j] += 1
        elif i == j:
            matrix[i][i] += 2
        else:
            matrix[i][j] += 1
            matrix[j][i] += 1

    return ids, matrix


# ============================================================
# МАТРИЦА ИНЦИДЕНТНОСТИ
# ============================================================

def incidence_matrix():
    ids = list(vertices.keys())
    matrix = []

    for v in ids:
        row = []

        for edge in edges:
            a, b = edge["a"], edge["b"]

            if directed:
                if a == b == v:
                    row.append(0)
                elif v == a:
                    row.append(1)
                elif v == b:
                    row.append(-1)
                else:
                    row.append(0)
            else:
                if a == b == v:
                    row.append(2)
                elif v == a or v == b:
                    row.append(1)
                else:
                    row.append(0)

        matrix.append(row)

    return ids, matrix


# ============================================================
# ИНФОРМАЦИЯ О ГРАФЕ И ПРОВЕРКИ
# ============================================================

def update_info():
    degree, in_degree, out_degree = calculate_degrees()

    if directed:
        degree_text = "\n".join(
            f"Вершина {v}: deg+ = {out_degree[v]}, "
            f"deg− = {in_degree[v]}, deg = {degree[v]}"
            for v in vertices
        )

        sum_out = sum(out_degree.values())
        sum_in = sum(in_degree.values())

        lemma_text = (
            f"Σ deg+ = {sum_out}\n"
            f"Σ deg− = {sum_in}\n"
            f"|A| = {len(edges)}\n"
            f"Проверка: "
            f"{'ВЫПОЛНЯЕТСЯ' if sum_out == len(edges) and sum_in == len(edges) else 'НАРУШЕНО'}"
        )

    else:
        degree_text = "\n".join(
            f"Вершина {v}: deg = {degree[v]}"
            for v in vertices
        )

        sum_degree = sum(degree.values())
        expected = 2 * len(edges)
        odd_count = sum(d % 2 for d in degree.values())

        lemma_text = (
            f"Σ deg(v) = {sum_degree}\n"
            f"2|E| = {expected}\n"
            f"Лемма о рукопожатиях: "
            f"{'ВЫПОЛНЯЕТСЯ' if sum_degree == expected else 'НАРУШЕНО'}\n"
            f"Вершин нечётной степени: {odd_count}\n"
            f"Количество нечётных степеней чётно: "
            f"{'ДА' if odd_count % 2 == 0 else 'НЕТ'}"
        )

    info_var.set(
        f"Количество вершин |V| = {len(vertices)}\n"
        f"Количество рёбер/дуг = {len(edges)}\n\n"
        f"Степени вершин:\n{degree_text}"
    )

    lemma_var.set(lemma_text)


# ============================================================
# ОБНОВЛЕНИЕ ТАБЛИЦ
# ============================================================

def update_tree(tree, columns, rows):
    tree.delete(*tree.get_children())
    tree["columns"] = columns

    for col in columns:
        tree.heading(col, text=str(col))
        tree.column(
            col,
            width=65,
            minwidth=40,
            anchor="center"
        )

    for row in rows:
        tree.insert("", "end", values=row)


def update_matrices():
    ids, matrix = adjacency_matrix()

    adj_columns = ["v"] + ids
    adj_rows = [
        [v] + matrix[i]
        for i, v in enumerate(ids)
    ]

    update_tree(adj_tree, adj_columns, adj_rows)

    ids, matrix = incidence_matrix()

    edge_columns = [f"e{e['id']}" for e in edges]
    inc_columns = ["v"] + edge_columns

    inc_rows = [
        [v] + matrix[i]
        for i, v in enumerate(ids)
    ]

    update_tree(inc_tree, inc_columns, inc_rows)


# ============================================================
# РЕДАКТИРОВАНИЕ ЯЧЕЕК МАТРИЦЫ СМЕЖНОСТИ
# ============================================================

def edit_adjacency_cell(event):
    region = adj_tree.identify("region", event.x, event.y)

    if region != "cell":
        return

    row_id = adj_tree.identify_row(event.y)
    col_id = adj_tree.identify_column(event.x)

    if not row_id or not col_id:
        return

    col_index = int(col_id[1:]) - 1

    # Первый столбец содержит номера вершин
    if col_index == 0:
        return

    bbox = adj_tree.bbox(row_id, col_id)

    if not bbox:
        return

    x, y, width, height = bbox
    old_values = list(adj_tree.item(row_id, "values"))

    entry = ttk.Entry(adj_tree, justify="center")
    entry.place(x=x, y=y, width=width, height=height)
    entry.insert(0, str(old_values[col_index]))
    entry.select_range(0, tk.END)
    entry.focus_set()

    finished = False

    def finish_edit(save):
        nonlocal finished

        if finished:
            return

        finished = True

        if not save:
            entry.destroy()
            return

        text = entry.get().strip()

        try:
            value = int(text)
        except ValueError:
            entry.destroy()
            messagebox.showwarning(
                "Ошибка ввода",
                "Введи целое число: -1, 0 или 1."
            )
            return

        if value not in (-1, 0, 1):
            entry.destroy()
            messagebox.showwarning(
                "Ошибка ввода",
                "Допустимы только значения -1, 0 и 1."
            )
            return

        old_values[col_index] = value
        adj_tree.item(row_id, values=old_values)
        entry.destroy()

    entry.bind("<Return>", lambda e: finish_edit(True))
    entry.bind("<Escape>", lambda e: finish_edit(False))

    # При потере фокуса сохраняем введённое значение
    entry.bind("<FocusOut>", lambda e: finish_edit(True))


adj_tree.bind("<Double-1>", edit_adjacency_cell)


# ============================================================
# ПОСТРОЕНИЕ ГРАФА ПО ЗАПОЛНЕННОЙ МАТРИЦЕ
# ============================================================

def apply_adjacency_matrix():
    global edges, next_edge_id
    global directed, selected_vertex, selected_edge, edge_start

    ids = list(vertices.keys())
    rows = adj_tree.get_children()

    if len(rows) != len(ids):
        messagebox.showerror(
            "Ошибка",
            "Количество строк матрицы не совпадает "
            "с количеством вершин."
        )
        return

    # Считываем матрицу из таблицы
    matrix = []

    try:
        for row_id in rows:
            values = list(adj_tree.item(row_id, "values"))

            if len(values) != len(ids) + 1:
                raise ValueError("Неверный размер матрицы.")

            matrix.append([
                int(value) for value in values[1:]
            ])

    except (ValueError, TypeError):
        messagebox.showerror(
            "Ошибка",
            "Матрица содержит некорректные значения."
        )
        return

    # Проверяем диагональ и размеры
    for i in range(len(ids)):
        if matrix[i][i] != 0:
            messagebox.showerror(
                "Ошибка матрицы",
                "На главной диагонали должны быть нули."
            )
            return

    # Матрица должна содержать согласованные пары 1 и -1
    new_edges = []

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a = matrix[i][j]
            b = matrix[j][i]

            if a == 1 and b == -1:
                new_edges.append({
                    "id": len(new_edges) + 1,
                    "a": ids[i],
                    "b": ids[j]
                })

            elif a == -1 and b == 1:
                new_edges.append({
                    "id": len(new_edges) + 1,
                    "a": ids[j],
                    "b": ids[i]
                })

            elif a == 0 and b == 0:
                continue

            else:
                messagebox.showerror(
                    "Ошибка матрицы",
                    f"Ячейки ({ids[i]}, {ids[j]}) и "
                    f"({ids[j]}, {ids[i]}) должны быть "
                    f"либо 0 и 0, либо 1 и -1."
                )
                return

    if len(new_edges) > MAX_EDGES:
        messagebox.showerror(
            "Ошибка",
            f"Максимум {MAX_EDGES} рёбер."
        )
        return

    # Сохраняем предыдущее состояние для Ctrl+Z
    remember()

    edges = new_edges
    next_edge_id = len(edges) + 1

    # Знаковая матрица задаёт ориентированный граф
    directed = True
    graph_type_var.set("Ориентированный")

    selected_vertex = None
    selected_edge = None
    edge_start = None

    refresh()

    status_var.set(
        "Граф построен по матрице смежности"
    )
# ============================================================
# ОТРИСОВКА РЁБЕР
# ============================================================

def draw_edge(edge):
    a, b, eid = edge["a"], edge["b"], edge["id"]

    if a not in vertices or b not in vertices:
        return

    x1, y1 = vertices[a]
    x2, y2 = vertices[b]

    color = "#d62728" if eid == selected_edge else "#333333"
    width = 3 if eid == selected_edge else 2

    if a == b:
        item = canvas.create_arc(
            x1 - 12, y1 - 2 * R - 18,
            x1 + 2 * R + 12, y1 + 12,
            start=20,
            extent=320,
            style=tk.ARC,
            outline=color,
            width=width,
            tags=("edge", f"edge_{eid}")
        )

        if directed:
            canvas.create_line(
                x1 + R + 3, y1 - R - 5,
                x1 + R + 1, y1 - R - 1,
                arrow=tk.LAST,
                fill=color,
                width=width
            )

        canvas.create_text(
            x1 + R + 12,
            y1 - 2 * R - 15,
            text=f"e{eid}",
            fill=color,
            font=("Arial", 9),
            tags=("edge", f"edge_{eid}")
        )

        edge_items[eid] = [item]
        return

    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)

    if length == 0:
        return

    ux = dx / length
    uy = dy / length

    parallel = [
        e for e in edges
        if e["id"] != eid
        and (
            (e["a"] == a and e["b"] == b)
            or (e["a"] == b and e["b"] == a)
        )
    ]

    offset = 0

    if parallel:
        offset = (eid % 2 * 2 - 1) * 9

    px, py = -uy, ux

    sx = x1 + ux * R + px * offset
    sy = y1 + uy * R + py * offset
    ex = x2 - ux * R + px * offset
    ey = y2 - uy * R + py * offset

    line = canvas.create_line(
        sx, sy, ex, ey,
        width=width,
        fill=color,
        arrow=tk.LAST if directed else tk.NONE,
        arrowshape=(12, 15, 6),
        tags=("edge", f"edge_{eid}")
    )

    label = canvas.create_text(
        (sx + ex) / 2 + px * 8,
        (sy + ey) / 2 + py * 8,
        text=f"e{eid}",
        font=("Arial", 9),
        fill=color,
        tags=("edge", f"edge_{eid}")
    )

    edge_items[eid] = [line, label]


# ============================================================
# ОТРИСОВКА ВЕРШИН
# ============================================================

def redraw():
    canvas.delete("all")
    edge_items.clear()
    vertex_items.clear()

    for edge in edges:
        draw_edge(edge)

    degree, in_degree, out_degree = calculate_degrees()

    for v, (x, y) in vertices.items():
        color = "#ffd166" if v == selected_vertex else "#bde0fe"
        outline = "#d62728" if v == selected_vertex else "#333333"

        oval = canvas.create_oval(
            x - R, y - R, x + R, y + R,
            fill=color,
            outline=outline,
            width=2,
            tags=("vertex", f"vertex_{v}")
        )

        if directed:
            label = f"{v}\n{out_degree[v]}/{in_degree[v]}"
        else:
            label = f"{v}\n{degree[v]}"

        text = canvas.create_text(
            x, y,
            text=label,
            font=("Arial", 9, "bold"),
            tags=("vertex", f"vertex_{v}")
        )

        vertex_items[v] = [oval, text]

    if vertices:
        xs = [p[0] for p in vertices.values()]
        ys = [p[1] for p in vertices.values()]

        canvas.configure(
            scrollregion=(
                min(xs) - 80,
                min(ys) - 80,
                max(xs) + 100,
                max(ys) + 100
            )
        )
    else:
        canvas.configure(scrollregion=(0, 0, 1000, 700))


def refresh():
    redraw()
    update_info()
    update_matrices()


# ============================================================
# ОБРАБОТКА ЩЕЛЧКОВ МЫШИ
# ============================================================

def click(event):
    global selected_vertex, selected_edge, edge_start
    global dragging, drag_offset

    x = canvas.canvasx(event.x)
    y = canvas.canvasy(event.y)

    v = vertex_at(x, y)
    e = edge_at(x, y)

    if mode == "vertex":
        if v is None:
            add_vertex(x, y)
        return

    if mode == "edge":
        if v is None:
            edge_start = None
            selected_vertex = None
            refresh()
            return

        if edge_start is None:
            edge_start = v
            selected_vertex = v
            selected_edge = None
            status_var.set(
                f"Выбрана вершина {v}: выбери конец ребра"
            )
            redraw()
        else:
            start = edge_start
            edge_start = None
            selected_vertex = None
            add_edge(start, v)

        return

    if mode == "delete":
        if v is not None:
            delete_vertex(v)
        elif e is not None:
            delete_edge(e)
        return

    if mode == "move":
        if v is not None:
            dragging = v
            selected_vertex = v
            vx, vy = vertices[v]
            drag_offset = (vx - x, vy - y)
            redraw()
        return

    if mode == "select":
        selected_vertex = v
        selected_edge = None if v is not None else e

        if v is not None:
            status_var.set(f"Выбрана вершина {v}")
        elif e is not None:
            status_var.set(f"Выбрано ребро e{e}")
        else:
            status_var.set("Ничего не выбрано")

        refresh()


def move_vertex(event):
    global dragging

    if mode != "move" or dragging is None:
        return

    x = canvas.canvasx(event.x) + drag_offset[0]
    y = canvas.canvasy(event.y) + drag_offset[1]

    for v, (vx, vy) in vertices.items():
        if v != dragging and math.hypot(x - vx, y - vy) < 2 * R + 5:
            return

    vertices[dragging] = (x, y)
    refresh()


def release(event):
    global dragging

    if dragging is not None:
        dragging = None
        refresh()


def delete_selected(event=None):
    if selected_vertex is not None:
        delete_vertex(selected_vertex)
    elif selected_edge is not None:
        delete_edge(selected_edge)


def on_escape(event=None):
    global selected_vertex, selected_edge
    global edge_start, dragging

    selected_vertex = None
    selected_edge = None
    edge_start = None
    dragging = None

    refresh()


canvas.bind("<Button-1>", click)
canvas.bind("<B1-Motion>", move_vertex)
canvas.bind("<ButtonRelease-1>", release)

root.bind_all("<Control-z>", lambda e: undo())
root.bind_all("<Control-Z>", lambda e: undo())
root.bind_all("<Delete>", delete_selected)
root.bind_all("<Escape>", on_escape)
# ============================================================
# ОЧИСТКА ГРАФА
# ============================================================

def clear_all():
    global vertices, edges
    global next_vertex_id, next_edge_id
    global selected_vertex, selected_edge
    global edge_start, dragging

    if not vertices and not edges:
        return

    if not messagebox.askyesno(
        "Очистить всё",
        "Удалить все вершины и рёбра?"
    ):
        return

    remember()

    vertices = {}
    edges = []
    next_vertex_id = 1
    next_edge_id = 1

    selected_vertex = None
    selected_edge = None
    edge_start = None
    dragging = None

    refresh()


# ============================================================
# АВТОМАТИЧЕСКАЯ РАСКЛАДКА
# ============================================================

def auto_layout():
    if not vertices:
        return

    remember()

    width = max(canvas.winfo_width(), 600)
    height = max(canvas.winfo_height(), 400)

    cx = width / 2
    cy = height / 2
    radius = max(100, min(width, height) * 0.35)

    ids = list(vertices.keys())
    n = len(ids)

    for i, v in enumerate(ids):
        angle = 2 * math.pi * i / n - math.pi / 2
        vertices[v] = (
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle)
        )

    refresh()


# ============================================================
# СОХРАНЕНИЕ В JSON
# ============================================================

def save_json():
    filename = filedialog.asksaveasfilename(
        title="Сохранить граф",
        defaultextension=".json",
        filetypes=[("JSON", "*.json")]
    )

    if not filename:
        return

    data = {
        "directed": directed,
        "allow_multiple": allow_multiple,
        "allow_loops": allow_loops,
        "next_vertex_id": next_vertex_id,
        "next_edge_id": next_edge_id,
        "vertices": [
            {"id": v, "x": x, "y": y}
            for v, (x, y) in vertices.items()
        ],
        "edges": edges
    }

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        status_var.set("Граф сохранён: " + filename)

    except (OSError, TypeError, ValueError) as exc:
        messagebox.showerror("Ошибка сохранения", str(exc))


# ============================================================
# ЗАГРУЗКА ИЗ JSON
# ============================================================

def load_json():
    global vertices, edges
    global next_vertex_id, next_edge_id
    global directed, allow_multiple, allow_loops
    global selected_vertex, selected_edge, edge_start

    filename = filedialog.askopenfilename(
        title="Загрузить граф",
        filetypes=[("JSON", "*.json")]
    )

    if not filename:
        return

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        new_vertices = {}

        for item in data["vertices"]:
            v = int(item["id"])
            x = float(item["x"])
            y = float(item["y"])
            new_vertices[v] = (x, y)

        new_edges = []

        for item in data["edges"]:
            a = int(item["a"])
            b = int(item["b"])
            eid = int(item["id"])

            if a not in new_vertices or b not in new_vertices:
                raise ValueError(
                    "Ребро ссылается на отсутствующую вершину."
                )

            new_edges.append({"id": eid, "a": a, "b": b})

        if len(new_vertices) > MAX_VERTICES or len(new_edges) > MAX_EDGES:
            raise ValueError("Файл превышает допустимые ограничения.")

        if len(set(new_vertices)) != len(new_vertices):
            raise ValueError("Обнаружены повторяющиеся ID вершин.")

        if len({e["id"] for e in new_edges}) != len(new_edges):
            raise ValueError("Обнаружены повторяющиеся ID рёбер.")

        if any(e["a"] == e["b"] for e in new_edges) and not data.get("allow_loops", False):
            raise ValueError("В файле есть петли, но они запрещены.")

        if not data.get("allow_multiple", False):
            seen = set()
            for e in new_edges:
                key = (
                    (e["a"], e["b"])
                    if data.get("directed", True)
                    else tuple(sorted((e["a"], e["b"])))
                )
                if key in seen:
                    raise ValueError("В файле есть кратные рёбра.")
                seen.add(key)

        remember()

        vertices = new_vertices
        edges = new_edges

        directed = bool(data.get("directed", True))
        allow_multiple = bool(data.get("allow_multiple", False))
        allow_loops = bool(data.get("allow_loops", False))

        next_vertex_id = max(
            int(data.get("next_vertex_id", 1)),
            max(vertices.keys(), default=0) + 1
        )

        next_edge_id = max(
            int(data.get("next_edge_id", 1)),
            max((e["id"] for e in edges), default=0) + 1
        )

        graph_type_var.set(
            "Ориентированный" if directed else "Неориентированный"
        )
        multi_var.set(allow_multiple)
        loops_var.set(allow_loops)

        selected_vertex = None
        selected_edge = None
        edge_start = None

        refresh()
        status_var.set("Граф загружен: " + filename)

    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        messagebox.showerror("Ошибка загрузки", str(exc))


# ============================================================
# ЭКСПОРТ МАТРИЦ В CSV
# ============================================================

def export_csv():
    filename = filedialog.asksaveasfilename(
        title="Экспорт матриц",
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv")]
    )

    if not filename:
        return

    try:
        ids, adj = adjacency_matrix()
        _, inc = incidence_matrix()

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:
            writer = csv.writer(f, delimiter=";")

            writer.writerow(["Матрица смежности"])
            writer.writerow(["v"] + ids)

            for v, row in zip(ids, adj):
                writer.writerow([v] + row)

            writer.writerow([])
            writer.writerow(["Матрица инцидентности"])
            writer.writerow(["v"] + [f"e{e['id']}" for e in edges])

            for v, row in zip(ids, inc):
                writer.writerow([v] + row)

        status_var.set("Матрицы экспортированы: " + filename)

    except OSError as exc:
        messagebox.showerror("Ошибка экспорта", str(exc))
# ============================================================
# КНОПКИ УПРАВЛЕНИЯ
# ============================================================

actions = ttk.Frame(main)
actions.pack(fill="x", pady=(0, 5))

ttk.Button(
    actions,
    text="↶ Отмена (Ctrl+Z)",
    command=undo
).pack(side="left", padx=2)

ttk.Button(
    actions,
    text="Очистить всё",
    command=clear_all
).pack(side="left", padx=2)

ttk.Button(
    actions,
    text="Разложить автоматически",
    command=auto_layout
).pack(side="left", padx=2)

ttk.Button(
    actions,
    text="Сохранить JSON",
    command=save_json
).pack(side="left", padx=2)

ttk.Button(
    actions,
    text="Загрузить JSON",
    command=load_json
).pack(side="left", padx=2)

ttk.Button(
    actions,
    text="Экспорт CSV",
    command=export_csv
).pack(side="left", padx=2)


# ============================================================
# ЗАПУСК
# ============================================================

set_mode("vertex")
refresh()
root.mainloop()