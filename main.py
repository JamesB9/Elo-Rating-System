import random

num_players = 100
team_size = 2
num_games = 10000
k_factor = 32


class Player:
    def __init__(self, name):
        self.name = name
        self.avg_skill = random.randint(1, 100)
        self.std_dev = 10  # random.randint(1, 20)
        self.elo = 1000
        self.games_played = 0

    def gen_game_score(self):
        self.games_played += 1
        return int(random.normalvariate(self.avg_skill, self.std_dev))

    def __str__(self):
        return 'Player {self.name}, {self.elo}, {self.avg_skill}, {self.std_dev}, {self.games_played}'.format(self=self)


class Team:
    def __init__(self, name):
        self.name = name
        self.players = []
        self.elo = 0

    def add_player(self, player):
        self.players.append(player)
        self.calculate_avg_elo()

    def calculate_avg_elo(self):
        elo = 0
        for player in self.players:
            elo += player.elo
        self.elo = elo / len(self.players)

    def __contains__(self, item):
        return item in self.players

    def __str__(self):
        s = "{}: ".format(self.name)
        for player in self.players:
            s += player.name + ", "
        return s

    def __iter__(self):
        return self.players.__iter__()

    def __len__(self):
        return len(self.players)


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

        # Turn Scores to 1, 0.5 and 0 (win, draw, loss)
        if score_a > score_b:
            score_a = 1
            score_b = 0
        elif score_b > score_a:
            score_b = 1
            score_a = 0
        else:
            score_a = 0.5
            score_b = 0.5

        rating_change_a = k_factor * (score_a - expected_a)
        rating_change_b = k_factor * (score_b - expected_b)

        for player in self.team_a:
            player.elo += int(rating_change_a)
        for player in self.team_b:
            player.elo += int(rating_change_b)

        # print(expected_a, expected_b, rating_change_a, rating_change_b)


def print_players(players):
    print(
        "{:>10} {:>15} {:>10} {:>10} {:>10} {:>10}".format("Rank", "Name", "Elo", "Avg Score", "Sigma", "Games Played"))
    for i, player in enumerate(players):
        print("{:>10} {:>15} {:>10} {:>10} {:>10} {:>10}".format(i, player.name, player.elo, player.avg_skill,
                                                                 player.std_dev,
                                                                 player.games_played))


def create_team(name, players, party=Team("Empty")):
    team = Team(name)
    for player in party:
        team.add_player(player)
        players.remove(player)

    while len(team) < team_size:
        player = players[random.randint(0, len(players) - 1)]
        team.add_player(player)
        players.remove(player)
    return team


def match_make(players, party=Team("Empty")):
    team_a = create_team("Team A", players, party)
    team_b = create_team("Team B", players)
    return team_a, team_b


def play_games(games_count, players):
    for i in range(games_count):
        team_a, team_b = match_make(players.copy())
        game = Game(team_a, team_b)
        game.play()


def main():
    # Create Players
    players = []
    for i in range(num_players):
        players.append(Player("Player {}".format(i + 1)))

    # print("PLAYERS BEFORE PLAYING {} GAMES".format(num_games))
    # print_players(players)

    play_games(num_games, players)

    shroud = Player("-=SHROUD=-")
    shroud.avg_skill = 90
    shroud.std_dev = 5
    players.append(shroud)
    party = Team("Team S")
    party.add_player(shroud)

    for i in range(400):
        team_a, team_b = match_make(players.copy(), party)
        print(team_a.elo)
        print(team_b.elo)
        print()
        game = Game(team_a, team_b)
        game.play()

    players.sort(key=lambda p: p.elo, reverse=True)
    print("\nPLAYERS AFTER PLAYING {} GAMES".format(num_games))
    print_players(players)


if __name__ == "__main__":
    main()
