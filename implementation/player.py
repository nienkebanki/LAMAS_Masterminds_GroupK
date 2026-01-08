

class Player:

    def __init__(self,secret_code, name):
        self.secret_code = secret_code
        self.name = name
    def make_guess():
        raise NotImplementedError("Please implement this function in a child class")
    def give_feedback(self,guess):
        raise NotImplementedError("Please implement this function in a child class")

class LittleInfoPlayer(Player):

    def make_guess(self):
        return None
    def give_feedback(self,guess):
        return None
class OnePlayerStrategy(Player):

    def make_guess(self):
        return None
    def give_feedback(self,guess):
        return None
class NonRevealing(Player):

    def make_guess(self):
        return None
    def give_feedback(self,guess):
        return None
    