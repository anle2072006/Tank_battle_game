
from engine import Action


class ExternalAgent:
    def __init__(self, player_id):
        self.player_id = player_id
        self.nodes_explored = 0

    def get_action(self, state):
        legal_actions = state.get_legal_actions()

        if Action.FIRE in legal_actions:
            return Action.FIRE

        return Action.STAY
