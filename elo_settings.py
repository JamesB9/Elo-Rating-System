# Rank Settings #

ranks = ["Bronze 1", "Bronze 2", "Bronze 3",
         "Silver 1", "Silver 2", "Silver 3",
         "Gold 1", "Gold 2", "Gold 3",
         "Platinum 1", "Platinum 2", "Platinum 3",
         "Diamond 1", "Diamond 2", "Diamond 3"]
elo_per_rank = 100  # Amount of elo between each rank


# ELO Value Settings #

k_factor = 32  # Max value a player's elo can change by (not including multipliers)
starting_elo = len(ranks) * elo_per_rank / 2  # Elo value each player starts at (middle of ranks)
player_elo_range = elo_per_rank * 3  # Max difference in elo allowed on a team
team_elo_range = elo_per_rank * 2  # Max difference in average elo opposing teams can have


# Improvement Method Toggles #

# Win Streaks
win_streak_multiplier = 2
# Initial Game Multiplier
initial_games_multiplier = 2  # Multiplier for first game
initial_games_count = 10  # Number of games until initial_games_multiplier reduced to 1
