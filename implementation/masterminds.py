from __future__ import annotations
from mlsolver.kripke import KripkeStructure, World
from mlsolver.formula import And, Or, Atom
from more_itertools import distinct_permutations as dp
from itertools import product
import math
import random
from collections import defaultdict
from typing import List, Tuple, Dict, Iterable, Optional


CODES = ["b", "r", "g", "y", "p"]   # colours
AGENTS = ["i", "j"]
CODE_LEN = 3


def H(candidate_set: Iterable) -> float:
    """Hartley entropy (uniform): log2(|S|)."""
    n = len(list(candidate_set)) if not isinstance(candidate_set, (list, set, tuple)) else len(candidate_set)
    if n <= 1:
        return 0.0
    return math.log2(n)


def black(g: Tuple[str, ...], c: Tuple[str, ...]) -> int:
    """# correct colour in correct position."""
    return sum(gi == ci for gi, ci in zip(g, c))


def white(g: Tuple[str, ...], c: Tuple[str, ...]) -> int:
    """# correct colours but wrong position (standard Mastermind, no repeats)."""
    b = black(g, c)
    return len(set(g) & set(c)) - b


def feedback(g: Tuple[str, ...], c: Tuple[str, ...]) -> Tuple[int, int]:
    return (black(g, c), white(g, c))


class Player:
    """
    Keeps:
      - Si: possible_code_opponent  (opponent candidates)
      - Ti: possible_code_own       (what opponent might think my code is, as modelled by me)
    """

    def __init__(self, idx: int):
        self.idx = idx

        codes_list = list(dp(CODES, r=CODE_LEN))  # tuples like ('b','g','p')
        self.secret_code: Tuple[str, ...] = random.choice(codes_list)

        print(f"Agent {AGENTS[idx]} secret code: {''.join(self.secret_code)}")

        self.possible_code_opponent: List[Tuple[str, ...]] = codes_list[:]  # Si
        self.possible_code_own: List[Tuple[str, ...]] = codes_list[:]       # Ti

    def expected_IG(self, guess: Tuple[str, ...]) -> float:
        """
        IG(g) = H(Si) - E_f[ H(Si^{g,f}) ]
        where f is feedback(guess, c) over c in Si with uniform prior.
        """
        buckets: Dict[Tuple[int, int], List[Tuple[str, ...]]] = defaultdict(list)
        for c in self.possible_code_opponent:
            buckets[feedback(guess, c)].append(c)

        H_before = math.log2(len(self.possible_code_opponent)) if len(self.possible_code_opponent) > 1 else 0.0
        H_after = 0.0
        n = len(self.possible_code_opponent)
        for codes in buckets.values():
            p = len(codes) / n
            H_after += p * (math.log2(len(codes)) if len(codes) > 1 else 0.0)

        return H_before - H_after

    def self_information_leak(self, guess: Tuple[str, ...]) -> float:
        """
        Immediate leak caused by -my- guess:
        the self-feedback (guess vs my secret) is public,
        so it shrinks Ti = possible_code_own.
        IL(g) = log2|Ti| - log2|Ti'|
        """
        if len(self.possible_code_own) <= 1:
            return 0.0

        fb_self = feedback(guess, self.secret_code)
        T_new = [c for c in self.possible_code_own if feedback(guess, c) == fb_self]

        before = math.log2(len(self.possible_code_own)) if len(self.possible_code_own) > 1 else 0.0
        after = math.log2(len(T_new)) if len(T_new) > 1 else 0.0
        return before - after

    def get_feedback(self, guess: Tuple[str, ...], c: Tuple[str, ...]) -> Tuple[int, int]:
        return feedback(guess, c)

    def make_guess(self) -> Tuple[str, ...]:
        raise NotImplementedError

    def update_knowledge(
        self,
        guess: Tuple[str, ...],
        feedback_opp: Tuple[int, int],
        feedback_self: Tuple[int, int],
    ):
        """
        Update:
          - Si with feedback_opp (guess vs opponent)
          - Ti with feedback_self (guess vs my code), since it is public
        and return a formula capturing the surviving opponent candidates for this agent
        (used for PAL update on the Kripke model).
        """
        # update Si
        new_opp: List[Tuple[str, ...]] = []
        formula = None

        for c in self.possible_code_opponent:
            if feedback(guess, c) == feedback_opp:
                new_opp.append(c)
                atom = Atom("".join(c) + AGENTS[self.idx])
                formula = atom if formula is None else Or(formula, atom)

        self.possible_code_opponent = new_opp

        # update Ti (public self-feedback)
        self.possible_code_own = [
            c for c in self.possible_code_own
            if feedback(guess, c) == feedback_self
        ]

        return formula


class Guessing_Focused_Player(Player):
    """Maximise expected information gain about opponent (ignore self-leak)."""

    def make_guess(self) -> Tuple[str, ...]:
        best_g = None
        best_score = -1e18
        for g in self.possible_code_opponent:
            score = self.expected_IG(g)
            if score > best_score:
                best_score = score
                best_g = g
        # fallback (should never happen)
        return best_g if best_g is not None else random.choice(self.possible_code_opponent)


