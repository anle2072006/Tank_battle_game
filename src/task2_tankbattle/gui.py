import pygame
import importlib.util
import subprocess
import sys

from pathlib import Path
from uuid import uuid4
from engine import Action
from agents import SearchAgent
from scenarios import MapBuilder


CELL_SIZE = 48
MIN_BOARD_WIDTH = 432
MIN_CONTENT_HEIGHT = 432
PANEL_HEIGHT = 125
SIDEBAR_WIDTH = 240
FPS = 60

COLORS = {
    "background": (25, 29, 39),
    "grid": (65, 70, 82),
    "wall": (155, 92, 58),
    "tank1": (65, 190, 110),
    "tank2": (235, 90, 90),
    "base1": (60, 150, 220),
    "base2": (230, 180, 60),
    "bullet": (255, 245, 150),
    "text": (245, 245, 245),
}

DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
}

MAP_MODES = {
    1: ("Endgame", MapBuilder.get_endgame_scenario),
    2: ("Midgame", MapBuilder.get_midgame_scenario),
    3: ("Battle City", MapBuilder.get_battle_city_map),
}

AI_MODES = {
    1: ("Minimax", False, False),
    2: ("Alpha-Beta", False, True),
    3: ("Heuristic Minimax", True, False),
    4: ("Heuristic + Alpha-Beta", True, True),
    5: ("Import External Agent...", None, None),
}


class Dropdown:
    def __init__(
        self, x, y, width, options,
        selected=3, open_up=False
    ):
        self.rect = pygame.Rect(x, y, width, 32)
        self.options = options
        self.selected = selected
        self.custom_label = None
        self.expanded = False
        self.open_up = open_up

        self.hover_main = 0.0
        self.hover_items = [0.0] * len(options)

    def option_rect(self, index):
        if self.open_up:
            y = self.rect.y - (
                len(self.options) - index
            ) * 32
        else:
            y = self.rect.bottom + index * 32

        return pygame.Rect(
            self.rect.x, y, self.rect.width, 32
        )

    def _fit_text(self, text_str, font, max_width):
        display = str(text_str)
        while display and font.size(display)[0] > max_width:
            display = display[:-1]
        if display != str(text_str):
            display = display[:-3] + "..." if len(display) > 3 else "..."
        return display

    def draw(self, screen, font):
        mouse = pygame.mouse.get_pos()

        target = 1.0 if self.rect.collidepoint(mouse) else 0.0
        self.hover_main += (target - self.hover_main) * 0.18

        bg = pygame.Color(55, 65, 80).lerp(
            pygame.Color(75, 105, 145),
            self.hover_main
        )

        pygame.draw.rect(
            screen, bg, self.rect, border_radius=5
        )
        pygame.draw.rect(
            screen, (120, 145, 175),
            self.rect, 1, border_radius=5
        )

        raw_label = self.custom_label if self.custom_label else self.options[self.selected]
        label = self._fit_text(raw_label, font, self.rect.width - 28)
        text = font.render(label, True, "white")
        screen.blit(text, (self.rect.x + 8, self.rect.y + 7))

        arrow = "^" if self.open_up else "v"
        arrow_text = font.render(arrow, True, "white")
        screen.blit(
            arrow_text,
            (self.rect.right - 18, self.rect.y + 7)
        )

        if not self.expanded:
            return

        for i, option in enumerate(self.options):
            rect = self.option_rect(i)

            target = 1.0 if rect.collidepoint(mouse) else 0.0
            self.hover_items[i] += (
                target - self.hover_items[i]
            ) * 0.18

            color = pygame.Color(40, 48, 62).lerp(
                pygame.Color(65, 105, 150),
                self.hover_items[i]
            )

            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(
                screen, (95, 115, 145), rect, 1
            )

            text = font.render(option, True, "white")
            screen.blit(text, (rect.x + 8, rect.y + 7))

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.expanded = not self.expanded
            return None

        if self.expanded:
            for i in range(len(self.options)):
                if self.option_rect(i).collidepoint(pos):
                    self.selected = i
                    self.expanded = False
                    return i + 1

        self.expanded = False
        return None


