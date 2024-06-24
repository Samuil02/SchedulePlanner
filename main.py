from ortools.sat.python import cp_model


model = cp_model.CpModel()

print('Введите кол-во дней в месяце:')
num_days = int(input())

print('Введите кол-во сотрудников:')
num_workers = int(input())

print('Введите среднюю нагрузку (>2):')
avg_load = int(input())

print('Введите день недели, с которого начинается месяц (1-7):')
begin_day = int(input())

max_shift = 12

S = ['Shift1', 'Shift2']
W = ['Worker' + str(n) for n in range(1, num_workers + 1)]
D = ['Day' + str(n) for n in range(1, num_days + 1)]
G = ['Shift_schedule' + str(n) for n in range(1, 6)]

dict_generate_func = {
    G[0]: lambda i: 1 <= (i + begin_day) % 7 <= 5,  # "Пять через два" (вых: сб, вс)
    # Четыре комбинации графиков смен "два через два". Каждая последующая смещена относительно предыдущей на 1 шаг
    G[1]: lambda i: i % 4 <= 1,
    G[2]: lambda i: (i + 1) % 4 <= 1,
    G[3]: lambda i: (i + 2) % 4 <= 1,
    G[4]: lambda i: (i + 3) % 4 <= 1
}

# Словарь с вариантами графиков смен
SS = {}

for d in D:
    for g in G:
        SS[d, g] = dict_generate_func[g](D.index(d))

# Переменные-комбинации
X = {}

for s in S:
    for w in W:
        for d in D:
            var_name = f"x_{s}_{w}_{d}"
            X[s, w, d] = model.NewBoolVar(var_name)

# Переменные-индикаторы связи между сотрудниками и графиками смен
Z = {}

for w in W:
    for g in G:
        var_name = f"z_{w}_{g}"
        Z[w, g] = model.NewBoolVar(var_name)

# Каждый сотрудник работает не более одной смены в день
for w in W:
    for d in D:
        lst_vars = [X[s, w, d] for s in S]

        model.AddAtMostOne(lst_vars)

# Каждый день каждая смена занята минимум одним сотрудником
for s in S:
    for d in D:
        lst_vars = [X[s, w, d] for w in W]

        model.AddAtLeastOne(lst_vars)

# Кол-во сотрудников в нагрузке
for d in D:
    lst_vars = [X[s, w, d] for s in S for w in W]

    the_monday = 1 if (D.index(d) + begin_day) % 7 == 1 else 0
    the_sunday = -1 if (D.index(d) + begin_day) % 7 == 0 else 0

    model.Add(sum(lst_vars) == avg_load + the_monday + the_sunday)

# Ограничение по кол-ву смен (часов) работы в месяц
for w in W:
    lst_vars = [X[s, w, d] for s in S for d in D]

    model.AddLinearConstraint(sum(lst_vars), 0, max_shift)

# Каждый сотрудник работает только по одному графику смен
for w in W:
    lst_vars = [Z[w, g] for g in G]

    model.AddExactlyOne(lst_vars)

# Связь X и Z
for s in S:
    for w in W:
        for d in D:

            lst_vars = [(SS[d, g] * Z[w, g]) for g in G]

            model.Add(X[s, w, d] <= sum(lst_vars))

# Решение
solver = cp_model.CpSolver()

status = solver.Solve(model)

if status == cp_model.FEASIBLE:
    print('Решение найдено')

# Сохранение результата
result = {}

for key, val in X.items():
    solver_item = solver.Value(val)

    if solver_item > 0:
        result[key[1], key[2]] = key[0]

# Вывод результата
print(' ' * 8, end=' ')
[print(d + ' ' * (6 - len(d)), end=' ') for d in D]
print()

name_of_days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

print(' ' * 8, end=' ')
[print(name_of_days[(D.index(d) + begin_day) % 7] + ' ' * 3, end=' ') for d in D]
print()

for w in W:
    print(w + ' ' * (8 - len(w)), end=' ')
    for d in D:
        if result.get((w, d)) is None:
            print(' ' * 6, end=' ')
        else:
            print(result[w, d], end=' ')
    print()

result_shifts = {}

for key, val in Z.items():
    solver_item = solver.Value(val)

    if solver_item > 0:
        result_shifts[key[0]] = key[1]

print('\nНазначение графиков смен сотрудникам')
for w in W:
    print(w, result_shifts[w])
