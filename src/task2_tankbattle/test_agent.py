from engine import Action


class ExternalAgent:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.nodes_explored = 0
        self.last_exec_time = 0.0

    def get_action(self, state) -> Action:
        legal_actions = state.get_legal_actions()

        if Action.FIRE in legal_actions:
            return Action.FIRE

        return Action.STAY