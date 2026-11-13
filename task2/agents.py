import time
import math
from engine import GameState, Action

class BaseAgent:
    def __init__(self, player_id: int, max_depth: int = 4):
        self.player_id = player_id
        self.max_depth = max_depth
        self.nodes_explored = 0
        self.last_exec_time = 0.0

    def get_action(self, state: GameState) -> Action:
        raise NotImplementedError

    def evaluate_heuristic(self, state: GameState) -> float:
        """
        Hàm Heuristic Eval(s) đánh giá trạng thái khi đạt độ sâu cắt (Cutoff Depth).
        Kết hợp: Chênh lệch máu Tank, máu Base, khoảng cách Manhattan, và đường ngắm bắn.
        """
        if state.is_terminal():
            return state.get_utility(self.player_id)

        opp_id = 2 if self.player_id == 1 else 1
        my_tank, opp_tank = state.tanks[self.player_id], state.tanks[opp_id]
        my_base, opp_base = state.bases[self.player_id], state.bases[opp_id]

        # 1. Trọng số máu (Ưu tiên giữ mạng và bảo vệ Base)
        hp_score = 150.0 * (my_tank.hp - opp_tank.hp) + 120.0 * (my_base.hp - opp_base.hp)

        # 2. Khoảng cách Manhattan tiến về phía địch / Base địch
        dist_to_opp_tank = abs(my_tank.x - opp_tank.x) + abs(my_tank.y - opp_tank.y)
        dist_to_opp_base = abs(my_tank.x - opp_base.x) + abs(my_tank.y - opp_base.y)
        position_score = -5.0 * dist_to_opp_tank - 8.0 * dist_to_opp_base

        # 3. Điểm thưởng khi đứng cùng hàng/cột và hướng nòng súng về phía mục tiêu (Line of Sight)
        aim_score = 0.0
        if my_tank.x == opp_tank.x or my_tank.y == opp_tank.y:
            aim_score += 25.0
        if my_tank.x == opp_base.x or my_tank.y == opp_base.y:
            aim_score += 30.0

        # 4. Phạt nặng nếu xe tăng mình đang nằm trên đường bay của đạn địch
        danger_penalty = 0.0
        for b in state.bullets:
            if b.owner_id == opp_id and (b.x == my_tank.x or b.y == my_tank.y):
                danger_penalty -= 80.0

        return hp_score + position_score + aim_score + danger_penalty


class SearchAgent(BaseAgent):
    def __init__(self, player_id: int, max_depth: int = 4, 
                 use_heuristic: bool = True, use_alpha_beta: bool = True):
        super().__init__(player_id, max_depth)
        self.use_heuristic = use_heuristic
        self.use_alpha_beta = use_alpha_beta

    def _leaf_value(self, state: GameState) -> float:
        if self.use_heuristic:
            return self.evaluate_heuristic(state)
        return state.get_utility(self.player_id)

    def _order_actions(self, actions):
        """Sắp xếp thứ tự hành động (Move Ordering): Ưu tiên FIRE trước để cắt tỉa Alpha-Beta tốt hơn."""
        priority = {Action.FIRE: 0, Action.MOVE_UP: 1, Action.MOVE_DOWN: 1, 
                    Action.MOVE_LEFT: 1, Action.MOVE_RIGHT: 1, Action.STAY: 2}
        return sorted(actions, key=lambda a: priority[a])

    def get_action(self, state: GameState) -> Action:
        self.nodes_explored = 0
        start_time = time.perf_counter()

        best_action = Action.STAY
        best_val = -math.inf
        alpha, beta = -math.inf, math.inf

        actions = self._order_actions(state.get_legal_actions())
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
            return self._leaf_value(state)

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
            return self._leaf_value(state)

        actions = self._order_actions(state.get_legal_actions())
        if is_maximizing:
            max_eval = -math.inf
            for action in actions:
                eval_val = self._alphabeta(state.apply_action(action), depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break  # Beta Cutoff
            return max_eval
        else:
            min_eval = math.inf
            for action in actions:
                eval_val = self._alphabeta(state.apply_action(action), depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break  # Alpha Cutoff
            return min_eval