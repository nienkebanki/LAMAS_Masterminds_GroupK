from mlsolver.kripke import *
from mlsolver.formula import *
from more_itertools import distinct_permutations as dp
from itertools import product
import networkx as nx
import matplotlib.pyplot as plt
from functools import reduce
import pygraphviz
import sys
import string
import math
import random

CODES =['b','r','g']
AGENTS = string.ascii_lowercase
CODE_LEN = 2

def calculate_entropy(candidate_set):
        if not candidate_set: return 0
        return math.log2(len(candidate_set))


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
    

    # def plot_knowledge(self, layout="neato", pos=None):
    #     G = nx.DiGraph()
    #     nodes = self.kripke.worlds.keys()
    #     # Edges drawn are given by the union of all agents' relations, with the labels depending on which agents' relations
    #     # the edge comes from.
    #     edges     = [(w, v, {'label': ''.join([a for a in AGENTS[:2] if (w,v) in self.kripke.relations[a]])})
    #                  for (w, v) in reduce(lambda x, y : x.union(y), self.kripke.relations.values()) if w != v]
    #     G.add_nodes_from(nodes)
    #     G.add_edges_from(edges) 
    #     if pos is None:
    #         pos = nx.nx_agraph.graphviz_layout(G, layout)
    #     else:
    #         # Reuse positions for the appropriate worlds if possible.
    #         pos = {a: pos[a1] for a in nodes for a1 in pos.keys() if a.startswith(a1)}
    #     # Use newlines instead of commas in node labels to avoid them being too long
    #     nodenames = {n: "\n".join(n.split(",")) for n in G.nodes}
    #     numlines = list(G.nodes.keys())[0].count(",")+1
    #     # Adjust font size based on how large the node label will be
    #     node_size = 2500*math.sqrt(numlines)
    #     font_size = round(node_size / 40 / max(numlines*2.1+.4,0))
    #     nx.draw(G, pos, with_labels=True, labels=nodenames, node_size=node_size, font_size=font_size, node_color="white", edgecolors="black")
    #     if (len(edges) < 200):
    #         # Draw edge labels if it's reasonable to do so
    #         nx.draw_networkx_edge_labels(G, pos, {(w,v):l for (w,v,l) in G.edges(data="label")}, font_size=20)
    #     plt.savefig("plot.png") 
    #     return pos
   
    def winner(self):
        if self.player1.possible_code_opponent == 1:
            return self.player1
        if self.player2.possible_code_opponent == 1:
            return self.player2
        return None
  
        
        
    def play_round(self):
        guess1 = self.player1.make_guess()
        print(f'Player a makes guess {guess1}')
        feedback1 = self.player2.get_feedback(guess1,self.player2.secret_code)
        guess2 = self.player2.make_guess()
        feedback2 = self.player1.get_feedback(guess2,self.player1.secret_code)
        announcement1 = self.player1.update_knowledge(guess1,feedback1,feedback2)
        announcement2 = self.player2.update_knowledge(guess2,feedback2,feedback1)
        announcement = And(announcement1,announcement2)
        print("solving for one")
        print(announcement)
        print(len(self.kripke.worlds))
        self.kripke = self.kripke.solve(announcement)
        print(len(self.kripke.worlds))
            



class Player:

    def __init__(self, idx):
        self.idx = idx
        codes = dp(CODES,r=CODE_LEN)
        codes_list = list(codes) 
        self.secret_code = random.choice(codes_list)
        print(f'Agent{AGENTS[idx]} secret code: {self.secret_code}')
        self.possible_code_own = codes_list
        self.possible_code_opponent = codes_list
    def make_guess():
        raise NotImplementedError("Please implement this function in a child class")
    def get_feedback(self,guess):
        raise NotImplementedError("Please implement this function in a child class")
    def update_knowledge(self,feedback):
        raise NotImplementedError("Please implement this function in a child class")

class Guessing_Focused_Player(Player):
    def black(self,g, c):
        return sum(gi == ci for gi, ci in zip(g, c))
    def white(self,g,c):
        b = self.black(g,c)
        return len(set(g) & set(c)) - b
    def make_guess(self):
        return random.choice(self.possible_code_opponent)
    def get_feedback(self,guess,c):
        return (self.black(guess,c), self.white(guess,c))
    def update_knowledge(self,guess,feedback_opp,feedback_self):
        new_possible_code = []
        formula = None 
        for c in self.possible_code_opponent:
            
            if self.get_feedback(guess, c) == feedback_opp:
                new_possible_code.append(c)
                if formula is None:
                    formula = Atom(''.join(c) + AGENTS[self.idx])
                else:
                    formula = Or(formula,Atom(''.join(c) + AGENTS[self.idx]))
        print(feedback_opp)
        self.possible_code_own = [
            c for c in self.possible_code_own 
            if self.get_feedback(guess, c) == feedback_self
        ]
        return formula
class Hiding_Focused_Player(Player):

    def make_guess(self):
        return guess
    def get_feedback(self,guess):
        return None
    def update_feedback(self,feedback):
        return
class Balanced_Player(Player):

    def make_guess(self):
        return guess
    def get_feedback(self,guess):
        return None
    def update_feedback(self,feedback):
        return    




#     def has_ended(self):
#         return self.winner() is not None
    
#     def apply_public_announcement(self):
#         return

if __name__ == "__main__":

    print("==> starting game")
    g = Game()
    print("==> one round")
    g.play_round()
   