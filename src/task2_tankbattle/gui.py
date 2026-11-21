
import pygame
import importlib.util
import tkinter as tk
import subprocess
import sys

from tkinter import filedialog
from pathlib import Path
from uuid import uuid4
from engine import Action
from agents import SearchAgent
from scenarios import MapBuilder


CELL_SIZE = 48
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

SIDEBAR_WIDTH = 240



class Dropdown:
    def __init__(
        self, x, y, width, options,
        selected=3, open_up=False
    ):
        self.rect = pygame.Rect(x, y, width, 32)
        self.options = options
        self.selected = selected
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

        label = self.options[self.selected]
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
    def __init__(self):
        pygame.init()

        self.map_mode = 2
        self.state = MAP_MODES[self.map_mode][1]()

        self.board_width = self.state.width * CELL_SIZE
        
        self.content_height = max(
            self.state.height * CELL_SIZE,
            432
        )
        self.width = self.board_width + SIDEBAR_WIDTH
        self.height = self.content_height + PANEL_HEIGHT



        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )
        pygame.display.set_caption("Tank Battle - AI Arena")

        self.font = pygame.font.SysFont("Arial", 18)

        self.dropdown_font = pygame.font.SysFont("Arial", 12)

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
        script = """
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.title("External Agent File Picker")
root.geometry("360x100")

label = tk.Label(
    root,
    text="Select a Python AI Agent file..."
)
label.pack(pady=20)

root.lift()
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
            max_depth=2,
            use_heuristic=heuristic,
            use_alpha_beta=alpha_beta
        )


    def change_agent(self, player_id, mode):
        if mode == 5:
            try:
                result = self.load_external_agent(player_id)
            except Exception as exc:
                import traceback

                traceback.print_exc()
                result = None
                self.last_action = f"Import error: {type(exc).__name__}"

            if result is None:
                dropdown = (
                    self.dropdown_p1 if player_id == 1
                    else self.dropdown_p2
                )
                dropdown.selected = self.agent_modes[player_id] - 1
                return

            agent, agent_name = result
            label = f"External: {agent_name}"

        else:
            agent = self.create_agent(player_id, mode)
            label = AI_MODES[mode][0]

        self.agents[player_id] = agent
        self.agent_modes[player_id] = mode
        self.agent_labels[player_id] = label

        self.reset()
        self.auto_play = False
        self.last_action = f"P{player_id}: {label}"


    def draw_grid(self):
        for y in range(self.state.height):
            for x in range(self.state.width):
                rect = pygame.Rect(
                    x * CELL_SIZE,
                    y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )

                pygame.draw.rect(
                    self.screen, COLORS["grid"], rect, 1
                )

    def draw_entities(self):
        for (x, y), hp in self.state.walls.items():
            rect = pygame.Rect(
                x * CELL_SIZE + 3,
                y * CELL_SIZE + 3,
                CELL_SIZE - 6,
                CELL_SIZE - 6
            )
            pygame.draw.rect(
                self.screen, COLORS["wall"], rect
            )

        for player_id, base in self.state.bases.items():
            if base.hp <= 0:
                continue

            color = COLORS[f"base{player_id}"]
            center = (
                base.x * CELL_SIZE + CELL_SIZE // 2,
                base.y * CELL_SIZE + CELL_SIZE // 2
            )
            pygame.draw.circle(
                self.screen, color, center, CELL_SIZE // 3
            )

        for player_id, tank in self.state.tanks.items():
            if tank.hp <= 0:
                continue

            color = COLORS[f"tank{player_id}"]
            center = pygame.Vector2(
                tank.x * CELL_SIZE + CELL_SIZE // 2,
                tank.y * CELL_SIZE + CELL_SIZE // 2
            )

            pygame.draw.rect(
                self.screen,
                color,
                (
                    tank.x * CELL_SIZE + 8,
                    tank.y * CELL_SIZE + 8,
                    CELL_SIZE - 16,
                    CELL_SIZE - 16
                ),
                border_radius=5
            )

            dx, dy = DIRECTIONS[tank.direction]
            end = center + pygame.Vector2(
                dx, dy
            ) * (CELL_SIZE // 2)

            pygame.draw.line(
                self.screen, (255, 255, 255),
                center, end, 5
            )

        for bullet in self.state.bullets:
            center = (
                bullet.x * CELL_SIZE + CELL_SIZE // 2,
                bullet.y * CELL_SIZE + CELL_SIZE // 2
            )
            pygame.draw.circle(
                self.screen, COLORS["bullet"], center, 5
            )


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

        title_font = pygame.font.SysFont("Arial", 13, bold=True)
        body_font = pygame.font.SysFont("Arial", 12)

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

        self.board_width = self.state.width * CELL_SIZE
        self.content_height = max(
            self.state.height * CELL_SIZE, 432
        )

        self.width = self.board_width + SIDEBAR_WIDTH
        self.height = self.content_height + PANEL_HEIGHT

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

                        # Click vào menu đang mở được ưu tiên
                        # trước các dropdown khác.
                        for dropdown, kind in dropdowns:
                            if dropdown.expanded:
                                if any(
                                    dropdown.option_rect(i).collidepoint(pos)
                                    for i in range(len(dropdown.options))
                                ):
                                    selected = (
                                        kind,
                                        dropdown.handle_click(pos)
                                    )
                                    break

                        if selected is None:
                            for dropdown, kind in dropdowns:
                                if dropdown.rect.collidepoint(pos):
                                    selected = (
                                        kind,
                                        dropdown.handle_click(pos)
                                    )
                                    break

                        for dropdown, _ in dropdowns:
                            dropdown.expanded = False

                        if selected is not None:
                            kind, mode = selected

                            if mode is not None:
                                if kind == 1:
                                    self.change_agent(1, mode)
                                elif kind == 2:
                                    self.change_agent(2, mode)
                                else:
                                    self.change_map(mode)
                            else:
                                # Click vào nút dropdown:
                                # mở menu đã chọn.
                                for dropdown, k in dropdowns:
                                    if k == kind:
                                        dropdown.expanded = True
                                        break



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

