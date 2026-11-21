class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col

class WhiteCell(Cell):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.value = 0  # 0 nghĩa là chưa điền
        self.domain = set(range(1, 10))

    def reset_domain(self):
        self.domain = set(range(1, 10))

class ClueCell(Cell):
    def __init__(self, row, col, row_sum=None, col_sum=None):
        super().__init__(row, col)
        self.row_sum = row_sum  # Tổng ngang bên phải
        self.col_sum = col_sum  # Tổng dọc bên dưới

class Run:
    def __init__(self, target_sum, cells, direction):
        self.target_sum = target_sum
        self.cells = cells
        self.direction = direction  # 'H' hoặc 'V'

class Board:
    def __init__(self, grid_data):
        self.rows = len(grid_data)
        self.cols = len(grid_data[0])
        self.grid = []
        self.white_cells = []
        self.runs = []
        
        self._init_board(grid_data)
        self._extract_runs()

    def _init_board(self, grid_data):
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                val = grid_data[r][c]
                if val == 0:
                    cell = WhiteCell(r, c)
                    self.white_cells.append(cell)
                    row_cells.append(cell)
                else:
                    # Ô xám trống dùng (None, None), ô clue dùng (row_sum, col_sum)
                    if isinstance(val, tuple):
                        row_sum, col_sum = val
                    else:
                        row_sum, col_sum = None, None
                    cell = ClueCell(r, c, row_sum, col_sum)
                    row_cells.append(cell)
            self.grid.append(row_cells)

    def _extract_runs(self):
        # Trích xuất run ngang (Horizontal runs)
        for r in range(self.rows):
            c = 0
            while c < self.cols:
                if isinstance(self.grid[r][c], ClueCell):
                    if self.grid[r][c].row_sum is not None:
                        target = self.grid[r][c].row_sum
                        run_cells = []
                        nc = c + 1
                        while nc < self.cols and isinstance(self.grid[r][nc], WhiteCell):
                            run_cells.append(self.grid[r][nc])
                            nc += 1
                        if run_cells:
                            self.runs.append(Run(target, run_cells, 'H'))
                c += 1

        # Trích xuất run dọc (Vertical runs)
        for c in range(self.cols):
            r = 0
            while r < self.rows:
                if isinstance(self.grid[r][c], ClueCell):
                    if self.grid[r][c].col_sum is not None:
                        target = self.grid[r][c].col_sum
                        run_cells = []
                        nr = r + 1
                        while nr < self.rows and isinstance(self.grid[nr][c], WhiteCell):
                            run_cells.append(self.grid[nr][c])
                            nr += 1
                        if run_cells:
                            self.runs.append(Run(target, run_cells, 'V'))
                r += 1

    def print_structure_stats(self):
        num_white = len(self.white_cells)
        num_runs = len(self.runs)
        total_row_sum = sum(run.target_sum for run in self.runs if run.direction == 'H')
        total_col_sum = sum(run.target_sum for run in self.runs if run.direction == 'V')
        print(f"Số ô trắng: {num_white}")
        print(f"Số run: {num_runs}")
        print(f"Tổng ngang: {total_row_sum}")
        print(f"Tổng dọc: {total_col_sum}")
        return num_white, num_runs, total_row_sum, total_col_sum

    def display(self):
        for r in range(self.rows):
            row_str = []
            for c in range(self.cols):
                cell = self.grid[r][c]
                if isinstance(cell, ClueCell):
                    rs = f"{cell.row_sum}" if cell.row_sum is not None else ""
                    cs = f"{cell.col_sum}" if cell.col_sum is not None else ""
                    row_str.append(f"[{rs}\\{cs}]")
                else:
                    val = cell.value if cell.value != 0 else "."
                    row_str.append(f"  {val}  ")
            print(" ".join(row_str))