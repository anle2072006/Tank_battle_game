class Validator:
    @staticmethod
    def is_run_valid(run):
        values = [cell.value for cell in run.cells if cell.value != 0]
        if len(values) != len(set(values)):
            return False
        if len(values) == len(run.cells):
            if sum(values) != run.target_sum:
                return False
        else:
            if sum(values) > run.target_sum:
                return False
        return True

    @staticmethod
    def is_board_valid(board):
        for run in board.runs:
            if not Validator.is_run_valid(run):
                return False
        return True