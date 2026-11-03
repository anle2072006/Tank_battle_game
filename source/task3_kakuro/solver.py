from combos import get_valid_combinations
from validator import Validator
from events import event_bus

class KakuroSolver:
    """Bộ giải CSP kết hợp Constraint Propagation, Backtracking và Heuristic MRV."""
    def __init__(self, board):
        self.board = board

    def constraint_propagation(self):
        """Áp dụng AC-3 / lọc miền giá trị dựa trên các tổ hợp hợp lệ của từng Run."""
        changed = True
        while changed:
            changed = False
            for run in self.board.runs:
                length = len(run.cells)
                valid_combos = get_valid_combinations(run.target_sum, length)
                
                # Lọc bỏ các tổ hợp không khớp với giá trị hiện tại của các ô đã gán
                current_values = [(i, cell.value) for i, cell in enumerate(run.cells) if cell.value != 0]
                filtered_combos = []
                for combo in valid_combos:
                    match = True
                    for idx, val in current_values:
                        if combo[idx] != val:
                            match = False
                            break
                    if match:
                        filtered_combos.append(combo)

                if not filtered_combos:
                    return False  # Miền giá trị rỗng -> Dead end

                # Cập nhật lại domain cho từng ô trong run
                for i, cell in enumerate(run.cells):
                    if cell.value == 0:
                        possible_values = set(combo[i] for combo in filtered_combos)
                        new_domain = cell.domain.intersection(possible_values)
                        if new_domain != cell.domain:
                            if not new_domain:
                                return False
                            cell.domain = new_domain
                            changed = True
                            event_bus.notify("DOMAIN_UPDATE", (cell, cell.domain))
        return True

    def select_unassigned_variable_mrv(self):
        """Heuristic MRV (Minimum Remaining Values): Chọn ô trắng có số lượng miền giá trị ít nhất."""
        unassigned = [c for c in self.board.white_cells if c.value == 0]
        if not unassigned:
            return None
        return min(unassigned, key=lambda cell: len(cell.domain))

    def solve(self):
        """Hàm giải chính bằng Backtracking Search."""
        if not self.constraint_propagation():
            return False

        cell = self.select_unassigned_variable_mrv()
        if cell is None:
            return Validator.is_board_valid(self.board)

        for val in sorted(cell.domain):
            cell.value = val
            event_bus.notify("ASSIGN", (cell, val))
            
            # Lưu lại domain trước khi sao lưu/lan truyền
            if Validator.is_board_valid(self.board):
                # Đệ quy giải tiếp
                if self.solve():
                    return True

            cell.value = 0
            event_bus.notify("BACKTRACK", cell)
            # Khôi phục lại domain nếu cần thiết (hoặc chạy lại propagation)

        return False