class TankBattleGUI:
    def _compute_cell_size(self):
        return min(CELL_SIZE, 540 // self.state.height)

    def _compute_layout(self):
        self.cell_size = self._compute_cell_size()
        actual_w = self.state.width * self.cell_size
        actual_h = self.state.height * self.cell_size

        self.board_width = max(actual_w, MIN_BOARD_WIDTH)
        self.content_height = max(actual_h, MIN_CONTENT_HEIGHT)
        self.board_offset_x = (self.board_width - actual_w) // 2
        self.board_offset_y = (self.content_height - actual_h) // 2

        self.width = self.board_width + SIDEBAR_WIDTH
        self.height = self.content_height + PANEL_HEIGHT

    def __init__(self):
        pygame.init()

        self.map_mode = 2
        self.state = MAP_MODES[self.map_mode][1]()
        self._compute_layout()

        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )
        pygame.display.set_caption("Tank Battle - AI Arena")

        self.font = pygame.font.SysFont("Arial", 18)
        self.dropdown_font = pygame.font.SysFont("Arial", 12)
        self.panel_title_font = pygame.font.SysFont("Arial", 13, bold=True)
        self.panel_body_font = pygame.font.SysFont("Arial", 12)

        options = [
            AI_MODES[i][0]
            for i in range(1, 6)
        ]

        sidebar_x = self.board_width + 25

        self.dropdown_p1 = Dropdown(
            sidebar_x, 91, 190, options,
            selected=3,
            open_up=False
        )

        self.dropdown_p2 = Dropdown(
            sidebar_x, 178, 190, options,
            selected=3,
            open_up=False
        )

        map_options = [
            MAP_MODES[i][0]
            for i in range(1, 4)
        ]

        self.dropdown_map = Dropdown(
            self.board_width + 25,
            268,
            190,
            map_options,
            selected=1,
            open_up=False
        )

        self.clock = pygame.time.Clock()

        self.agent_modes = {
            1: 4,
            2: 4
        }

        self.agent_labels = {
            1: "Heuristic + Alpha-Beta",
            2: "Heuristic + Alpha-Beta"
        }

        self.agents = {
            1: self.create_agent(1, 4),
            2: self.create_agent(2, 4)
        }

        self.last_action = "Press SPACE to start"
        self.running = True
        self.auto_play = False
        self.turn_delay = 500  # 500 ms giữa các lượt
        self.last_turn_time = pygame.time.get_ticks()

    def choose_agent_file(self):
        if sys.platform == "darwin":
            applescript = (
                'POSIX path of (choose file with prompt '
                '"Select External AI Agent (.py)")'
            )
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            if "-128" in result.stderr or "User canceled" in result.stderr:
                return ""
            raise RuntimeError("File picker failed:\n" + result.stderr)
        script = """
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.title("External Agent File Picker")
root.geometry("360x100")
root.attributes("-topmost", True)

label = tk.Label(
    root,
    text="Select a Python AI Agent file..."
)
label.pack(pady=20)

root.lift()
root.focus_force()
root.update()

filename = filedialog.askopenfilename(
    parent=root,
    title="Select External AI Agent",
    filetypes=[
        ("Python files", "*.py"),
        ("All files", "*.*")
    ]
)

print(filename, flush=True)
root.destroy()
"""

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            raise RuntimeError(
                "File picker failed:\n" + result.stderr
            )

        return result.stdout.strip()

    def load_external_agent(self, player_id):
        file_path = self.choose_agent_file()

        if not file_path:
            return None
        
        path = Path(file_path).resolve()
        if path.suffix != ".py":
            raise ValueError("Selected file must be a .py file")

        gui_dir = str(Path(__file__).resolve().parent)
        if gui_dir not in sys.path:
            sys.path.insert(0, gui_dir)
        parent_dir = str(path.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        module_name = f"external_agent_{uuid4().hex}"

        spec = importlib.util.spec_from_file_location(
            module_name, str(path)
        )

        if spec is None or spec.loader is None:
            raise ImportError("Cannot load Python file")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        agent_class = getattr(
            module, "ExternalAgent", None
        )

        if not isinstance(agent_class, type):
            raise TypeError(
                "File must define class ExternalAgent"
            )

        agent = agent_class(player_id=player_id)

        if not callable(getattr(agent, "get_action", None)):
            raise TypeError(
                "Agent must implement get_action(state)"
            )

        return agent, path.stem

    def create_agent(self, player_id, mode):
        name, heuristic, alpha_beta = AI_MODES[mode]

        return SearchAgent(
            player_id=player_id,
            max_depth=4,
            use_heuristic=heuristic,
            use_alpha_beta=alpha_beta
        )

    def change_agent(self, player_id, mode):
        dropdown = self.dropdown_p1 if player_id == 1 else self.dropdown_p2

        if mode == 5:
            try:
                result = self.load_external_agent(player_id)
            except Exception as exc:
                import traceback

                traceback.print_exc()
                result = None
                self.last_action = f"Import error: {type(exc).__name__}"

            if result is None:
                dropdown.selected = self.agent_modes[player_id] - 1
                dropdown.custom_label = (
                    self.agent_labels[player_id]
                    if self.agent_modes[player_id] == 5
                    else None
                )
                return

            agent, agent_name = result
            label = f"External: {agent_name}"
            dropdown.custom_label = label

        else:
            agent = self.create_agent(player_id, mode)
            label = AI_MODES[mode][0]
            dropdown.custom_label = None

        self.agents[player_id] = agent
        self.agent_modes[player_id] = mode
        self.agent_labels[player_id] = label

        self.reset()
        self.auto_play = False
        self.last_action = f"P{player_id}: {label}"

    def draw_grid(self):
        cs = self.cell_size
        ox, oy = self.board_offset_x, self.board_offset_y
        for y in range(self.state.height):
            for x in range(self.state.width):
                rect = pygame.Rect(ox + x * cs, oy + y * cs, cs, cs)
                pygame.draw.rect(self.screen, COLORS["grid"], rect, 1)

    def draw_entities(self):
        cs = self.cell_size
        ox, oy = self.board_offset_x, self.board_offset_y
        wall_colors = {
            3: COLORS["wall"],
            2: (125, 74, 48),
            1: (95, 58, 40),
        }

        for (x, y), hp in self.state.walls.items():
            rect = pygame.Rect(ox + x * cs + 3, oy + y * cs + 3, cs - 6, cs - 6)
            pygame.draw.rect(self.screen, wall_colors.get(hp, COLORS["wall"]), rect)

        for player_id, base in self.state.bases.items():
            if base.hp <= 0:
                continue
            color = COLORS[f"base{player_id}"]
            center = (ox + base.x * cs + cs // 2, oy + base.y * cs + cs // 2)
            pygame.draw.circle(self.screen, color, center, cs // 3)

        tank_pad = max(6, cs // 6)
        for player_id, tank in self.state.tanks.items():
            if tank.hp <= 0:
                continue
            color = COLORS[f"tank{player_id}"]
            center = pygame.Vector2(ox + tank.x * cs + cs // 2, oy + tank.y * cs + cs // 2)
            pygame.draw.rect(
                self.screen,
                color,
                (ox + tank.x * cs + tank_pad, oy + tank.y * cs + tank_pad, cs - 2 * tank_pad, cs - 2 * tank_pad),
                border_radius=5
            )
            dx, dy = DIRECTIONS[tank.direction]
            end = center + pygame.Vector2(dx, dy) * (cs // 2)
            pygame.draw.line(self.screen, (255, 255, 255), center, end, max(3, cs // 10))

        bullet_radius = max(4, cs // 9)
        for bullet in self.state.bullets:
            center = (ox + bullet.x * cs + cs // 2, oy + bullet.y * cs + cs // 2)
            pygame.draw.circle(self.screen, COLORS["bullet"], center, bullet_radius)

    def draw_sidebar(self):
        x = self.board_width
        h = self.content_height

        pygame.draw.rect(
            self.screen,
            (30, 36, 48),
            (x, 0, SIDEBAR_WIDTH, h)
        )

        # AI Selection
        ai_rect = pygame.Rect(x + 12, 12, 216, 222)
        pygame.draw.rect(
            self.screen, (35, 45, 60),
            ai_rect, border_radius=8
        )

        title = self.font.render(
            "AI SELECTION", True, COLORS["text"]
        )
        self.screen.blit(title, (x + 24, 24))

        # Player cards
        cards = [
            (59, "PLAYER 1 - GREEN", COLORS["tank1"]),
            (146, "PLAYER 2 - RED", COLORS["tank2"])
        ]

        for y, label, color in cards:
            rect = pygame.Rect(x + 18, y, 204, 76)

            pygame.draw.rect(
                self.screen, (42, 50, 65),
                rect, border_radius=7
            )
            pygame.draw.rect(
                self.screen, color,
                rect, 1, border_radius=7
            )

            text = self.dropdown_font.render(
                label, True, color
            )
            self.screen.blit(text, (rect.x + 12, rect.y + 9))

        # Map Selection
        map_rect = pygame.Rect(
            x + 18, 240, 204, 68
        )

        pygame.draw.rect(
            self.screen,
            (42, 50, 65),
            map_rect,
            border_radius=7
        )

        pygame.draw.rect(
            self.screen,
            (90, 160, 220),
            map_rect,
            1,
            border_radius=7
        )

        map_title = self.dropdown_font.render(
            "MAP SELECTION",
            True,
            (130, 195, 245)
        )

        self.screen.blit(
            map_title,
            (x + 30, 249)
        )

        # Controls fills remaining space
        controls_rect = pygame.Rect(
            x + 12, 318, 216, h - 330
        )

        pygame.draw.rect(
            self.screen, (35, 45, 60),
            controls_rect, border_radius=8
        )

        controls_title = self.font.render(
            "CONTROLS", True, COLORS["text"]
        )
        self.screen.blit(
            controls_title, (x + 24, 328)
        )

        controls = [
            "SPACE : Play / Pause",
            "N     : Next Turn",
            "R     : Reset"
        ]

        for i, line in enumerate(controls):
            text = self.dropdown_font.render(
                line, True, COLORS["text"]
            )
            self.screen.blit(
                text, (x + 24, 359 + i * 23)
            )

        # Draw dropdowns last
        dropdowns = [
            self.dropdown_p1,
            self.dropdown_p2,
            self.dropdown_map
        ]

        # Draw closed dropdowns first
        for dropdown in dropdowns:
            if not dropdown.expanded:
                dropdown.draw(
                    self.screen,
                    self.dropdown_font
                )

        # Draw expanded dropdown on top
        for dropdown in dropdowns:
            if dropdown.expanded:
                dropdown.draw(
                    self.screen,
                    self.dropdown_font
                )

    def draw_panel(self):
        y = self.content_height

        pygame.draw.rect(
            self.screen,
            (20, 26, 38),
            (0, y, self.width, PANEL_HEIGHT)
        )

        margin = 8
        gap = 6
        available = self.width - margin * 2 - gap * 3

        widths = [
            int(available * 0.27),
            int(available * 0.18),
            int(available * 0.18)
        ]
        widths.append(available - sum(widths))

        tank1 = self.state.tanks[1]
        tank2 = self.state.tanks[2]
        base1 = self.state.bases[1]
        base2 = self.state.bases[2]

        if self.state.is_terminal():
            winner = self.get_winner()
            status = f"P{winner} Wins" if winner else "Draw"
        elif self.auto_play:
            status = "Running"
        else:
            status = "Paused"

        cards = [
            (
                "MATCH STATUS",
                [
                    f"Turn: {self.state.turn_count}",
                    f"Current: P{self.state.current_turn}",
                    status
                ],
                (90, 200, 245)
            ),
            (
                "PLAYER 1",
                [
                    f"Tank HP: {tank1.hp}",
                    f"Base HP: {base1.hp}"
                ],
                COLORS["tank1"]
            ),
            (
                "PLAYER 2",
                [
                    f"Tank HP: {tank2.hp}",
                    f"Base HP: {base2.hp}"
                ],
                COLORS["tank2"]
            ),
            (
                "LAST ACTION",
                self.last_action.split(" | ", 1),
                (190, 150, 240)
            )
        ]

        title_font = self.panel_title_font
        body_font = self.panel_body_font

        x = margin

        for index, (title, lines, accent) in enumerate(cards):
            width = widths[index]

            rect = pygame.Rect(
                x, y + 10, width, PANEL_HEIGHT - 20
            )

            pygame.draw.rect(
                self.screen,
                (35, 45, 60),
                rect,
                border_radius=8
            )

            pygame.draw.rect(
                self.screen,
                (75, 100, 135),
                rect,
                1,
                border_radius=8
            )

            heading = title_font.render(title, True, accent)
            self.screen.blit(heading, (x + 8, y + 19))

            for line_index, line in enumerate(lines):
                display = str(line)
                max_width = width - 16

                while (
                    display
                    and body_font.size(display)[0] > max_width
                ):
                    display = display[:-1]

                if display != str(line):
                    display = display[:-3] + "..." if len(display) > 3 else "..."

                surface = body_font.render(
                    display, True, COLORS["text"]
                )

                self.screen.blit(
                    surface,
                    (x + 8, y + 47 + line_index * 21)
                )

            x += width + gap

    def get_winner(self):
        if not self.state.is_terminal():
            return None

        alive = []

        for player_id in (1, 2):
            tank = self.state.tanks[player_id]
            base = self.state.bases[player_id]

            if tank.hp > 0 and base.hp > 0:
                alive.append(player_id)

        if len(alive) == 1:
            return alive[0]

        return None

    def next_turn(self):
        if self.state.is_terminal():
            winner = self.get_winner()

            if winner is not None:
                self.last_action = f"GAME OVER - PLAYER {winner} WINS!"
            else:
                self.last_action = "GAME OVER - DRAW!"

            return

        player = self.state.current_turn
        agent = self.agents[player]

        try:
            action = agent.get_action(self.state.clone())

            if not isinstance(action, Action):
                raise TypeError(
                    "Agent must return an Action enum"
                )

            legal_actions = self.state.get_legal_actions()

            if action not in legal_actions:
                raise ValueError(
                    f"Illegal action: {action.name}"
                )

        except Exception as exc:
            print(f"Player {player} agent error:", exc)
            self.auto_play = False
            self.last_action = f"P{player} agent error - paused"
            return

        self.state = self.state.apply_action(action)

        tank = self.state.tanks[player]
        opponent = self.state.tanks[2 if player == 1 else 1]

        print(
            f"Turn {self.state.turn_count} | "
            f"P{player} | "
            f"Action: {action.name} | "
            f"Pos: ({tank.x}, {tank.y}) | "
            f"Enemy: ({opponent.x}, {opponent.y}) | "
            f"Tank HP: {tank.hp}/{opponent.hp} | "
            f"Bases: {self.state.bases[1].hp}/"
            f"{self.state.bases[2].hp} | "
            f"Walls: {len(self.state.walls)} | "
            f"Nodes: {getattr(agent, 'nodes_explored', 0)}"
        )

        self.last_action = (
            f"Player {player}: {action.name} | "
            f"Nodes: {getattr(agent, 'nodes_explored', 0)}"
        )

        if self.state.is_terminal():
            winner = self.get_winner()

            if winner is not None:
                self.last_action = f"GAME OVER - PLAYER {winner} WINS!"
            else:
                self.last_action = "GAME OVER - DRAW!"

    def change_map(self, mode):
        if mode not in MAP_MODES:
            return

        self.map_mode = mode
        self.auto_play = False
        self.reset()
        self._compute_layout()

        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )

        sidebar_x = self.board_width + 25

        self.dropdown_p1.rect.x = sidebar_x
        self.dropdown_p2.rect.x = sidebar_x
        self.dropdown_map.rect.x = sidebar_x

        self.dropdown_p1.expanded = False
        self.dropdown_p2.expanded = False
        self.dropdown_map.expanded = False

        self.last_action = f"Map: {MAP_MODES[mode][0]}"
        self.last_turn_time = pygame.time.get_ticks()

    def reset(self):
        self.state = MAP_MODES[self.map_mode][1]()
        self.auto_play = False
        self.last_action = "Game reset"
        self.last_turn_time = pygame.time.get_ticks()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.auto_play = not self.auto_play
                        self.last_turn_time = pygame.time.get_ticks()

                    elif event.key == pygame.K_n:
                        if not self.auto_play:
                            self.next_turn()

                    elif event.key == pygame.K_r:
                        self.reset()
                        self.auto_play = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        pos = event.pos
                        dropdowns = [
                            (self.dropdown_p1, 1),
                            (self.dropdown_p2, 2),
                            (self.dropdown_map, 3)
                        ]

                        selected = None
                        toggled_open = None

                        # Uu tien click vao muc con cua menu dang mo
                        for dropdown, kind in dropdowns:
                            if dropdown.expanded:
                                if any(
                                    dropdown.option_rect(i).collidepoint(pos)
                                    for i in range(len(dropdown.options))
                                ):
                                    selected = (kind, dropdown.handle_click(pos))
                                    break

                        # Neu khong click muc con, kiem tra click vao nut dropdown
                        if selected is None:
                            for dropdown, kind in dropdowns:
                                if dropdown.rect.collidepoint(pos):
                                    if not dropdown.expanded:
                                        toggled_open = dropdown
                                    break

                        for dropdown, _ in dropdowns:
                            dropdown.expanded = False

                        if toggled_open is not None:
                            toggled_open.expanded = True
                        elif selected is not None:
                            kind, mode = selected
                            if mode is not None:
                                if kind == 1:
                                    self.change_agent(1, mode)
                                elif kind == 2:
                                    self.change_agent(2, mode)
                                else:
                                    self.change_map(mode)

            if self.auto_play:
                now = pygame.time.get_ticks()

                if self.state.is_terminal():
                    self.auto_play = False

                elif now - self.last_turn_time >= self.turn_delay:
                    self.next_turn()
                    self.last_turn_time = now

                    if self.state.is_terminal():
                        self.auto_play = False
            self.screen.fill(COLORS["background"])

            self.draw_grid()
            self.draw_entities()
            self.draw_panel()
            self.draw_sidebar()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    app = TankBattleGUI()
    app.run()