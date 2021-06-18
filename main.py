import random, datetime
from enum import Enum
from elo_settings import *
from sim_settings import *

# LOGGING
time = str(datetime.datetime.now())
filename = "logs/" + time.replace(":", ".") + ".log"
logFile = open(filename, "w")
log = "LOG " + str(time) + "\n"
log += "Simulation Settings: \n" \
       "Number of Players: {} \n" \
       "Team Sizes: {} \n" \
       "Games per Player: {} \n" \
       "\nElo System Settings: \n" \
       "Elo Per Rank: {} \n" \
       "K Factor: {} \n" \
       "Win Streak Multiplayer: {} \n" \
       "Initial Games Multiplier: {} \n" \
       "Initial Games Count: {} \n" \
       "Consider Game Closeness: {} \n" \
       "Consider Player Scores: {} \n\n".format(num_players, team_size, games_per_player, elo_per_rank, k_factor,
                                                win_streak_multiplier, initial_games_multiplier, initial_games_count,
                                                consider_game_closeness, consider_player_score)

# LISTS

players = []
queued = []
players_unqueued = []
full_teams = []


class Outcome(Enum):
    WIN = 1
    LOSS = 2
    DRAW = 3


class Player:
    def __init__(self, name):
        # Player Sim Stats
        self.name = name
        self.avg_skill = random.randint(1, 1000)
        self.std_dev = 1  # random.randint(1, 200)

        # Elo / Rank
        self.elo = starting_elo
        self.rank = int(self.elo / elo_per_rank)

        # Wins / Losses / Draws
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.win_streak_count = 0  # Number of consecutive wins

        # Prev Score
        self.score = 0
        self.elo_change = 0

    def gen_game_score(self):
        score = int(random.normalvariate(self.avg_skill, self.std_dev))
        self.score = score if score > 0 else 1
        return self.score

    def update_rank(self, elo_change, outcome):
        # Win Streak Multiplier
        if self.win_streak_count >= win_streak_min:
            elo_change *= win_streak_multiplier

        # Initial Games Multiplier
        if not self.get_games_played() > initial_games_count:
            dif = initial_games_multiplier - 1
            elo_change *= initial_games_multiplier - (dif * self.get_games_played() / initial_games_count)

        # Change Elo
        self.elo += round(elo_change)
        self.elo_change = round(elo_change)
        if self.elo < 0:
            self.elo = 0

        # Update Rank
        self.rank = int(self.elo / elo_per_rank)
        self.rank = len(ranks) - 1 if self.rank >= len(ranks) else self.rank

        # Update Win/Loss
        if outcome == outcome.WIN:
            self.wins += 1
            self.win_streak_count += 1
        elif outcome == outcome.DRAW:
            self.draws += 1
            self.win_streak_count = 0
        elif outcome == outcome.LOSS:
            self.losses += 1
            self.win_streak_count = 0

    def get_games_played(self):
        return self.wins + self.draws + self.losses

    def __str__(self):
        return '{self.name}, {self.elo}'.format(self=self)


class Team:
    def __init__(self, *members):
        self.members = list(members)
        self.elo = 0
        self.calculate_avg_elo()

    def add_member(self, player):
        self.members.append(player)
        self.calculate_avg_elo()

    def calculate_avg_elo(self):
        elo = 0
        for player in self.members:
            elo += player.elo
        self.elo = elo / len(self.members)

    def __iadd__(self, other):
        self.members.extend(other.members)
        self.calculate_avg_elo()

    def __contains__(self, item):
        return item in self.members

    def __str__(self):
        s = ""
        for player in self.members:
            s += "{:<10} {:>10} {:>4}, ".format(player.name, ranks[player.rank], str(player.elo))
        s += str(self.elo)
        return s

    def __iter__(self):
        return self.members.__iter__()

    def __len__(self):
        return len(self.members)


def normalise_scores(score_a, score_b):
    # Turn Scores to 1, 0.5 and 0 (win, draw, loss)
    if consider_game_closeness:
        score_a = score_a / ((score_b + 0.01) * 2)  # +0.01 to ensure divisor is never 0
        if score_a > 1:
            score_a = 1
        score_b = 1 - score_a
    else:
        if score_a > score_b:
            score_a = 1
            score_b = 0
        elif score_b > score_a:
            score_b = 1
            score_a = 0
        else:
            score_a = 0.5
            score_b = 0.5

    return score_a, score_b


