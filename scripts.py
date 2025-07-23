leaderboard = {}

def add_score(player_name, score):
    leaderboard[player_name] = score

def display_leaderboard():
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda item: item[1], reverse=True)
    for player, score in sorted_leaderboard:
        print(f"{player}: {score}")

def find_top_player():
    if not leaderboard:
        return None
    return max(leaderboard, key=leaderboard.get)

# Example usage
add_score("Alice", 1200)
add_score("Bob", 950)
add_score("Charlie", 1500)

display_leaderboard()
top_player = find_top_player()
print(f"Top player: {top_player}")
