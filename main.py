import random

num_players = 1000
team_size = 1
num_games = 100000
k_factor = 32

players = []
queued = []
players_unqueued = []
full_teams = []

ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"]
ranked_players = [[], [], [], [], []]
playing_elo_range = 200

ranks_upper_bound = 1600
ranks_size = ranks_upper_bound / (len(ranks) - 2)


class Player:
    def __init__(self, name):
        self.name = name
        self.avg_skill = random.randint(1, 100)
        self.std_dev = 10  # random.randint(1, 20)
        self.elo = 1000
        self.games_played = 0
        self.rank = 0
        ranked_players[0].append(self)
        self.update_rank(0)

    def gen_game_score(self):
        self.games_played += 1
        return int(random.normalvariate(self.avg_skill, self.std_dev))

    def update_rank(self, elo_change):
        self.elo += elo_change
        ranked_players[self.rank].remove(self)

        if self.elo > ranks_upper_bound:
            self.rank = 4
        else:
            for i in range(len(ranks)):
                if self.elo < (i * ranks_size):
                    self.rank = i
                    break
        ranked_players[self.rank].append(self)

    def __str__(self):
        return 'Player {self.name}, {self.elo}, {self.avg_skill}, {self.std_dev}, {self.games_played}'.format(self=self)


class Team:
    def __init__(self, *players):
        self.players = list(players)
        self.elo = 0
        self.calculate_avg_elo()

    def add_player(self, player):
        self.players.append(player)
        self.calculate_avg_elo()

    def calculate_avg_elo(self):
        elo = 0
        for player in self.players:
            elo += player.elo
        self.elo = elo / len(self.players)

    def __iadd__(self, other):
        self.players.extend(other.players)
        self.calculate_avg_elo()

    def __contains__(self, item):
        return item in self.players

    def __str__(self):
        s = ""
        for player in self.players:
            s += "{:>10} {:>4}, ".format(ranks[player.rank], str(player.elo))
        s += str(self.elo)
        return s

    def __iter__(self):
        return self.players.__iter__()

    def __len__(self):
        return len(self.players)


class Game:
    def __init__(self, team_a, team_b):
        self.team_a = team_a
        self.team_b = team_b
        #print("Game Found")
        #print(team_a)
        #print(team_b)
        #print()

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
            player.update_rank(int(rating_change_a))
        for player in self.team_b:
            player.update_rank(int(rating_change_b))


def print_players():
    print(
        "{:>10} {:>15} {:>10} {:>10} {:>10} {:>10}".format("Rank", "Name", "Elo", "Avg Score", "Sigma", "Games Played"))
    for i, player in enumerate(players):
        print("{:>10} {:>15} {:>10} {:>10} {:>10} {:>10}".format(i, player.name, player.elo, player.avg_skill,
                                                                 player.std_dev,
                                                                 player.games_played))


'''
def create_team(name, party=Team("Empty")):
    team = Team(name)
    for player in party:
        team.add_player(player)
        players.remove(player)

    while len(team) < team_size:
        player = players[random.randint(0, len(players) - 1)]
        team.add_player(player)
        players.remove(player)
    return team
'''


def queue(team):
    queued.append(team)


def match_make(team):
    if len(team) == team_size:
        full_teams.append(team)
    else:
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
    full_team_a = None
    full_team_b = None
    for i, full_team in enumerate(full_teams):
        if i + 1 < len(full_teams) and abs(full_team.elo - full_teams[i + 1].elo) < 100:
            full_team_a = full_team
            full_team_b = full_teams[i + 1]

    if full_team_a is not None and full_team_b is not None:
        game = Game(full_team_a, full_team_b)
        game.play()
        full_teams.remove(full_team_a)
        full_teams.remove(full_team_b)

        for player in full_team_a:
            players_unqueued.append(player)
        for player in full_team_b:
            players_unqueued.append(player)
        return 1
    return 0


def valid_team_merge(team_a, team_b):
    if len(team_a) + len(team_b) <= team_size:  # If team is within size
        if abs(team_a.elo - team_b.elo) < playing_elo_range:  # If elo within range
            return True
    return False


def main():
    # Create Players
    for i in range(num_players):
        # Create Player
        player = Player("Player {}".format(i + 1))
        players.append(player)
        players_unqueued.append(player)

    for player in players_unqueued:
        match_make(Team(player))
        players_unqueued.remove(player)

    game_count = 0
    while game_count < num_games:
        games_played = check_for_games()
        game_count += games_played
        print("Games Played = ", game_count)

        if random.random() < 0.1 or games_played == 0:
            if games_played == 0 and len(players_unqueued) == 0:
                print("FAILED")
            for player in players_unqueued:
                match_make(Team(player))
                players_unqueued.remove(player)

    '''
    shroud = Player("-=SHROUD=-")
    shroud.avg_skill = 90
    shroud.std_dev = 5
    players.append(shroud)
    party = Team("Team S")
    party.add_player(shroud)

    for i in range(400):
        team_a, team_b = match_make(party)
        game = Game(team_a, team_b)
        game.play()
    '''
    players.sort(key=lambda p: p.elo, reverse=True)
    print("\nPLAYERS AFTER PLAYING {} GAMES".format(num_games))
    print_players()


if __name__ == "__main__":
    main()
