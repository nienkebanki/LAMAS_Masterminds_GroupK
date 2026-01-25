from mlsolver.kripke import *
from mlsolver.formula import *
from more_itertools import distinct_permutations as dp
from itertools import product
import math
import random
from collections import defaultdict
 

CODES =['b','r','g','y','p']
AGENTS = ['i','j']
CODE_LEN = 3

def H(candidate_set):
        if not candidate_set: return 0
        return math.log2(len(candidate_set))

def black(self,g, c):
    return sum(gi == ci for gi, ci in zip(g, c))
def white(self,g,c):
    b = black(g,c)
    return len(set(g) & set(c)) - b
def feedback(guess,c):
    return (black(guess,c), white(guess,c))


class Game:
    def __init__(self):
        #Worlds are given by the distinct permutation of the two codes 
        self.player1 = Guessing_Focused_Player(0)
        self.player2 = Guessing_Focused_Player(1)
        
        a_possible_codes = []
        b_possible_code = []
        for x in dp(CODES,r=CODE_LEN):
            name = ''.join(x)
            a_possible_codes.append(name)
            b_possible_code.append(name)
        pairs = product(a_possible_codes, b_possible_code)
        worlds = [World(''.join(x), {r + AGENTS[i]: True for (i, r) in enumerate(x)}) for x in pairs]
        relations = {
            AGENTS[0]: set(
                (a.name, b.name)
                for a in worlds
                for b in worlds
                if a.name[:CODE_LEN] == b.name[:CODE_LEN]   # first 3 letters
            ),
            AGENTS[1]: set(
                (a.name, b.name)
                for a in worlds
                for b in worlds
                if a.name[-CODE_LEN:] == b.name[-CODE_LEN:] # last 3 letters
            )
        }
        self.kripke = KripkeStructure(worlds, relations)
    

   
    def there_is_a_winner(self):
        if self.player1.possible_code_opponent == 1:
            print(f'Agent{AGENTS[self.player1.idx]} secret code: {self.secret_code}')
            return True
        if self.player2.possible_code_opponent == 1:
            print(f'Agent{AGENTS[self.player1.idx]} secret code: {self.secret_code}')
            return True
        return False
  
        
        
    def play_round(self):
        guess1 = self.player1.make_guess()
        feedback1 = self.player2.get_feedback(guess1,self.player2.secret_code)
        guess2 = self.player2.make_guess()
        feedback2 = self.player1.get_feedback(guess2,self.player1.secret_code)
        announcement1 = self.player1.update_knowledge(guess1,feedback1,feedback2)
        announcement2 = self.player2.update_knowledge(guess2,feedback2,feedback1)
        announcement = And(announcement1,announcement2)
        self.kripke = self.kripke.solve(announcement)
        return len(self.kripke.worlds)

    def simulate_game(self):
        max_rounds = 60
        round_leakeage = [len(self.kripke.worlds)]
        for round_num in range(1, max_rounds + 1):
            
            leak = self.play_round()
            round_leakeage.append(leak)
            if self.there_is_a_winner():           
                break
        return round_num
class Player:
    def __init__(self, idx):
        self.idx = idx
        codes = dp(CODES,r=CODE_LEN)
        codes_list = list(codes) 
        self.secret_code = random.choice(codes_list)
        print(f'Agent{AGENTS[idx]} secret code: {self.secret_code}')
        self.possible_code_own = codes_list
        self.possible_code_opponent = codes_list
    def expected_IG(self, guess):
        buckets = defaultdict(set)

        for c in self.possible_code_opponent:
            fb = feedback(guess, c)
            buckets[fb].add(c)

        H_before = H(self.possible_code_opponent)
        H_after = 0

        for fb_set in buckets.values():
            p = len(fb_set) / len(self.possible_code_opponent)
            H_after += p * H(fb_set)
        return H_before - H_after
    def expected_IL(self,opponent_model_of_you, guess, fb):
        T = opponent_model_of_you
        T_new = {
            c for c in T
            if feedback(guess, c) == fb
        }      
        return H(T) - H(T_new)
    def get_feedback(self,guess,c):
        raise NotImplementedError("Please implement this function in a child class")
    def make_guess(self):
        raise NotImplementedError("Please implement this function in a child class")
    def update_knowledge(self,guess,feedback_opp,feedback_self):
        new_possible_code = []
        formula = None 
        for c in self.possible_code_opponent:
            
            if feedback(guess, c) == feedback_opp:
                new_possible_code.append(c)
                if formula is None:
                    formula = Atom(''.join(c) + AGENTS[self.idx])
                else:
                    formula = Or(formula,Atom(''.join(c) + AGENTS[self.idx]))
        self.possible_code_opponent = new_possible_code
        self.possible_code_own = [
            c for c in self.possible_code_own 
            if feedback(guess, c) == feedback_self
        ]
        return formula
    

class Guessing_Focused_Player(Player):
    def make_guess(self):
        best_g = None
        best_score = -1
        for g in self.possible_code_opponent:
            score = self.expected_IG(g)
            if score > best_score:
                best_score = score
                best_g = g
        return best_g
    def get_feedback(self, guess, c):
        return feedback(guess,c)
    
class Hiding_Focused_Player(Player):
    def make_guess(self):
        return random.choice(self.possible_code_opponent)
    def get_feedback(self, guess, c):
        best_feedback = None
        best_score  = math.inf
        for g in self.possible_code_own:
            if score < best_score:
                best_score = score
                best_g = g

class Balanced_Player(Player):


    def __init__(self, idx, alpha=1.0, beta=1.0):
        super().__init__(idx)
        self.alpha = alpha
        self.beta = beta

    def make_guess(self):
        best_g = None
        best_score = -float("inf")

        for g in self.possible_code_opponent:
            ig = self.expected_IG(g)
            il = self.expected_IL(g)

            score = self.alpha * ig - self.beta * il

            if score > best_score:
                best_score = score
                best_g = g

        return best_g



#     def has_ended(self):
#         return self.winner() is not None
    
#     def apply_public_announcement(self):
#         return


if __name__ == "__main__":

    print("==> starting game")
    g = Game()
    print("==> one round")
    g.play_round()
   