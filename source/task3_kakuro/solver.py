from combos import get_valid_combinations
from validator import Validator
from events import event_bus

class KakuroSolver:
    def __init__(self, board):
        self.board = board

    def constraint_propagation(self):
        changed = True
        while changed:
            changed = False
            for run in self.board.runs:
                length = len(run.cells)
                valid_combos = get_valid_combinations(run.target_sum, length)
                
                # Sửa 2 (dòng 25): Điều kiện giữ tổ hợp là giá trị đã gán phải nằm trong tổ hợp
                current_values = [cell.value for cell in run.cells if cell.value != 0]
                filtered_combos = []
                for combo in valid_combos:
                    if all(val in combo for val in current_values):
                        filtered_combos.append(combo)

                if not filtered_combos:
                    return False  # Dead end

                # Sửa 2 (dòng 37): Miền khả dĩ của ô là hợp mọi chữ số của mọi tổ hợp còn sống
                if filtered_combos:
                    all_possible_digits = set().union(*filtered_combos)
                else:
                    all_possible_digits = set()

                for cell in run.cells:
                    if cell.value == 0:
                        new_domain = cell.domain.intersection(all_possible_digits)
                        if not new_domain:
                            return False
                        if new_domain != cell.domain:
                            cell.domain = new_domain
                            changed = True
                            event_bus.notify("DOMAIN_UPDATE", (cell, cell.domain))
        return True

    def select_unassigned_variable_mrv(self):
        unassigned = [c for c in self.board.white_cells if c.value == 0]
        if not unassigned:
            return None
        return min(unassigned, key=lambda cell: len(cell.domain))

    def solve(self):
        if not self.constraint_propagation():
            return False

        cell = self.select_unassigned_variable_mrv()
        if cell is None:
            return Validator.is_board_valid(self.board)

        # Sửa 3: Lưu bản sao miền và giá trị của mọi ô trắng trước khi thử gán
        saved_domains = {c: c.domain.copy() for c in self.board.white_cells}
        saved_values = {c: c.value for c in self.board.white_cells}

        for val in sorted(cell.domain):
            cell.value = val
            event_bus.notify("ASSIGN", (cell, val))
            
            if Validator.is_board_valid(self.board):
                if self.solve():
                    return True

            # Khôi phục lại miền và giá trị trước khi thử giá trị tiếp theo
            for c in self.board.white_cells:
                c.domain = saved_domains[c].copy()
                c.value = saved_values[c]
            event_bus.notify("BACKTRACK", cell)

        # Sửa 3: Khi hết giá trị mà vẫn thất bại, đảm bảo khôi phục miền trước khi return False
        for c in self.board.white_cells:
            c.domain = saved_domains[c].copy()
            c.value = saved_values[c]

        return False