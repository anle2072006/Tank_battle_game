# Task 3 – Kakuro (Constraint Satisfaction Problem)

Solve Kakuro puzzles using Constraint Propagation, Backtracking Search, and CSP heuristics. Includes an interactive GUI for visualizing the solving process.

## Requirements

- Python 3.9+
- Tkinter (for GUI)
- Packages listed in `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

On Arch Linux, install Tkinter if needed:

```bash
sudo pacman -S tk
```

## Structure

```text
task3_kakuro/
├── board.py           # Board, cells, runs, and domains
├── combos.py          # Valid digit combinations
├── solver.py          # Constraint propagation and backtracking
├── validator.py       # Constraint validation
├── events.py          # Solver events for visualization
├── puzzles.py         # Sample 5x5 and 9x9 puzzles
├── experiments.py     # Heuristic comparison and testing
├── main.py            # Console demo and experiments
├── gui.py             # Interactive Kakuro visualizer
├── notebook.ipynb     # Jupyter notebook
├── requirements.txt   # Python dependencies
└── README.md
```

## Usage

Run all solver demonstrations and experiments:

```bash
python main.py
```

Launch the graphical interface:

```bash
python gui.py
```

### GUI Controls

| Control     | Description                         |
| ----------- | ----------------------------------- |
| Puzzle Size | Switch between 5x5 and 9x9 puzzles  |
| Solve       | Run the solver and record its steps |
| Next        | Move to the next solving step       |
| Back        | Return to the previous step         |
| Result      | Jump directly to the final result   |

### Visualization

The GUI visualizes the following solver events:

| Event         | Description                           |
| ------------- | ------------------------------------- |
| INIT          | Initialize cell domains               |
| DOMAIN_UPDATE | Reduce a cell's domain (yellow)       |
| ASSIGN        | Assign a value to a cell (green)      |
| BACKTRACK     | Restore a previous search state (red) |
| SOLVED        | Display the completed solution        |
| FAILED        | Report an unsuccessful solve          |

The GUI also displays domain values, removed candidates, and solver statistics.

## Algorithms

The solver models Kakuro as a Constraint Satisfaction Problem (CSP):

- **Variables:** White cells in the puzzle.
- **Domains:** Digits from 1 to 9.
- **Constraints:** Each run must match its target sum without repeated digits.
- **Constraint Propagation:** Removes values inconsistent with valid run combinations.
- **Backtracking Search:** Explores assignments and restores previous states when necessary.
- **Heuristics:** Supports MRV, Degree, MRV + Degree, and LCV.

## Experiments

Run:

```bash
python main.py
```

The experiments evaluate:

- Solver correctness on 5x5 and 9x9 puzzles.
- Search performance with different heuristics.
- Performance with and without constraint propagation.
- Solver stability across repeated runs.
- Unsolvable puzzles and puzzles with multiple solutions.

## Notes

The GUI uses the existing `KakuroSolver` and `EventEmitter` without modifying the core solving algorithm. Solving events are recorded and replayed using the Next, Back, and Result controls.
