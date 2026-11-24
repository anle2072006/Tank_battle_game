import time
import math
import heapq
from engine import GameState, Action, DIRECTION_DELTAS


class BaseAgent:
    def __init__(self, player_id: int, max_depth: int = 4):
        self.player_id = player_id
        self.max_depth = max_depth
        self.nodes_explored = 0
        self.last_exec_time = 0.0
        self._dist_cache = {}

    def get_action(self, state: GameState) -> Action:
        raise NotImplementedError

    def _get_dist_map(self, state: GameState, tx: int, ty: int, walls_key=None) -> dict:
        """
        Tính bản đồ khoảng cách ngắn nhất có xét chi phí phá tường (Weighted Dijkstra):
        - Ô trống có chi phí = 1.
        - Ô tường gạch có chi phí = hp + 1 (số lượt bắn phá tường + 1 lượt đi qua).
        - Ô chứa căn cứ (Base) khác mục tiêu bị chặn, không cho xe tăng đi xuyên qua.
        Kết quả được lưu cache theo trạng thái tường để đạt tốc độ O(1) khi duyệt cây.
        """
        if walls_key is None:
            walls_key = frozenset(state.walls.items())
        key = (tx, ty, walls_key)
        if key in self._dist_cache:
            return self._dist_cache[key]

        blocked_bases = {
            (b.x, b.y) for b in state.bases.values()
            if b.hp > 0 and (b.x, b.y) != (tx, ty)
        }
        dist = {(tx, ty): 0}
        pq = [(0, tx, ty)]
        walls = state.walls
        w, h = state.width, state.height

        while pq:
            d, x, y = heapq.heappop(pq)
            if d > dist[(x, y)]:
                continue
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    if (nx, ny) in blocked_bases:
                        continue
                    step_cost = walls[(nx, ny)] + 1 if (nx, ny) in walls else 1
                    nd = d + step_cost
                    if nd < dist.get((nx, ny), 9999):
                        dist[(nx, ny)] = nd
                        heapq.heappush(pq, (nd, nx, ny))

        self._dist_cache[key] = dist
        return dist

    def _has_clear_los(self, state: GameState, x: int, y: int,
                       direction: str, tx: int, ty: int) -> bool:
        """
        Kiểm tra đường ngắm thẳng (Line of Sight):
        Trả về True nếu mục tiêu (tx, ty) nằm đúng hướng nhìn và không có vật cản ở giữa.
        """
        dx, dy = DIRECTION_DELTAS[direction]
        if dx == 0:
            if x != tx or (ty - y) * dy <= 0:
                return False
        else:
            if y != ty or (tx - x) * dx <= 0:
                return False

        cx, cy = x + dx, y + dy
        while (cx, cy) != (tx, ty):
            if (cx, cy) in state.walls:
                return False
            for t in state.tanks.values():
                if t.hp > 0 and t.x == cx and t.y == cy:
                    return False
            for b in state.bases.values():
                if b.hp > 0 and b.x == cx and b.y == cy:
                    return False
            cx += dx
            cy += dy
        return True

    def evaluate_heuristic(self, state: GameState) -> float:
        """
        Hàm Heuristic Eval(s) đánh giá trạng thái tại độ sâu cắt (Cutoff Depth).
        Kết hợp 5 thành phần:
        1. Chênh lệch máu Tank và Base.
        2. Khoảng cách đường đi ngắn nhất có xét tường chắn và Base (Weighted Dijkstra).
        3. Độ bền tường lá chắn bao quanh căn cứ.
        4. Đường ngắm bắn trực diện có xét tầm sát thương tức thì (<= 3 ô).
        5. Mức độ đe dọa/cơ hội từ các viên đạn đang bay.
        """
        if state.is_terminal():
            return state.get_utility(self.player_id)

        opp_id = 2 if self.player_id == 1 else 1
        my_tank, opp_tank = state.tanks[self.player_id], state.tanks[opp_id]
        my_base, opp_base = state.bases[self.player_id], state.bases[opp_id]

        # 1. Trọng số máu (ưu tiên gây sát thương dứt điểm địch, bảo vệ căn cứ và giữ mạng khi máu thấp)
        hp_score = (
            170.0 * my_tank.hp
            - 210.0 * opp_tank.hp
            + 200.0 * (my_base.hp - opp_base.hp)
        )
        if my_tank.hp <= 2:
            hp_score -= 120.0 * (3 - my_tank.hp)

        # 2. Khoảng cách đường đi ngắn nhất có xét tường (tính walls_key 1 lần cho cả 3 lần tra cứu)
        walls_key = frozenset(state.walls.items())
        dist_to_opp_tank = self._get_dist_map(state, opp_tank.x, opp_tank.y, walls_key).get((my_tank.x, my_tank.y), 99)
        dist_to_opp_base = self._get_dist_map(state, opp_base.x, opp_base.y, walls_key).get((my_tank.x, my_tank.y), 99)
        opp_dist_to_my_base = self._get_dist_map(state, my_base.x, my_base.y, walls_key).get((opp_tank.x, opp_tank.y), 99)
        chase_weight = 14.0 if opp_tank.hp <= 2 else 6.0
        position_score = (
            -chase_weight * dist_to_opp_tank
            - 8.0 * dist_to_opp_base
            + 5.0 * opp_dist_to_my_base
        )

        # 3. Bảo vệ tường lá chắn ngay sát căn cứ mình và khuyến khích phá tường nhà địch
        my_shield_hp = sum(
            state.walls.get((my_base.x + dx, my_base.y + dy), 0)
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))
        )
        opp_shield_hp = sum(
            state.walls.get((opp_base.x + dx, opp_base.y + dy), 0)
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))
        )
        shield_score = 12.0 * (my_shield_hp - opp_shield_hp)

        # 4. Đường ngắm bắn trực diện (ưu tiên cao hơn khi trong tầm bắn 3 ô tức thì)
        aim_score = 0.0
        manhattan_tanks = abs(my_tank.x - opp_tank.x) + abs(my_tank.y - opp_tank.y)
        manhattan_my_opp_base = abs(my_tank.x - opp_base.x) + abs(my_tank.y - opp_base.y)
        manhattan_opp_my_base = abs(opp_tank.x - my_base.x) + abs(opp_tank.y - my_base.y)

        if self._has_clear_los(state, my_tank.x, my_tank.y, my_tank.direction, opp_tank.x, opp_tank.y):
            aim_score += 45.0 if manhattan_tanks <= 3 else 25.0
        if self._has_clear_los(state, my_tank.x, my_tank.y, my_tank.direction, opp_base.x, opp_base.y):
            aim_score += 50.0 if manhattan_my_opp_base <= 3 else 30.0
        if self._has_clear_los(state, opp_tank.x, opp_tank.y, opp_tank.direction, my_tank.x, my_tank.y):
            aim_score -= 40.0 if manhattan_tanks <= 3 else 20.0
        if self._has_clear_los(state, opp_tank.x, opp_tank.y, opp_tank.direction, my_base.x, my_base.y):
            aim_score -= 45.0 if manhattan_opp_my_base <= 3 else 25.0

        # 5. Đánh giá đạn đang bay (phạt nặng nếu đạn địch nhắm vào mình, thưởng nếu đạn mình trúng hướng)
        bullet_score = 0.0
        for b in state.bullets:
            if b.owner_id == opp_id:
                if self._has_clear_los(state, b.x, b.y, b.direction, my_tank.x, my_tank.y):
                    bullet_score -= 90.0
                if self._has_clear_los(state, b.x, b.y, b.direction, my_base.x, my_base.y):
                    bullet_score -= 70.0
            else:
                if self._has_clear_los(state, b.x, b.y, b.direction, opp_tank.x, opp_tank.y):
                    bullet_score += 70.0
                if self._has_clear_los(state, b.x, b.y, b.direction, opp_base.x, opp_base.y):
                    bullet_score += 60.0

        return hp_score + position_score + shield_score + aim_score + bullet_score


