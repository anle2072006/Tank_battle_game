from board import Board
from solver import KakuroSolver
from events import event_bus
from validator import Validator
import time

def ui_listener(event_type, data):
    pass

if __name__ == "__main__":
    event_bus.subscribe(ui_listener)

    # 1. Bảng 5x5 đã được sửa chuẩn xác theo danh sách lỗi
    sample_grid_5x5 = [
        [(None, None), (None, None), (None, 21), (None, 14), (None, None)],
        [(None, None), (12, 14), 0, 0, (None, 11)],
        [(21, None), 0, 0, 0, 0],
        [(11, None), 0, 0, 0, 0],
        [(None, None), (16, None), 0, 0, (None, None)]
    ]

    # 2. Bảng 9x9 đã được sửa đúng 16 điểm theo danh sách chi tiết
    sample_grid_9x9 = [
        [(None, None), (None, None), (None, 44), (None, 16), (None, 9), (None, None), (None, 15), (None, 44), (None, None)], # Hàng 0
        [(None, None), (22, None), 0, 0, 0, (3, 11), 0, 0, (None, 14)],                                                           # Hàng 1 (Đã sửa cột 0, cột 1, 4, 5, 7, 8)
        [(None, None), (28, 17), 0, 0, 0, 0, 0, 0, 0],                                                                           # Hàng 2 (Đã sửa cột 0, cột 1 chung 28,17)
        [(14, None), 0, 0, (None, None), (20, 12), 0, 0, 0, 0],                                                                  # Hàng 3 (Đã sửa (12,20) thành (20,12))
        [(17, None), 0, 0, (22, 29), 0, 0, 0, 0, (None, 7)],                                                                     # Hàng 4
        [(None, None), (28, 12), 0, 0, 0, 0, (12, None), 0, 0],                                                                  # Hàng 5 (Đã sửa (12,28) thành (28,12) và (None,12) thành (12,None))
        [(14, None), 0, 0, 0, 0, (None, 7), (6, 12), 0, 0],                                                                      # Hàng 6 (Đã sửa cột 4, 5, 6)
        [(39, None), 0, 0, 0, 0, 0, 0, 0, (None, None)],                                                                         # Hàng 7 (Đã sửa ô cuối cột 8 thành (None, None))
        [(None, None), (16, None), 0, 0, (8, None), 0, 0, 0, (None, None)]                                                       # Hàng 8 (Đã sửa (None,8) thành (8,None))
    ]

    print("=== KIỂM TRA CẤU TRÚC BẢNG 9x9 ===")
    board_9x9 = Board(sample_grid_9x9)
    num_white, num_runs, total_h, total_v = board_9x9.print_structure_stats()

    # Kiểm tra nhanh tính chính xác của cấu trúc bảng 9x9
    assert num_white == 48 and num_runs == 28 and total_h == 249 and total_v == 249, \
        f"Cấu trúc bảng 9x9 chưa khớp! Nhận được: White={num_white}, Runs={num_runs}, H={total_h}, V={total_v}"

    print("\n[OK] Cấu trúc bảng 9x9 hoàn toàn chính xác! Đang tiến hành giải...")
    
    solver_9x9 = KakuroSolver(board_9x9, var_heuristic="MRV", val_heuristic="LCV")
    start_time = time.time()
    success = solver_9x9.solve()
    end_time = time.time()

    if success and Validator.is_board_valid(board_9x9):
        print(f"\n[THÀNH CÔNG] Đã giải xong bảng 9x9 trong {end_time - start_time:.4f} giây!")
        print(f"Thống kê: {solver_9x9.assignments} gán, {solver_9x9.backtracks} quay lui.")
        print("=== KẾT QUẢ GIẢI KAKURO 9x9 ===")
        board_9x9.display()
    else:
        print("\n[THẤT BẠI] Không tìm thấy lời giải hoặc lời giải không hợp lệ.")

    # 3. Kiểm tra giải nhanh bảng 5x5
    print("\n=== KIỂM TRA GIẢI BẢNG 5x5 ===")
    board_5x5 = Board(sample_grid_5x5)
    solver_5x5 = KakuroSolver(board_5x5, var_heuristic="MRV", val_heuristic="LCV")
    if solver_5x5.solve() and Validator.is_board_valid(board_5x5):
        print("[THÀNH CÔNG] Đã giải xong bảng 5x5!")
        board_5x5.display()
    else:
        print("[THẤT BẠI] Bảng 5x5 không tìm thấy lời giải.")