class Validator:
    """Kiểm tra tính hợp lệ của trạng thái bảng và các run."""
    @staticmethod
    def is_run_valid(run):
        values = [cell.value for cell in run.cells if cell.value != 0]
        # Không được chứa chữ số trùng lặp
        if len(values) != len(set(values)):
            return False
        if len(values) == len(run.cells):
            if sum(values) != run.target_sum: # Nếu điền đầy đủ, tổng phải bằng target_sum
                return False
        else:
            if sum(values) > run.target_sum:
                return False
        return True # Nếu chưa điền đầy đủ, tổng hiện tại không được vượt quá target_sum

    @staticmethod
    def is_board_valid(board):
        for run in board.runs:
            if not Validator.is_run_valid(run):
                return False
        return True