class SearchAgent(BaseAgent):
    def __init__(self, player_id: int, max_depth: int = 4,
                 use_heuristic: bool = True, use_alpha_beta: bool = True):
        super().__init__(player_id, max_depth)
        self.use_heuristic = use_heuristic
        self.use_alpha_beta = use_alpha_beta

    def _leaf_value(self, state: GameState, depth: int) -> float:
        if state.is_terminal():
            util = state.get_utility(self.player_id)
            if self.use_heuristic:
                # Ưu tiên kết thúc thắng sớm và trì hoãn thua muộn
                if util > 0:
                    return util + depth * 10.0
                if util < 0:
                    return util - depth * 10.0
            return util
        if self.use_heuristic:
            return self.evaluate_heuristic(state)
        return 0.0

    def _has_fire_target(self, state: GameState) -> bool:
        """Kiểm tra xem phía trước nòng súng có tường, xe tăng địch hoặc căn cứ địch không."""
        tank = state.tanks[state.current_turn]
        dx, dy = DIRECTION_DELTAS[tank.direction]
        cx, cy = tank.x + dx, tank.y + dy
        while state.is_within_bounds(cx, cy):
            if (cx, cy) in state.walls:
                return True
            for t in state.tanks.values():
                if t.hp > 0 and t.player_id != tank.player_id and t.x == cx and t.y == cy:
                    return True
            for b in state.bases.values():
                if b.hp > 0 and b.x == cx and b.y == cy:
                    return b.player_id != tank.player_id
            cx += dx
            cy += dy
        return False

    def _order_actions(self, actions, state: GameState = None):
        """Sắp xếp thứ tự hành động (Move Ordering): chỉ ưu tiên FIRE khi có mục tiêu phía trước."""
        if state is not None and self.use_heuristic and not self._has_fire_target(state):
            priority = {
                Action.MOVE_UP: 0,
                Action.MOVE_DOWN: 0,
                Action.MOVE_LEFT: 0,
                Action.MOVE_RIGHT: 0,
                Action.FIRE: 1,
                Action.STAY: 2,
            }
        else:
            priority = {
                Action.FIRE: 0,
                Action.MOVE_UP: 1,
                Action.MOVE_DOWN: 1,
                Action.MOVE_LEFT: 1,
                Action.MOVE_RIGHT: 1,
                Action.STAY: 2,
            }
        return sorted(actions, key=lambda a: priority[a])

    def get_action(self, state: GameState) -> Action:
        self.nodes_explored = 0
        self._dist_cache.clear()
        start_time = time.perf_counter()

        best_action = Action.STAY
        best_val = -math.inf
        alpha, beta = -math.inf, math.inf

        legal_actions = state.get_legal_actions()
        if self.use_alpha_beta:
            actions = self._order_actions(legal_actions, state)
            if self.use_heuristic:
                # Sắp xếp nước đi tại nút gốc theo điểm Heuristic 1 bước để cắt tỉa sâu và tránh trì hoãn khi đồng điểm
                actions.sort(key=lambda a: self.evaluate_heuristic(state.apply_action(a)), reverse=True)
        elif self.use_heuristic:
            # Áp dụng Move Ordering tại nút gốc cho Heuristic Minimax để tránh bắn gió khi đồng điểm
            actions = self._order_actions(legal_actions, state)
        else:
            actions = legal_actions

        for action in actions:
            next_state = state.apply_action(action)
            if self.use_alpha_beta:
                val = self._alphabeta(next_state, self.max_depth - 1, alpha, beta, False)
                alpha = max(alpha, val)
            else:
                val = self._minimax(next_state, self.max_depth - 1, False)

            if val > best_val:
                best_val = val
                best_action = action

        self.last_exec_time = (time.perf_counter() - start_time) * 1000.0  # ms
        return best_action

    def _minimax(self, state: GameState, depth: int, is_maximizing: bool) -> float:
        self.nodes_explored += 1
        if depth == 0 or state.is_terminal():
            return self._leaf_value(state, depth)

        actions = state.get_legal_actions()
        if is_maximizing:
            max_eval = -math.inf
            for action in actions:
                eval_val = self._minimax(state.apply_action(action), depth - 1, False)
                max_eval = max(max_eval, eval_val)
            return max_eval
        else:
            min_eval = math.inf
            for action in actions:
                eval_val = self._minimax(state.apply_action(action), depth - 1, True)
                min_eval = min(min_eval, eval_val)
            return min_eval

    def _alphabeta(self, state: GameState, depth: int, alpha: float, beta: float, is_maximizing: bool) -> float:
        self.nodes_explored += 1
        if depth == 0 or state.is_terminal():
            return self._leaf_value(state, depth)

        actions = self._order_actions(state.get_legal_actions(), state)
        if is_maximizing:
            max_eval = -math.inf
            for action in actions:
                eval_val = self._alphabeta(state.apply_action(action), depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break  # Cắt tỉa Beta
            return max_eval
        else:
            min_eval = math.inf
            for action in actions:
                eval_val = self._alphabeta(state.apply_action(action), depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break  # Cắt tỉa Alpha
            return min_eval