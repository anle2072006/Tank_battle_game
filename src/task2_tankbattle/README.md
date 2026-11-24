# Task 2 - Tank Battle (Adversarial Search)

Turn-based Tank Battle modeled as a two-player zero-sum game, applying Minimax, Alpha-Beta Pruning, and Heuristic Evaluation, with a PyGame GUI supporting external agent integration.

## Requirements

- Python 3.9+
- Packages listed in `requirements.txt`

Install dependencies:

    pip install -r requirements.txt

## Structure

    task2_tankbattle/
    - engine.py            Entities (Tank, Base, Bullet), GameState, and Action set
    - agents.py            BaseAgent and SearchAgent (Minimax, Alpha-Beta, Heuristic)
    - scenarios.py         MapBuilder for Endgame, Midgame, and Battle City maps
    - gui.py               PyGame GUI and external agent loader
    - test_agent.py        Sample ExternalAgent for integration testing
    - experiments.ipynb    Benchmarking notebook and full-match tournament simulation
    - task2_benchmark.png  Execution time and explored states vs. search depth plot
    - report_task2.tex     LaTeX report section for Task 2
    - requirements.txt     Python dependencies
    - README.md            Usage instructions

## Usage

### 1. Run the PyGame GUI

Navigate to `task2_tankbattle` and run:

    python gui.py

GUI controls:
- AI SELECTION: Choose an algorithm for Player 1 (Green) and Player 2 (Red): Minimax, Alpha-Beta, Heuristic Minimax, Heuristic + Alpha-Beta, or "Import External Agent..." to load an external Python file.
- MAP SELECTION: Switch between Endgame, Midgame, and Battle City maps.
- SPACE: Start or pause auto-play.
- N: Step forward one turn manually (while paused).
- R: Reset the current map to its initial state.

### 2. Re-run Experiments and Plots

Open `experiments.ipynb` in VS Code or Jupyter Notebook and run **Restart & Run All** to:
1. Measure explored states and average execution time of all 4 configurations at depths d = 2, 3, 4, 5 on Endgame and Mid-game scenarios.
2. Generate the log-scale comparison chart (`task2_benchmark.png`).
3. Simulate full head-to-head matches across algorithm configurations.

## External Agent Integration

To compete with an external algorithm in the same environment, create a `.py` file defining an `ExternalAgent` class (see `test_agent.py`):

    from engine import Action

    class ExternalAgent:
        def __init__(self, player_id: int):
            self.player_id = player_id
            self.nodes_explored = 0
            self.last_exec_time = 0.0

        def get_action(self, state) -> Action:
            legal_actions = state.get_legal_actions()
            return legal_actions[0]

Launch `gui.py`, select **"Import External Agent..."** for Player 1 or Player 2, and choose the `.py` file.