class Game:
    def __init__(self, team_a, team_b):
        self.team_a = team_a
        self.team_b = team_b
        self.average_score_a = 0
        self.average_score_b = 0
        self.outcome_a = None
        self.outcome_b = None

    def play(self):
        # Generate Scores
        score_a = 0
        score_b = 0
        for player in self.team_a:
            score_a += player.gen_game_score()
        for player in self.team_b:
            score_b += player.gen_game_score()

        # Average Scores
        self.average_score_a = score_a / team_size
        self.average_score_b = score_b / team_size

        # Decide Outcome
        self.outcome_a = Outcome.WIN if score_a > score_b else Outcome.LOSS if score_a < score_b else Outcome.DRAW
        self.outcome_b = Outcome.WIN if score_b > score_a else Outcome.LOSS if score_b < score_a else Outcome.DRAW

        # Change Player Elo
        if consider_player_score:
            self.update_elo_consider_player_score(self.average_score_a, self.average_score_b)
        else:
            self.update_elo(score_a, score_b)

        self.log_leaderboard()

    def update_elo(self, score_a, score_b):
        # Turn Scores to 1, 0.5 and 0 (win, draw, loss)
        score_a, score_b = normalise_scores(score_a, score_b)
        # Calculate Expected Scores
        expected_a = 1 / (1 + pow(10, (self.team_b.elo - self.team_a.elo) / elo_dif_10x_skill))
        expected_b = 1 - expected_a
        # Calculate Rating Change
        rating_change_a = k_factor * (score_a - expected_a)
        rating_change_b = k_factor * (score_b - expected_b)

        # Update each player's elo
        for player in self.team_a:
            player.update_rank(rating_change_a, self.outcome_a)
        for player in self.team_b:
            player.update_rank(rating_change_b, self.outcome_b)

    def update_elo_consider_player_score(self, score_a, score_b):
        # Update each player's elo
        for player in self.team_a:
            # Calculate Expected Scores
            expected = 1 / (1 + pow(10, (self.team_b.elo - player.elo) / elo_dif_10x_skill))
            # Score
            score, unused_score_b = normalise_scores(player.score, score_b)  # unused_score_b is throw away variable
            # Calculate Rating Change
            rating_change = k_factor * (score - expected)
            # Ensure rating_change isn't positive for a loss and negative for a win
            if self.outcome_a == Outcome.WIN and rating_change < 0:
                rating_change = elo_change_lower_bound
            elif self.outcome_a == Outcome.LOSS and rating_change > 0:
                rating_change = -elo_change_lower_bound

            # Update player elo
            player.update_rank(rating_change, self.outcome_a)

        for player in self.team_b:
            # Calculate Expected Scores
            expected = 1 / (1 + pow(10, (self.team_a.elo - player.elo) / elo_dif_10x_skill))
            # Score
            score, unused_score_a = normalise_scores(player.score, score_a)  # unused_score_b is throw away variable
            # Calculate Rating Change
            rating_change = k_factor * (score - expected)
            # Ensure rating_change isn't positive for a loss and negative for a win
            if self.outcome_b == Outcome.WIN and rating_change < 0:
                rating_change = elo_change_lower_bound
            elif self.outcome_b == Outcome.LOSS and rating_change > 0:
                rating_change = -elo_change_lower_bound
            # Update player elo
            player.update_rank(rating_change, self.outcome_b)

    def log_leaderboard(self):
        global log
        # Game Header
        leaderboard = "\nTeam A ({}) VS Team B ({}) \n".format(self.team_a.elo, self.team_b.elo)
        # Game Outcome
        if self.outcome_a == Outcome.WIN:
            leaderboard += "Winner: TEAM A  -  {} to {} \n".format(self.average_score_a, self.average_score_b)
        elif self.outcome_a == Outcome.LOSS:
            leaderboard += "Winner: TEAM B  -  {} to {} \n".format(self.average_score_b, self.average_score_a)
        else:
            leaderboard += "DRAW  -  {} to {} \n".format(self.average_score_a, self.average_score_b)

        # Column Headers
        leaderboard += "{:<6} {:<10} {:>10} {:>10} {:>15} {:>10} {:>10} \n".format("Team", "Name", "Avg Skill", "Score",
                                                                                   "Rank", "Elo", "Elo +/-")
        # Sort Players
        self.team_a.members.sort(key=lambda p: p.score, reverse=True)
        self.team_b.members.sort(key=lambda p: p.score, reverse=True)
        # Print Player Information
        for player in self.team_a:
            extra_detail = "  "
            if player.win_streak_count >= win_streak_min and win_streak_multiplier > 1:
                extra_detail += " s_x" + str(win_streak_multiplier)
            if player.get_games_played() < initial_games_count and initial_games_multiplier > 1:
                extra_detail += " g_x" + str(initial_games_multiplier)
            leaderboard += "{:<6} {:<10} {:>10} {:>10} {:>15} {:>10} {:>10} {:<10}\n".format(
                "A", player.name, player.avg_skill, player.score, ranks[player.rank], player.elo, player.elo_change,
                extra_detail)
        leaderboard += "\n"
        for player in self.team_b:
            extra_detail = "  "
            if player.win_streak_count >= win_streak_min and win_streak_multiplier > 1:
                extra_detail += " s_x" + str(player.win_streak_count)
            if player.get_games_played() < initial_games_count and initial_games_multiplier > 1:
                extra_detail += " g_x" + str(initial_games_multiplier)
            leaderboard += "{:<6} {:<10} {:>10} {:>10} {:>15} {:>10} {:>10} {:<10}\n".format(
                "B", player.name, player.avg_skill, player.score, ranks[player.rank], player.elo, player.elo_change,
                extra_detail)
        log += leaderboard