class Hiding_Focused_Player(Player):
    """
    Minimise immediate self-leak IL(g) caused by self-feedback of own guess.
    Tie-breaker: pick higher IG (prevents stalling).
    """

    def make_guess(self) -> Tuple[str, ...]:
        best_g = None
        best_leak = float("inf")
        best_ig = -1e18

        for g in self.possible_code_opponent:
            leak = self.self_information_leak(g)
            ig = self.expected_IG(g)
            if leak < best_leak or (leak == best_leak and ig > best_ig):
                best_leak = leak
                best_ig = ig
                best_g = g

        return best_g if best_g is not None else random.choice(self.possible_code_opponent)


class Balanced_Player(Player):
    """
    One-parameter balanced strategy:
      U(g) = IG(g) - lambda_ * IL(g)
    where IL(g) is the immediate self-leak from public self-feedback.
    """

    def __init__(self, idx: int, lambda_: float = 1.0):
        super().__init__(idx)
        self.lambda_ = float(lambda_)

    def make_guess(self) -> Tuple[str, ...]:
        best_g = None
        best_score = -1e18

        for g in self.possible_code_opponent:
            ig = self.expected_IG(g)
            il = self.self_information_leak(g)
            score = ig - self.lambda_ * il
            if score > best_score:
                best_score = score
                best_g = g

        return best_g if best_g is not None else random.choice(self.possible_code_opponent)


class Game:
    def __init__(self, p1: Optional[Player] = None, p2: Optional[Player] = None):
        # pick strategies here
        self.player1 = p1 if p1 is not None else Guessing_Focused_Player(0)
        self.player2 = p2 if p2 is not None else Guessing_Focused_Player(1)

        # build world space: (codeA, codeB)
        all_codes = ["".join(x) for x in dp(CODES, r=CODE_LEN)]
        pairs = product(all_codes, all_codes)

        worlds = [
            World("".join(x), {r + AGENTS[i]: True for (i, r) in enumerate(x)})
            for x in pairs
        ]

        relations = {
            AGENTS[0]: {
                (a.name, b.name)
                for a in worlds
                for b in worlds
                if a.name[:CODE_LEN] == b.name[:CODE_LEN]
            },
            AGENTS[1]: {
                (a.name, b.name)
                for a in worlds
                for b in worlds
                if a.name[-CODE_LEN:] == b.name[-CODE_LEN:]
            },
        }
        self.kripke = KripkeStructure(worlds, relations)

    def there_is_a_winner(self) -> bool:
        return (len(self.player1.possible_code_opponent) == 1) or (len(self.player2.possible_code_opponent) == 1)

    def play_round(self) -> int:
        """
        One full round = i moves and j moves.
        Each move uses one guess g and produces -two- public feedbacks:
          - feedback(g, opponent_code)
          - feedback(g, own_code)
        Both agents update on the same public pair.
        """

        # i's move 
        g1 = self.player1.make_guess()
        fb1_about_j = feedback(g1, self.player2.secret_code)   # g1 vs j
        fb1_about_i = feedback(g1, self.player1.secret_code)   # g1 vs i (public)

        ann1_i = self.player1.update_knowledge(g1, fb1_about_j, fb1_about_i)
        ann1_j = self.player2.update_knowledge(g1, fb1_about_i, fb1_about_j)

        # j's move
        g2 = self.player2.make_guess()
        fb2_about_i = feedback(g2, self.player1.secret_code)   # g2 vs i
        fb2_about_j = feedback(g2, self.player2.secret_code)   # g2 vs j (public)

        ann2_j = self.player2.update_knowledge(g2, fb2_about_i, fb2_about_j)
        ann2_i = self.player1.update_knowledge(g2, fb2_about_j, fb2_about_i)

        # public announcement update on the Kripke model
        announcement = And(And(ann1_i, ann1_j), And(ann2_i, ann2_j))
        self.kripke = self.kripke.solve(announcement)
        return len(self.kripke.worlds)

    def simulate_game(self, max_rounds: int = 10, verbose: bool = True):
        worlds_left = [len(self.kripke.worlds)]

        for r in range(1, max_rounds + 1):
            w = self.play_round()
            worlds_left.append(w)

            if verbose:
                print(f"Round {r}: worlds={w} |Si|={len(self.player1.possible_code_opponent)} "
                      f"|Ti|={len(self.player1.possible_code_own)} "
                      f"|Sj|={len(self.player2.possible_code_opponent)} "
                      f"|Tj|={len(self.player2.possible_code_own)}")

            if self.there_is_a_winner():
                if verbose:
                    if len(self.player1.possible_code_opponent) == 1:
                        print(f"Epistemic win: {AGENTS[0]} knows {AGENTS[1]}'s code.")
                    if len(self.player2.possible_code_opponent) == 1:
                        print(f"Epistemic win: {AGENTS[1]} knows {AGENTS[0]}'s code.")
                return r, worlds_left

        return max_rounds, worlds_left
