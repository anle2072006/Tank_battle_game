from board import Board
from solver import KakuroSolver
from events import event_bus

def ui_listener(event_type, data):
    if event_type == "ASSIGN":
        cell, val = data
        pass
    elif event_type == "BACKTRACK":
        pass

if __name__ == "__main__":
    # Đăng ký listener mẫu
    event_bus.subscribe(ui_listener)

    # Khởi tạo bảng Kakuro phức tạp 9x9 (mô phỏng đề bài Task 3)
    # None hoặc 0 là ô trắng. Tuple (row_sum, col_sum) là ô gợi ý đen.
    # Dưới đây là cấu trúc mẫu mô phỏng bảng 9x9 theo yêu cầu đồ án:
    sample_grid = [
        [None, (44, None), (16, None), (9, None), None, (15, None), (44, None), None, None],
        [(22, None), 0, 0, 0, (11, 3), 0, 0, (14, None), None],
        [(28, None), 0, 0, 0, 0, 0, 0, 0, 0],
        [(14, None), 0, 0, (20, 12), 0, 0, 0, 0, 0],
        [(17, None), 0, 0, (29, 22), 0, 0, 0, 0, (7, None)],
        [None, (28, 12), 0, 0, 0, 0, (12, None), 0, 0],
        [(14, None), 0, 0, 0, (7, None), (12, 6), 0, 0, 0],
        [(39, None), 0, 0, 0, 0, 0, 0, 0, 0],
        [None, (16, None), 0, 0, (8, None), 0, 0, 0, None]
    ]

    print("=== TRẠNG THÁI BẢNG KAKURO BAN ĐẦU ===")
    board = Board(sample_grid)
    board.display()

    print("\nĐang chạy thuật toán giải CSP (Constraint Propagation + Backtracking + MRV)...")
    solver = KakuroSolver(board)
    
    import time
    start_time = time.time()
    success = solver.solve()
    end_time = time.time()

    if success:
        print(f"\n[THÀNH CÔNG] Đã tìm thấy lời giải sau {end_time - start_time:.4f} giây!\n")
        print("=== KẾT QUẢ GIẢI KAKURO ===")
        board.display()
    else:
        print("\n[THẤT BẠI] Không tìm thấy lời giải hợp lệ cho bảng này.")