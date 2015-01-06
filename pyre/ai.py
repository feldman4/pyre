

def game_of_life(spin, score):
    # score = s.neighbor_sum()

    if spin & (score < 2 or score > 3):
        spin = False
    elif not spin & score == 3:
        spin = True

    return spin
