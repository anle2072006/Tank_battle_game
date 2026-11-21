from collections import Counter

from board import Board
from solver import KakuroSolver
from events import event_bus
from validator import Validator
from experiments import (compare_configs, results_table, stability_test, run_config,
                         count_solutions, is_fully_valid)
from puzzles import (SAMPLE_5X5, SAMPLE_9X9, UNSOLVABLE_COMBO, UNSOLVABLE_SEARCH,
                     MULTI_SOLUTION)

MAX_ASSIGNMENTS = 50000


class EventRecorder:
    """Listener mẫu cho UI: ghi lại toàn bộ sự kiện để phát lại sau."""
    def __init__(self):
        self.events = []

    def __call__(self, event_type, data):
        self.events.append((event_type, data))


def check_structure(grid, expected, name):
    board = Board(grid)
    stats = board.print_structure_stats()
    assert stats == expected, f"Cấu trúc bảng {name} sai: {stats}, cần {expected}"
    print(f"[OK] Bảng {name} đúng cấu trúc\n")


def demo_solve(grid, name):
    recorder = EventRecorder()
    event_bus.subscribe(recorder)
    board = Board(grid)
    solver = KakuroSolver(board)
    success = solver.solve()
    event_bus.unsubscribe(recorder)

    ok = success and is_fully_valid(board)
    print(f"[{'THÀNH CÔNG' if ok else 'THẤT BẠI'}] Bảng {name}: {solver.get_stats()}")
    counts = Counter(event_type for event_type, _ in recorder.events)
    print(f"Sự kiện đã phát: {dict(counts)}")
    if ok:
        board.display()
    print()


if __name__ == "__main__":
    print("=== 1. KIỂM TRA CẤU TRÚC BẢNG ===")
    check_structure(SAMPLE_5X5, (12, 8, 60, 60), "5x5")
    check_structure(SAMPLE_9X9, (48, 28, 249, 249), "9x9")

    print("=== 2. GIẢI BẢNG 5x5 VÀ 9x9 (MRV, không LCV) ===")
    demo_solve(SAMPLE_5X5, "5x5")
    demo_solve(SAMPLE_9X9, "9x9")

    print("=== 3. SO SÁNH CÁC CẤU HÌNH TRÊN BẢNG 9x9 (có lan truyền) ===")
    configs = [(v, l, True) for v in ("none", "mrv", "degree", "mrv_degree") for l in ("none", "lcv")]
    print(results_table(compare_configs(SAMPLE_9X9, configs, MAX_ASSIGNMENTS)))
    print(f"(giới hạn {MAX_ASSIGNMENTS} lần gán mỗi cấu hình)\n")

    print("=== 4. TẮT LAN TRUYỀN RÀNG BUỘC ===")
    no_prop = [(v, "none", False) for v in ("none", "mrv")]
    print(results_table(compare_configs(SAMPLE_9X9, no_prop, 200000)))
    print()

    print("=== 5. ĐỘ ỔN ĐỊNH (chạy lặp 20 lần, cấu hình mrv) ===")
    for name, grid in (("5x5", SAMPLE_5X5), ("9x9", SAMPLE_9X9)):
        s = stability_test(grid, "mrv", "none", True, repeats=20)
        print(f"{name}: {s}")
    print()

    print("=== 6. BẢNG ĐẶC BIỆT ===")
    for name, grid in (("vô nghiệm (hết tổ hợp)", UNSOLVABLE_COMBO),
                       ("vô nghiệm (phải tìm kiếm)", UNSOLVABLE_SEARCH)):
        r = run_config(grid)
        print(f"{name}: solved={r['solved']} (kỳ vọng False), số nghiệm vét cạn = {count_solutions(grid)}")
    r = run_config(MULTI_SOLUTION)
    print(f"nhiều nghiệm: solved={r['solved']} valid={r['valid']}, số nghiệm vét cạn = {count_solutions(MULTI_SOLUTION, limit=10)} (kỳ vọng 2)")
    print()

    print("=== 7. KIỂM CHỨNG ĐỘC LẬP: SỐ NGHIỆM CỦA ĐỀ ===")
    print(f"5x5: {count_solutions(SAMPLE_5X5)} nghiệm (dừng ở 2), 9x9: {count_solutions(SAMPLE_9X9)} nghiệm (dừng ở 2)")
