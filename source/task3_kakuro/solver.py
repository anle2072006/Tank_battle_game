import time
from combos import get_valid_combinations
from validator import Validator
from events import event_bus as default_event_bus, EventType

VAR_HEURISTICS = ("none", "mrv", "degree", "mrv_degree")
VAL_HEURISTICS = ("none", "lcv")


class SearchLimitReached(Exception):
    """Dừng tìm kiếm khi vượt số lần gán tối đa."""


class KakuroSolver:
    """Bộ giải Kakuro: lan truyền ràng buộc + backtracking + heuristic.

    var_heuristic: none | mrv | degree | mrv_degree
    val_heuristic: none | lcv
    use_propagation: bật/tắt lan truyền ràng buộc (để so sánh hiệu quả)
    max_assignments: giới hạn số lần gán, dùng khi chạy cấu hình quá chậm
    """

    def __init__(self, board, var_heuristic="mrv", val_heuristic="none",
                 use_propagation=True, event_bus=default_event_bus,
                 max_assignments=None):
        self.board = board
        self.var_heuristic = str(var_heuristic).lower()
        self.val_heuristic = str(val_heuristic).lower()
        if self.var_heuristic not in VAR_HEURISTICS:
            raise ValueError(f"var_heuristic không hợp lệ: {var_heuristic!r}, chọn một trong {VAR_HEURISTICS}")
        if self.val_heuristic not in VAL_HEURISTICS:
            raise ValueError(f"val_heuristic không hợp lệ: {val_heuristic!r}, chọn một trong {VAL_HEURISTICS}")
        self.use_propagation = use_propagation
        self.event_bus = event_bus
        self.max_assignments = max_assignments

        # Mỗi ô trắng thuộc đúng 2 run, tính sẵn một lần để các heuristic không phải duyệt lại
        self.cell_to_runs = {c: [] for c in self.board.white_cells}
        for run in self.board.runs:
            for c in run.cells:
                self.cell_to_runs[c].append(run)

        self.assignments = 0
        self.backtracks = 0
        self.domain_updates = 0
        self.execution_time = 0.0
        self.hit_limit = False

    # ---------- sự kiện ----------
    def _emit(self, event_type, **data):
        if self.event_bus:
            self.event_bus.notify(event_type, data)

    # ---------- lan truyền ràng buộc ----------
    def constraint_propagation(self):
        """Lọc tổ hợp của từng run theo các giá trị đã gán, rồi thu hẹp miền các ô còn trống.

        Lặp đến khi không còn thay đổi. Trả về False nếu có miền rỗng hoặc run hết tổ hợp.
        """
        changed = True
        while changed:
            changed = False
            for run in self.board.runs:
                valid_combos = get_valid_combinations(run.target_sum, len(run.cells))

                # Giữ tổ hợp chứa mọi giá trị đã gán trong run
                current_values = [c.value for c in run.cells if c.value != 0]
                filtered_combos = [combo for combo in valid_combos
                                   if all(val in combo for val in current_values)]
                if not filtered_combos:
                    return False

                # Miền khả dĩ của ô = hợp mọi chữ số của các tổ hợp còn sống
                possible_digits = set().union(*filtered_combos)
                for cell in run.cells:
                    if cell.value == 0:
                        new_domain = cell.domain & possible_digits
                        if not new_domain:
                            return False
                        if new_domain != cell.domain:
                            old_domain = cell.domain
                            cell.domain = new_domain
                            changed = True
                            self.domain_updates += 1
                            self._emit(EventType.DOMAIN_UPDATE,
                                       cell=(cell.row, cell.col),
                                       old=sorted(old_domain), new=sorted(new_domain),
                                       run=(run.direction, run.target_sum))
        return True

    # ---------- heuristic chọn biến ----------
    def get_degree(self, cell):
        """Degree: số ô chưa gán cùng run với cell."""
        neighbors = set()
        for run in self.cell_to_runs[cell]:
            for c in run.cells:
                if c is not cell and c.value == 0:
                    neighbors.add(c)
        return len(neighbors)

    def select_unassigned_variable(self):
        unassigned = [c for c in self.board.white_cells if c.value == 0]
        if not unassigned:
            return None
        if self.var_heuristic == "mrv":
            return min(unassigned, key=lambda c: len(c.domain))
        if self.var_heuristic == "degree":
            return max(unassigned, key=self.get_degree)
        if self.var_heuristic == "mrv_degree":
            smallest = min(len(c.domain) for c in unassigned)
            candidates = [c for c in unassigned if len(c.domain) == smallest]
            return max(candidates, key=self.get_degree)
        return unassigned[0]

    # ---------- heuristic chọn giá trị ----------
    def order_domain_values(self, cell):
        """LCV: thử trước giá trị làm mất ít lựa chọn của các ô cùng run nhất."""
        if self.val_heuristic != "lcv":
            return sorted(cell.domain)

        def eliminated(val):
            count = 0
            for run in self.cell_to_runs[cell]:
                for c in run.cells:
                    if c is not cell and c.value == 0 and val in c.domain:
                        count += 1
            return count

        return sorted(cell.domain, key=lambda v: (eliminated(v), v))

    # ---------- backtracking ----------
    def _restore(self, saved_domains, saved_values):
        for c in self.board.white_cells:
            c.domain = saved_domains[c].copy()
            c.value = saved_values[c]

    def _backtrack(self, depth):
        if self.use_propagation and not self.constraint_propagation():
            return False

        cell = self.select_unassigned_variable()
        if cell is None:
            return Validator.is_board_valid(self.board)

        saved_domains = {c: c.domain.copy() for c in self.board.white_cells}
        saved_values = {c: c.value for c in self.board.white_cells}

        for val in self.order_domain_values(cell):
            if self.max_assignments is not None and self.assignments >= self.max_assignments:
                raise SearchLimitReached()
            cell.value = val
            self.assignments += 1
            self._emit(EventType.ASSIGN, cell=(cell.row, cell.col), value=val, depth=depth)

            # Chỉ cần kiểm tra các run chứa ô vừa gán
            if all(Validator.is_run_valid(run) for run in self.cell_to_runs[cell]):
                if self._backtrack(depth + 1):
                    return True

            self._restore(saved_domains, saved_values)
            self.backtracks += 1
            self._emit(EventType.BACKTRACK, cell=(cell.row, cell.col), value=val, depth=depth)

        self._restore(saved_domains, saved_values)
        return False

    def solve(self):
        """Giải bảng. Có thể gọi lại nhiều lần: mỗi lần đều reset thống kê và trạng thái ban đầu."""
        self.assignments = 0
        self.backtracks = 0
        self.domain_updates = 0
        self.hit_limit = False
        initial_domains = {c: c.domain.copy() for c in self.board.white_cells}
        initial_values = {c: c.value for c in self.board.white_cells}

        self._emit(EventType.INIT,
                   rows=self.board.rows, cols=self.board.cols,
                   domains={(c.row, c.col): sorted(c.domain) for c in self.board.white_cells},
                   config=self.get_config())

        start = time.perf_counter()
        try:
            success = self._backtrack(0)
        except SearchLimitReached:
            success = False
            self.hit_limit = True
        self.execution_time = time.perf_counter() - start

        if success:
            self._emit(EventType.SOLVED, stats=self.get_stats(),
                       solution={(c.row, c.col): c.value for c in self.board.white_cells})
        else:
            self._restore(initial_domains, initial_values)
            self._emit(EventType.FAILED, stats=self.get_stats(),
                       reason="limit" if self.hit_limit else "no_solution")
        return success

    # ---------- thống kê ----------
    def get_config(self):
        return {"var": self.var_heuristic, "val": self.val_heuristic,
                "propagation": self.use_propagation}

    def get_stats(self):
        return {"assignments": self.assignments, "backtracks": self.backtracks,
                "domain_updates": self.domain_updates,
                "execution_time": self.execution_time, "hit_limit": self.hit_limit}
