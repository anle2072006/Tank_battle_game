from itertools import combinations

def get_valid_combinations(target_sum, length):
    valid_combos = []
    for combo in combinations(range(1, 10), length):
        if sum(combo) == target_sum:
            valid_combos.append(combo)
    return valid_combos