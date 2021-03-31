import random

num_players = 10
num_games = 1000
k_factor = 32


class Player:
    def __init__(self, name):
        self.name = name
        self.avg_skill = random.randint(1, 100)
        self.std_dev = 10
        self.elo = 1000

    def gen_game_score(self):
        return int(random.normalvariate(self.avg_skill, self.std_dev))

    def __str__(self):
        return 'Player {self.name}, {self.elo}, {self.avg_skill}, {self.std_dev}'.format(self=self)


def print_players(players):
    print("{:<10} {:<10} {:<10} {:<10}".format("Name", "Elo", "Avg Score", "Standard Deviation"))
    for player in players:
        print("{:<10} {:<10} {:<10} {:<10}".format(player.name, player.elo, player.avg_skill, player.std_dev))


def play_game(player_a, player_b):
    # print("GAME")
    # print("Player A: ", player_a)
    # print("Player B: ", player_b)

    # Calculate Expected Scores
    expected_a = 1 / (1 + pow(10, (player_b.elo - player_a.elo) / 400))
    expected_b = 1 - expected_a

    score_a = player_a.gen_game_score()
    score_b = player_b.gen_game_score()

    # print("Score A: ", score_a)
    # print("Score B: ", score_b)

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

    player_a.elo += int(rating_change_a)
    player_b.elo += int(rating_change_b)

    # print("Expected A: {:0.2f}".format(expected_a))
    # print("Expected B: {:0.2f}".format(expected_b))
    # print("Change A: {:0.2f}".format(rating_change_a))
    # print("Change B: {:0.2f}".format(rating_change_b))
    # print("Player A: ", player_a)
    # print("Player B: ", player_b)
    # print()


def main():
    players = []
    print("PLAYERS BEFORE PLAYING {} GAMES".format(num_games))
    for i in range(num_players):
        players.append(Player("Player {}".format(i + 1)))

    print_players(players)

    for i in range(num_games):
        # Pick Players
        player_a = players[random.randint(0, len(players) - 1)]
        player_b = players[random.randint(0, len(players) - 1)]
        while player_a.name == player_b.name:
            player_b = players[random.randint(0, len(players) - 1)]

        play_game(player_a, player_b)

    players.sort(key=lambda p: p.elo, reverse=True)
    print("\nPLAYERS AFTER PLAYING {} GAMES".format(num_games))
    print_players(players)


if __name__ == "__main__":
    main()
