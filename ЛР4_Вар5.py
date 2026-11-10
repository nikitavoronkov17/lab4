"""
Лабораторная работа № 4. Вариант 5.
Последовательный, двоичный и интерполяционный поиск.
n = 10000, 31623, 100000, 316228, 1000000; распределение P (равномерное);
k = 5000 неуспешных запросов. Доп. задание Б5 — сравнение с bisect.

Всё в одном файле: генерация данных, три алгоритма поиска, обёртка
над bisect, замер и эксперимент. Внешних зависимостей, кроме
matplotlib для графиков, нет.
"""
import math
import random
import time
from bisect import bisect_left


# ==================== Вспомогательные функции ====================

def generate_sorted_data(n, seed=42):
    """Упорядоченный массив из n различных равномерных ключей из [0; 10n]."""
    rng = random.Random(seed + n)
    return sorted(rng.sample(range(10 * n), n))


def make_queries(a, k, seed=1):
    """k неуспешных запросов: ключи из [0; 10·n], которых нет в массиве."""
    rng = random.Random(seed)
    n = len(a)
    aset = set(a)
    queries = []
    hi = 10 * n
    while len(queries) < k:
        q = rng.randint(0, hi)
        if q not in aset:
            queries.append(q)
    return queries


# ==================== Три классических алгоритма ====================

def linear_search(a, q):
    """Последовательный поиск. Возвращает (индекс или −1, число сравнений)."""
    for i, value in enumerate(a):
        if value == q:
            return i, i + 1
    return -1, len(a)


def binary_search(a, q):
    """Двоичный поиск в упорядоченном массиве (итеративная форма)."""
    lo, hi, cmps = 0, len(a) - 1, 0
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        cmps += 1
        if a[mid] == q:
            return mid, cmps
        if a[mid] < q:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1, cmps


def interpolation_search(a, q):
    """Интерполяционный поиск в упорядоченном массиве."""
    lo, hi, cmps = 0, len(a) - 1, 0
    while lo <= hi and a[lo] <= q <= a[hi]:
        if a[lo] == a[hi]:
            cmps += 1
            return (lo, cmps) if a[lo] == q else (-1, cmps)
        mid = lo + (q - a[lo]) * (hi - lo) // (a[hi] - a[lo])
        cmps += 1
        if a[mid] == q:
            return mid, cmps
        if a[mid] < q:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1, cmps


# ==================== Б5: обёртка над bisect ====================

def bisect_search(a, q):
    """Поиск через стандартный модуль bisect.
    Возвращает (индекс или −1, оценочное число сравнений = log2(n)+1)."""
    i = bisect_left(a, q)
    cmps = math.floor(math.log2(len(a))) + 1 if a else 0
    if i < len(a) and a[i] == q:
        return i, cmps
    return -1, cmps


# ==================== Замер ====================

def benchmark(search_func, data, queries, repeats=3):
    """Возвращает (среднее время одного запроса в с, среднее число сравнений)."""
    times = []
    total_cmps = 0
    for _ in range(repeats):
        start = time.perf_counter()
        for q in queries:
            idx, c = search_func(data, q)
            assert idx == -1, f"{search_func.__name__}: найден {idx} для {q}"
            total_cmps += c
        times.append((time.perf_counter() - start) / len(queries))
    return sum(times) / len(times), total_cmps / (len(queries) * repeats)


# ==================== Эксперимент ====================

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    SIZES = [10_000, 31_623, 100_000, 316_228, 1_000_000]
    K = 5000
    algorithms = {
        "Последовательный": linear_search,
        "Двоичный": binary_search,
        "Интерполяционный": interpolation_search,
        "bisect (Б5)": bisect_search,
    }

    results_time = {name: [] for name in algorithms}
    results_cmps = {name: [] for name in algorithms}

    print(f"{'n':>10}" + "".join(f"{name:>22}" for name in algorithms))
    for n in SIZES:
        data = generate_sorted_data(n)
        queries = make_queries(data, K)
        row = f"{n:>10}"
        for name, func in algorithms.items():
            t, c = benchmark(func, data, queries, repeats=3)
            results_time[name].append(t * 1e6)   # мкс
            results_cmps[name].append(c)
            row += f"{t * 1e6:>14.2f} мкс {c:>5.1f}"
        print(row)

    # Отношения T(n_{i+1}) / T(n_i)
    print("\nОтношения T(n_{i+1}) / T(n_i):")
    for name in algorithms:
        ratios = [results_time[name][i + 1] / results_time[name][i]
                  for i in range(len(SIZES) - 1)]
        print(f"  {name:<22} " + " ".join(f"{r:>6.2f}" for r in ratios))

    # Теоретические значения для сверки с таблицей 5
    print("\nТеоретические значения:")
    for n in SIZES:
        print(f"  n = {n:>10}:  n = {n:>10},  "
              f"log2(n) = {math.log2(n):>5.2f},  "
              f"log2(log2(n)) = {math.log2(math.log2(n)):>5.2f}")

    # --- Графики ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for name, times in results_time.items():
        axes[0].plot(SIZES, times, marker="o", label=name)
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("n (лог. шкала)")
    axes[0].set_ylabel("Среднее время запроса, мкс")
    axes[0].set_title("Время одного запроса")
    axes[0].grid(True, which="both", ls="--", alpha=0.6)
    axes[0].legend()

    for name, cmps in results_cmps.items():
        axes[1].plot(SIZES, cmps, marker="o", label=name)
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("n (лог. шкала)")
    axes[1].set_ylabel("Среднее число сравнений")
    axes[1].set_title("Число сравнений на запрос")
    axes[1].grid(True, which="both", ls="--", alpha=0.6)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig("lr4_plot.png", dpi=150)
    plt.show()