from board import Board
from solver import KakuroSolver
from events import event_bus
import time

def ui_listener(event_type, data):
    pass

if __name__ == "__main__":
    event_bus.subscribe(ui_listener)

    # 1. Kiểm tra bảng 5x5 mẫu (nếu cần)
    sample_grid_5x5 = [
        [(None, None), (None, None), (None, None), (21, None), (14, None)],
        [(None, None), (14, 12), (None, None), 0, 0, (11, None)],
        [(21, None), 0, 0, 0, 0],
        [(11, None), 0, 0, 0, 0],
        [(None, None), (None, 16), 0, 0, (None, None)]
    ]

    # 2. Bảng 9x9 chuẩn xác theo đề bài (Đúng các hướng dẫn về thứ tự cột, tuple, và ô xám (None, None))
    sample_grid_9x9 = [
        [(None, None), (None, None), (None, 44), (None, 16), (None, 9), (None, None), (None, 15), (None, 44), (None, None)],
        [(22, None), 0, 0, 0, (3, 11), 0, 0, (14, None), (None, None)],
        [(28, None), 0, 0, 0, 0, 0, 0, 0, 0],
        [(14, None), 0, 0, (None, None), (12, 20), 0, 0, 0, 0],
        [(17, None), 0, 0, (22, 29), 0, 0, 0, 0, (None, 7)],
        [(None, None), (12, 28), 0, 0, 0, 0, (None, 12), 0, 0],
        [(14, None), 0, 0, 0, (None, 7), (6, 12), 0, 0, 0],
        [(39, None), 0, 0, 0, 0, 0, 0, 0, 0],
        [(None, None), (16, None), 0, 0, (None, 8), 0, 0, 0, (None, None)]
    ]

    print("=== KIỂM TRA CẤU TRÚC BẢNG 9x9 ===")
    board_9x9 = Board(sample_grid_9x9)
    num_white, num_runs, total_h, total_v = board_9x9.print_structure_stats()

    # Kiểm tra nhanh tính chính xác của cấu trúc bảng
    assert num_white == 48 and num_runs == 28 and total_h == 249 and total_v == 249, \
        "Cấu trúc bảng chưa khớp với thông số yêu cầu (48, 28, 249, 249)!"

    print("\n[OK] Cấu trúc bảng hoàn toàn chính xác! Đang tiến hành giải bảng Kakuro 9x9...")
    
    solver = KakuroSolver(board_9x9)
    start_time = time.time()
    success = solver.solve()
    end_time = time.time()

    if success:
        print(f"\n[THÀNH CÔNG] Đã giải xong bảng 9x9 trong {end_time - start_time:.4f} giây!\n")
        print("=== KẾT QUẢ GIẢI KAKURO 9x9 ===")
        board_9x9.display()
    else:
        print("\n[THẤT BẠI] Không tìm thấy lời giải.")