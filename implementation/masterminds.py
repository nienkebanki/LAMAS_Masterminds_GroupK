import random

from player import Player

CODES =['b','r','y','g','p']

class Game:
    def __init__(self):

        # random.seed(9)
        self.players = []
        for name in list(range(2)):
            p = Player(name,('b','r','y'))

        self.current_player_idx = 0

    def game_str(self):
        return 'GAME STATE:\n' + \
               '\n'.join(p.game_str() for p in self.players) + \
               '\n'

    def play_round(self, view=None):
        if not self.has_ended():
            self.players[self.current_player_idx].play_round(self, view=view)
            self.next_player()

    def next_player(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)



    def winner(self):
        player1 = self.players[0]
        player2 = self.players[1]
        if player1.guess == player2.secret_code:
            return player1
        if player2.guess == player1.secret_code:
            return player2
        return None

    def has_ended(self):
        return self.winner() is not None
    
    def apply_public_announcement(self):
        return