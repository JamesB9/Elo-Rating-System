import random
from enum import Enum
from elo_settings import *
from sim_settings import *


class Outcome(Enum):
    WIN = 1
    LOSS = 2
    DRAW = 3


players = []
queued = []
players_unqueued = []
full_teams = []


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

    def gen_game_score(self):
        score = int(random.normalvariate(self.avg_skill, self.std_dev))
        self.score = score if score > 0 else 1
        return self.score

    def update_rank(self, elo_change, outcome):
        # Win Streak Multiplier
        if self.win_streak_count > 2:
            elo_change *= win_streak_multiplier

        # Initial Games Multiplier
        if not self.get_games_played() > initial_games_count:
            dif = initial_games_multiplier - 1
            elo_change *= initial_games_multiplier - (dif * self.get_games_played() / initial_games_count)

        # Change Elo
        self.elo += int(elo_change)
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


class Game:
    def __init__(self, team_a, team_b):
        self.team_a = team_a
        self.team_b = team_b

    def play(self):
        # Calculate Expected Scores
        expected_a = 1 / (1 + pow(10, (self.team_b.elo - self.team_a.elo) / 400))
        expected_b = 1 - expected_a

        # Generate Scores
        score_a = 0
        score_b = 0
        for player in self.team_a:
            score_a += player.gen_game_score()
        for player in self.team_b:
            score_b += player.gen_game_score()

        # Average Scores
        average_score_a = score_a / team_size
        average_score_b = score_b / team_size

        # Decide Outcome
        outcome_a = Outcome.WIN if score_a > score_b else Outcome.LOSS if score_a < score_b else Outcome.DRAW
        outcome_b = Outcome.WIN if score_b > score_a else Outcome.LOSS if score_b < score_a else Outcome.DRAW

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

        # Calculate Rating Change
        rating_change_a = k_factor * (score_a - expected_a)
        rating_change_b = k_factor * (score_b - expected_b)

        # Update each player's elo
        if consider_player_score:
            for player in self.team_a:
                elo_change = player_score_consideration(player, rating_change_a, average_score_b)
                player.update_rank(elo_change, outcome_a)
            for player in self.team_b:
                elo_change = player_score_consideration(player, rating_change_b, average_score_a)
                player.update_rank(elo_change, outcome_b)
        else:
            for player in self.team_a:
                player.update_rank(rating_change_a, outcome_a)
            for player in self.team_b:
                player.update_rank(rating_change_b, outcome_b)


def player_score_consideration(player, elo_change, avg_score_opponent):

    if elo_change > 0 and player.score < avg_score_opponent:  # If player won the game and got carried
        perc_dif = player.score / avg_score_opponent
        perc_dif = 2 if perc_dif > 2 else 1 if perc_dif < 1 else perc_dif
    elif elo_change < 0 and player.score > avg_score_opponent:  # If player lost the game but did better than opponents
        perc_dif = avg_score_opponent / player.score
        perc_dif = 2 if perc_dif > 2 else 0.5 if perc_dif < 0.5 else perc_dif
    else:
        perc_dif = 1

    return elo_change * perc_dif


def print_players():
    players.sort(key=lambda p: p.elo, reverse=True)

    # Print Table Column Headers
    print("{:>10} {:>15} {:>15} {:>10} {:>10} {:>10} {:>15} {:>10}".format(
        "Index", "Name", "Rank", "Elo", "Avg Score", "Sigma", "Games Played", "W/L/D"))

    # Print Table Contents
    for i, player in enumerate(players):
        print("{:>10} {:>15} {:>15} {:>10} {:>10} {:>10} {:>15} {:>10}".format(
            (i + 1), player.name, ranks[player.rank], player.elo, player.avg_skill, player.std_dev,
            player.get_games_played(),
            str(player.wins) + "/" + str(player.losses) + "/" + str(player.draws)))


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
    full_teams.sort(key=lambda t: t.elo, reverse=True)

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
