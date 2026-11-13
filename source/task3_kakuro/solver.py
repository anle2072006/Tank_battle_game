import time
from combos import get_valid_combinations
from validator import Validator
from events import event_bus

class KakuroSolver:
    def __init__(self, board, var_heuristic='mrv', val_heuristic='lcv', event_bus=event_bus):
        self.board = board
        self.var_heuristic = var_heuristic
        self.val_heuristic = val_heuristic
        self.event_bus = event_bus
        
        # Thống kê
        self.assignments = 0
        self.backtracks = 0
        self.execution_time = 0

    def constraint_propagation(self):
        changed = True
        while changed:
            changed = False
            for run in self.board.runs:
                length = len(run.cells)
                valid_combos = get_valid_combinations(run.target_sum, length)
                
                # Điều kiện giữ tổ hợp là giá trị đã gán phải nằm trong tổ hợp
                current_values = [cell.value for cell in run.cells if cell.value != 0]
                filtered_combos = []
                for combo in valid_combos:
                    if all(val in combo for val in current_values):
                        filtered_combos.append(combo)

                if not filtered_combos:
                    return False  # Dead end

                # Miền khả dĩ của ô là hợp mọi chữ số của mọi tổ hợp còn sống
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
                            if self.event_bus:
                                self.event_bus.notify("DOMAIN_UPDATE", (cell, cell.domain))
        return True

    def select_unassigned_variable(self):
        unassigned = [c for c in self.board.white_cells if c.value == 0]
        if not unassigned:
            return None
            
        if self.var_heuristic == 'mrv':
            return min(unassigned, key=lambda cell: len(cell.domain))
        return unassigned[0] # Default fallback

    def order_domain_values(self, cell):
        if self.val_heuristic == 'lcv':
            # LCV: Đếm số ô cùng run chưa gán chứa giá trị này
            def lcv_score(val):
                score = 0
                runs = [run for run in self.board.runs if cell in run.cells]
                for run in runs:
                    for c in run.cells:
                        if c != cell and c.value == 0 and val in c.domain:
                            score += 1
                return score
            return sorted(list(cell.domain), key=lcv_score)
        
        return sorted(list(cell.domain))

    def solve_recursive(self, use_propagation):
        if use_propagation:
            if not self.constraint_propagation():
                return False

        cell = self.select_unassigned_variable()
        if cell is None:
            return Validator.is_board_valid(self.board)

        # Lưu bản sao miền và giá trị của mọi ô trắng trước khi thử gán
        saved_domains = {c: c.domain.copy() for c in self.board.white_cells}
        saved_values = {c: c.value for c in self.board.white_cells}

        for val in self.order_domain_values(cell):
            cell.value = val
            self.assignments += 1
            if self.event_bus:
                self.event_bus.notify("ASSIGN", (cell, val))
            
            if Validator.is_board_valid(self.board):
                if self.solve_recursive(use_propagation):
                    return True

            # Khôi phục lại miền và giá trị trước khi thử giá trị tiếp theo
            for c in self.board.white_cells:
                c.domain = saved_domains[c].copy()
                c.value = saved_values[c]
                
            self.backtracks += 1
            if self.event_bus:
                self.event_bus.notify("BACKTRACK", cell)

        # Khi hết giá trị mà vẫn thất bại, đảm bảo khôi phục miền trước khi return False
        for c in self.board.white_cells:
            c.domain = saved_domains[c].copy()
            c.value = saved_values[c]

        return False

    def solve(self, use_propagation=True):
        # Hàm bọc ngoài để reset bộ đếm và timer, đồng thời phát sự kiện tổng
        self.assignments = 0
        self.backtracks = 0
        start_time = time.time()
        
        if self.event_bus:
            self.event_bus.notify('INIT', board=self.board)
            
        success = self.solve_recursive(use_propagation)
        
        self.execution_time = time.time() - start_time
        
        if self.event_bus:
            if success:
                self.event_bus.notify('SOLVED', board=self.board, stats=self.get_stats())
            else:
                self.event_bus.notify('FAILED', board=self.board, stats=self.get_stats())
                
        return success

    def get_stats(self):
        return {
            'assignments': self.assignments,
            'backtracks': self.backtracks,
            'execution_time': self.execution_time
        }