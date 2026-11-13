import statistics
from board import Board
from solver import KakuroSolver
from validator import Validator


def board_solution(board):
    """Nghiệm hiện tại của bảng dưới dạng dict {(hàng, cột): giá trị}."""
    return {(c.row, c.col): c.value for c in board.white_cells}


def is_fully_valid(board):
    """Đã điền hết và mọi run hợp lệ (dùng Validator, độc lập với solver)."""
    return all(c.value != 0 for c in board.white_cells) and Validator.is_board_valid(board)


def run_config(grid, var="mrv_degree", val="none", propagation=True,
               max_assignments=None, event_bus=None):
    """Giải một bảng mới với một cấu hình, trả về dict kết quả."""
    board = Board(grid)
    solver = KakuroSolver(board, var_heuristic=var, val_heuristic=val,
                          use_propagation=propagation, event_bus=event_bus,
                          max_assignments=max_assignments)
    success = solver.solve()
    result = {"var": var, "val": val, "propagation": propagation, "solved": success,
              "valid": success and is_fully_valid(board),
              "solution": board_solution(board) if success else None}
    result.update(solver.get_stats())
    return result


def compare_configs(grid, configs, max_assignments=None):
    """configs: danh sách (var, val, propagation)."""
    return [run_config(grid, var, val, prop, max_assignments) for var, val, prop in configs]


def stability_test(grid, var, val, propagation=True, repeats=20):
    """Chạy lặp một cấu hình, kiểm tra nghiệm và số liệu tìm kiếm giống nhau mọi lần."""
    results = [run_config(grid, var, val, propagation) for _ in range(repeats)]
    first = results[0]
    same_solution = all(r["solution"] == first["solution"] for r in results)
    same_counts = all((r["assignments"], r["backtracks"]) == (first["assignments"], first["backtracks"])
                      for r in results)
    times = [r["execution_time"] for r in results]
    return {"repeats": repeats, "all_valid": all(r["valid"] for r in results),
            "same_solution": same_solution, "same_counts": same_counts,
            "mean_time": statistics.mean(times),
            "std_time": statistics.pstdev(times),
            "assignments": first["assignments"], "backtracks": first["backtracks"]}


def count_solutions(grid, limit=2):
    """Đếm nghiệm bằng vét cạn có cắt tỉa theo tổng. Viết riêng, không dùng KakuroSolver.

    Dừng khi đã tìm đủ `limit` nghiệm. Dùng để kiểm chứng bảng có nghiệm duy nhất hay nhiều nghiệm.
    """
    board = Board(grid)
    cells = sorted(board.white_cells, key=lambda c: (c.row, c.col))
    runs_of = {id(c): [] for c in cells}
    for run in board.runs:
        for c in run.cells:
            runs_of[id(c)].append(run)
    value = {}

    def feasible(run):
        vals = [value[id(c)] for c in run.cells if id(c) in value]
        if len(set(vals)) != len(vals):
            return False
        total = sum(vals)
        left = len(run.cells) - len(vals)
        if left == 0:
            return total == run.target_sum
        # tổng nhỏ nhất và lớn nhất còn có thể đạt được với `left` chữ số khác nhau (bỏ qua việc trùng với vals)
        return total + left * (left + 1) // 2 <= run.target_sum <= total + sum(range(9, 9 - left, -1))

    found = 0

    def dfs(i):
        nonlocal found
        if found >= limit:
            return
        if i == len(cells):
            found += 1
            return
        cell = cells[i]
        for v in range(1, 10):
            value[id(cell)] = v
            if all(feasible(r) for r in runs_of[id(cell)]):
                dfs(i + 1)
            del value[id(cell)]

    dfs(0)
    return found


def format_table(headers, rows):
    """Bảng chữ căn cột để in ra console hoặc notebook."""
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    line = " | ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    sep = "-+-".join("-" * w for w in widths)
    body = [" | ".join(str(c).ljust(w) for c, w in zip(r, widths)) for r in rows]
    return "\n".join([line, sep] + body)


def results_table(results):
    headers = ["Chọn biến", "Chọn giá trị", "Lan truyền", "Giải được", "Lần gán", "Quay lui", "Cắt miền", "Thời gian (s)"]
    rows = []
    for r in results:
        solved = "giới hạn" if r["hit_limit"] else ("có" if r["solved"] else "không")
        rows.append([r["var"], r["val"], "có" if r["propagation"] else "không", solved,
                     r["assignments"], r["backtracks"], r["domain_updates"], f"{r['execution_time']:.4f}"])
    return format_table(headers, rows)
