import random

def roll_dice(sides=20):
    """Roll a dice with given sides (default d20)."""
    return random.randint(1, sides)
