from enum import Enum
from typing import List, Tuple, Dict, Optional

class Action(Enum):
    MOVE_UP = (0, -1)
    MOVE_DOWN = (0, 1)
    MOVE_LEFT = (-1, 0)
    MOVE_RIGHT = (1, 0)
    FIRE = (0, 0)
    STAY = (0, 0)

DIRECTION_DELTAS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0)
}

ACTION_TO_DIR = {
    Action.MOVE_UP: "UP",
    Action.MOVE_DOWN: "DOWN",
    Action.MOVE_LEFT: "LEFT",
    Action.MOVE_RIGHT: "RIGHT"
}

class Tank:
    def __init__(self, player_id: int, x: int, y: int, direction: str = "UP", hp: int = 6):
        self.player_id = player_id
        self.x = x
        self.y = y
        self.direction = direction
        self.hp = hp

    def clone(self) -> 'Tank':
        return Tank(self.player_id, self.x, self.y, self.direction, self.hp)

class Base:
    def __init__(self, player_id: int, x: int, y: int, hp: int = 9):
        self.player_id = player_id
        self.x = x
        self.y = y
        self.hp = hp

    def clone(self) -> 'Base':
        return Base(self.player_id, self.x, self.y, self.hp)

class Bullet:
    def __init__(self, owner_id: int, x: int, y: int, direction: str):
        self.owner_id = owner_id
        self.x = x
        self.y = y
        self.direction = direction

    def clone(self) -> 'Bullet':
        return Bullet(self.owner_id, self.x, self.y, self.direction)

class GameState:
    def __init__(self, width: int, height: int, tanks: Dict[int, Tank], 
                 bases: Dict[int, Base], walls: Dict[Tuple[int, int], int], 
                 bullets: List[Bullet], current_turn: int = 1, turn_count: int = 0):
        self.width = width
        self.height = height
        self.tanks = tanks          # {1: Tank1, 2: Tank2}
        self.bases = bases          # {1: Base1, 2: Base2}
        self.walls = walls          # {(x, y): hp} với hp khởi tạo = 3
        self.bullets = bullets
        self.current_turn = current_turn
        self.turn_count = turn_count

    def clone(self) -> 'GameState':
        """Sao chép trạng thái nhanh để tăng tốc độ duyệt cây Minimax."""
        return GameState(
            self.width, self.height,
            {k: v.clone() for k, v in self.tanks.items()},
            {k: v.clone() for k, v in self.bases.items()},
            self.walls.copy(),
            [b.clone() for b in self.bullets],
            self.current_turn,
            self.turn_count
        )

    def is_within_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_cell_blocked(self, x: int, y: int) -> bool:
        if not self.is_within_bounds(x, y):
            return True
        if (x, y) in self.walls:
            return True
        for t in self.tanks.values():
            if t.hp > 0 and t.x == x and t.y == y:
                return True
        for b in self.bases.values():
            if b.hp > 0 and b.x == x and b.y == y:
                return True
        return False

    def get_legal_actions(self) -> List[Action]:
        """Trả về danh sách các hành động hợp lệ cho xe tăng đang giữ lượt."""
        tank = self.tanks[self.current_turn]
        actions = [Action.FIRE, Action.STAY]
        for move_act in [Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT]:
            dx, dy = move_act.value
            nx, ny = tank.x + dx, tank.y + dy
            if not self.is_cell_blocked(nx, ny):
                actions.append(move_act)
            elif tank.direction != ACTION_TO_DIR[move_act]:
                # Vẫn cho phép xoay hướng tại chỗ dù phía trước bị chặn
                actions.append(move_act)
        return actions

    def apply_action(self, action: Action) -> 'GameState':
        """Hàm chuyển trạng thái (Transition Function): Thực thi hành động và di chuyển đạn."""
        next_state = self.clone()
        tank = next_state.tanks[next_state.current_turn]

        # 1. Xử lý hành động của Tank
        if action in ACTION_TO_DIR:
            tank.direction = ACTION_TO_DIR[action]
            dx, dy = action.value
            nx, ny = tank.x + dx, tank.y + dy
            if not next_state.is_cell_blocked(nx, ny):
                tank.x, tank.y = nx, ny
        elif action == Action.FIRE:
            next_state.bullets.append(Bullet(tank.player_id, tank.x, tank.y, tank.direction))

        # 2. Xử lý đạn bay (3 ô mỗi chu kỳ, kiểm tra va chạm từng ô một)
        surviving_bullets = []
        for bullet in next_state.bullets:
            dx, dy = DIRECTION_DELTAS[bullet.direction]
            bullet_alive = True
            for _ in range(3):
                bullet.x += dx
                bullet.y += dy
                
                # Ra ngoài biên bản đồ
                if not next_state.is_within_bounds(bullet.x, bullet.y):
                    bullet_alive = False
                    break
                
                # Va chạm Tường (Máu = 3, Sát thương = 1)
                pos = (bullet.x, bullet.y)
                if pos in next_state.walls:
                    next_state.walls[pos] -= 1
                    if next_state.walls[pos] <= 0:
                        del next_state.walls[pos]
                    bullet_alive = False
                    break
                
                # Va chạm Tank (Máu = 6, Sát thương = 1)
                hit_tank = False
                for t in next_state.tanks.values():
                    if t.hp > 0 and t.x == bullet.x and t.y == bullet.y:
                        t.hp -= 1
                        hit_tank = True
                        break
                if hit_tank:
                    bullet_alive = False
                    break

                # Va chạm Base (Máu = 9, Sát thương = 1)
                hit_base = False
                for b in next_state.bases.values():
                    if b.hp > 0 and b.x == bullet.x and b.y == bullet.y:
                        b.hp -= 1
                        hit_base = True
                        break
                if hit_base:
                    bullet_alive = False
                    break

            if bullet_alive:
                surviving_bullets.append(bullet)

        next_state.bullets = surviving_bullets
        next_state.current_turn = 2 if self.current_turn == 1 else 1
        next_state.turn_count += 1
        return next_state

    def is_terminal(self, max_turns: int = 200) -> bool:
        for t in self.tanks.values():
            if t.hp <= 0:
                return True
        for b in self.bases.values():
            if b.hp <= 0:
                return True
        return self.turn_count >= max_turns

    def get_utility(self, max_player: int = 1) -> float:
        """Hàm Utility chính xác cho Terminal State."""
        min_player = 2 if max_player == 1 else 1
        max_dead = (self.tanks[max_player].hp <= 0) or (self.bases[max_player].hp <= 0)
        min_dead = (self.tanks[min_player].hp <= 0) or (self.bases[min_player].hp <= 0)

        if max_dead and min_dead:
            return 0.0
        if min_dead:
            return 10000.0
        if max_dead:
            return -10000.0
        return 0.0