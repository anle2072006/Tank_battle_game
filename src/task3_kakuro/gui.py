
import tkinter as tk
from collections import Counter

from board import Board, WhiteCell, ClueCell
from solver import KakuroSolver
from events import EventEmitter
from puzzles import SAMPLE_5X5, SAMPLE_9X9


class KakuroGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kakuro - CSP Visualizer")

        self.board = Board(SAMPLE_5X5)
        self.puzzle_var = tk.StringVar(value="5x5")
        self.events = []
        self.snapshots = []
        self.step_index = -1
        self.playback_values = {}
        self.playback_domains = {}
        self.playback_mode = False

        self.title = tk.Label(
            root, text="KAKURO SOLVER",
            font=("Arial", 20, "bold")
        )
        self.title.pack(pady=10)

        self.puzzle_frame = tk.Frame(root)
        self.puzzle_frame.pack(pady=5)

        tk.Label(
            self.puzzle_frame,
            text="Puzzle size:"
        ).pack(side="left", padx=5)

        self.puzzle_select = tk.OptionMenu(
            self.puzzle_frame,
            self.puzzle_var,
            "5x5",
            "9x9",
            command=self.change_puzzle
        )
        self.puzzle_select.pack(side="left")

        self.grid_frame = tk.Frame(root)
        self.grid_frame.pack(padx=20, pady=10)

        self.draw_board()

        self.solve_button = tk.Button(
            root, text="Solve", command=self.solve,
            font=("Arial", 12)
        )
        self.solve_button.pack(pady=10)
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=5)

        self.back_button = tk.Button(
            self.control_frame,
            text="◀ Back",
            command=self.previous_step
        )
        self.back_button.pack(side="left", padx=5)

        self.next_button = tk.Button(
            self.control_frame,
            text="Next ▶",
            command=self.next_step
        )
        self.next_button.pack(side="left", padx=5)

        self.result_button = tk.Button(
            self.control_frame,
            text="⏭ Result",
            command=self.show_result
        )
        self.result_button.pack(side="left", padx=5)

        self.step_label = tk.Label(
            root,
            text="Step 0/0"
        )
        self.step_label.pack(pady=5)
        self.event_detail = tk.Label(
            root,
            text="",
            font=("Arial", 10),
            justify="center",
            wraplength=350
        )
        self.event_detail.pack(pady=5)

        self.status = tk.Label(
            root, text="Ready", font=("Arial", 11)
        )
        self.status.pack(pady=10)


    def change_puzzle(self, selection):
        puzzle = SAMPLE_5X5 if selection == "5x5" else SAMPLE_9X9

        self.board = Board(puzzle)

        self.events = []
        self.snapshots = []
        self.step_index = -1

        self.playback_mode = False
        self.playback_values = {}
        self.playback_domains = {}

        self.active_cell = None
        self.active_event = None

        self.step_label.config(text="Step 0/0")
        self.event_detail.config(text="")
        self.status.config(text="Ready")

        self.draw_board()

    def draw_board(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.grid[r][c]

                bg = "#444444"
                fg = "white"
                font_size = 12
                text = ""

                if isinstance(cell, WhiteCell):
                    bg = "white"
                    fg = "black"
                    pos = (r, c)

                    if self.playback_mode:
                        value = self.playback_values.get(pos, 0)
                        domain = self.playback_domains.get(
                            pos, set(range(1, 10))
                        )

                        if value:
                            text = str(value)
                        else:
                            digits = sorted(domain)
                            text = "\n".join(
                                " ".join(map(str, digits[i:i + 3]))
                                for i in range(0, len(digits), 3)
                            )
                            fg = "#64748B"
                            font_size = 8

                        if pos == getattr(self, "active_cell", None):
                            event = getattr(self, "active_event", None)

                            if event == "ASSIGN":
                                bg = "#BBF7D0"
                            elif event == "DOMAIN_UPDATE":
                                bg = "#FEF08A"
                            elif event == "BACKTRACK":
                                bg = "#FECACA"
                    else:
                        text = str(cell.value) if cell.value else ""

                elif isinstance(cell, ClueCell):
                    horizontal = cell.row_sum or ""
                    vertical = cell.col_sum or ""
                    text = f"{horizontal}\n{vertical}"

                tk.Label(
                    self.grid_frame,
                    text=text,
                    width=6 if self.board.rows == 9 else 7,
                    height=3,
                    bg=bg,
                    fg=fg,
                    relief="solid",
                    borderwidth=1,
                    font=("Arial", font_size),
                    justify="center"
                ).grid(row=r, column=c)




    def on_event(self, event_type, data):
      self.events.append((event_type, data.copy()))

      values = {
          (cell.row, cell.col): cell.value
          for cell in self.board.white_cells
      }

      domains = {
          (cell.row, cell.col): cell.domain.copy()
          for cell in self.board.white_cells
      }

      self.snapshots.append({
          "event": event_type,
          "data": data.copy(),
          "values": values,
          "domains": domains
      })


    def solve(self):
        puzzle = (
            SAMPLE_5X5
            if self.puzzle_var.get() == "5x5"
            else SAMPLE_9X9
        )

        self.board = Board(puzzle)
        self.events = []
        self.snapshots = []
        self.playback_mode = False
        self.active_cell = None
        self.active_event = None

        bus = EventEmitter()
        bus.subscribe(self.on_event)

        try:
            solver = KakuroSolver(self.board, event_bus=bus)
            success = solver.solve()
        finally:
            bus.unsubscribe(self.on_event)
        self.step_index = -1
        self.playback_mode = True

        
        self.playback_values = {
            (c.row, c.col): 0
            for c in self.board.white_cells
        }

        self.playback_domains = {
            (c.row, c.col): set(range(1, 10))
            for c in self.board.white_cells
        }

        self.step_label.config(
            text=f"Step 0/{len(self.snapshots)}"
        )

        self.event_detail.config(
            text="Press Next to replay solver events"
        )

        self.draw_board()


        counts = Counter(
            event_type for event_type, _ in self.events
        )

        if success:
            stats = solver.get_stats()

            self.status.config(
                text=(
                    f"Solved successfully!\n"
                    f"Assignments: {stats['assignments']} | "
                    f"Backtracks: {stats['backtracks']}\n"
                    f"Domain updates: {stats['domain_updates']}"
                )
            )
        else:
            self.status.config(text="No solution found")

        print("Events:", dict(counts))


    def show_result(self):
        if not self.snapshots:
            self.status.config(
                text="Please press Solve first!"
            )
            return

        self.step_index = len(self.snapshots) - 1
        self.show_step()

    def next_step(self):
        if self.step_index < len(self.snapshots) - 1:
            self.step_index += 1
            self.show_step()


    def previous_step(self):
        if self.step_index > 0:
            self.step_index -= 1
            self.show_step()


    def show_step(self):
        snapshot = self.snapshots[self.step_index]

        self.playback_values = snapshot["values"].copy()
        self.playback_domains = {
            pos: domain.copy()
            for pos, domain in snapshot["domains"].items()
        }

        event_type = snapshot["event"]
        data = snapshot["data"]

        self.active_cell = data.get("cell")
        self.active_event = event_type

        self.step_label.config(
            text=(
                f"Step {self.step_index + 1}/"
                f"{len(self.snapshots)} — {event_type}"
            )
        )

        if event_type == "DOMAIN_UPDATE":
            old_domain = set(data["old"])
            new_domain = set(data["new"])
            removed = sorted(old_domain - new_domain)

            message = (
                f"Cell: {data['cell']}\n"
                f"Before: {sorted(old_domain)}\n"
                f"After: {sorted(new_domain)}\n"
                f"Removed: {removed}"
            )

        elif event_type == "ASSIGN":
            message = (
                f"Assign {data['value']} "
                f"to cell {data['cell']}"
            )

        elif event_type == "BACKTRACK":
            message = (
                f"Backtrack at {data['cell']}\n"
                f"Rejected value: {data['value']}"
            )

        elif event_type == "SOLVED":
            message = "Solution found!"

        elif event_type == "INIT":
            message = "Initializing domains..."

        else:
            message = "Solver failed."

        self.event_detail.config(text=message)

        self.draw_board()



if __name__ == "__main__":
    root = tk.Tk()
    app = KakuroGUI(root)
    root.mainloop()
