# Rank Settings #

ranks = ["Bronze 1", "Bronze 2", "Bronze 3",
         "Silver 1", "Silver 2", "Silver 3",
         "Gold 1", "Gold 2", "Gold 3",
         "Platinum 1", "Platinum 2", "Platinum 3",
         "Diamond 1", "Diamond 2", "Diamond 3"]
elo_per_rank = 100  # Amount of elo between each rank

# ELO Value Settings #

k_factor = 100  # Max value a player's elo can change by (not including multipliers)
elo_dif_10x_skill = 400  # Amount of elo between two players whereby higher player is 10x more likely to win game
starting_elo = len(ranks) * elo_per_rank / 2  # Elo value each player starts at (middle of ranks)
player_elo_range = elo_per_rank * 3  # Max difference in elo allowed on a team
team_elo_range = elo_per_rank * 1  # Max difference in average elo opposing teams can have

# Improvement Method Toggles #

# Win Streaks
win_streak_multiplier = 1  # Multiplier to elo change for win streak
win_streak_min = 3  # Minimum streak to get multiplier
# Initial Game Multiplier
initial_games_multiplier = 1  # Multiplier for first game
initial_games_count = 10  # Number of games until initial_games_multiplier reduced to 1
# Game Score Closeness Consideration
consider_game_closeness = True
# Consider individual performance when deciding how much to +/- elo for each player
consider_player_score = True
elo_change_lower_bound = 10  # If player won game but elo change calculated to be negative, this is set as the change