def print_players():
    global log
    players.sort(key=lambda p: p.elo, reverse=True)
    # Print Table Column Headers
    table = "\nTable of Players: \n {:>10} {:>15} {:>15} {:>10} {:>10} {:>10} {:>15} {:>10} \n".format(
        "Index", "Name", "Rank", "Elo", "Avg Skill", "Sigma", "Games Played", "W/L/D")

    # Print Table Contents
    for i, player in enumerate(players):
        table += "{:>10} {:>15} {:>15} {:>10} {:>10} {:>10} {:>15} {:>10} \n".format(
            (i + 1), player.name, ranks[player.rank], player.elo, player.avg_skill, player.std_dev,
            player.get_games_played(),
            str(player.wins) + "/" + str(player.losses) + "/" + str(player.draws))

    log += table


def match_make(team):
    if len(team) == team_size:  # If party size is a full team
        full_teams.append(team)
    else:  # If party size is less than a full team
        merged_into = -1
        for i, qteam in enumerate(queued):
            if valid_team_merge(qteam, team):
                qteam += team
                merged_into = i
                break

        if merged_into == -1:
            queued.append(team)
        elif len(queued[merged_into]) == team_size:
            full_teams.append(queued[merged_into])
            queued.remove(queued[merged_into])


def check_for_games():
    # Match Full Teams
    #full_teams.sort(key=lambda t: t.elo, reverse=True)
    random.shuffle(full_teams)

    for i, full_team in enumerate(full_teams):
        if i + 1 < len(full_teams) and abs(full_team.elo - full_teams[i + 1].elo) < team_elo_range:
            # Select Teams
            full_team_a = full_team
            full_team_b = full_teams[i + 1]

            # Play Game
            game = Game(full_team_a, full_team_b)
            game.play()

            # Remove Full Teams from queue
            full_teams.remove(full_team_a)
            full_teams.remove(full_team_b)
            # Un queue all players
            for player in full_team_a:
                players_unqueued.append(player)
            for player in full_team_b:
                players_unqueued.append(player)

            return 1  # Return 1 game played

    return 0  # Return 0 games played


def valid_team_merge(team_a, team_b):
    if len(team_a) + len(team_b) <= team_size:  # If team is within size
        if abs(team_a.elo - team_b.elo) < player_elo_range:  # If elo within range
            return True
    return False


def match_make_all_players():
    random.shuffle(players_unqueued)
    for i in range(len(players_unqueued)):
        match_make(Team(players_unqueued[0]))
        players_unqueued.remove(players_unqueued[0])


def main():
    # Create Players
    for i in range(num_players):
        player = Player("Player {}".format(i + 1))
        players.append(player)
        players_unqueued.append(player)

    print_players()

    # Match Make Players (find teammates)
    match_make_all_players()

    # Play Games and randomly search players again (once game finished)
    game_count = 0
    while game_count < num_games:
        games_played = check_for_games()
        game_count += games_played

        if games_played == 0:  # No Games could be found (out of players or too different in skill)
            match_make_all_players()  # Re-fill queue with players

    print_players()


if __name__ == "__main__":
    main()
    logFile.write(log)
    logFile.close()
