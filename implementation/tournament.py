from __future__ import annotations

import contextlib
import io
import random
from dataclasses import dataclass
from typing import Callable, List, Optional
import pandas as pd
import masterminds as mm


@dataclass(frozen=True)
class PlayerSpec:
    name: str
    factory: Callable[[int], mm.Player]


def _winner_label(game: mm.Game) -> str:
    """Return which agent(s) ended up knowing the opponent's code (in p1/p2 terms)."""
    p1_knows = (len(game.player1.possible_code_opponent) == 1)
    p2_knows = (len(game.player2.possible_code_opponent) == 1)
    if p1_knows and p2_knows:
        return "tie"
    if p1_knows:
        return "p1"
    if p2_knows:
        return "p2"
    return "failed"


def run_one_game(
    p1_spec: PlayerSpec,
    p2_spec: PlayerSpec,
    max_rounds: int = 60,
    seed: Optional[int] = None,
):
    """Run a single game, suppressing all internal prints, and return metrics + winner (p1/p2/both/none)."""
    if seed is not None:
        random.seed(seed)

    # fresh player instances per game
    p1 = p1_spec.factory(0)
    p2 = p2_spec.factory(1)

    # suppress noisy prints (secret codes, debug prints, etc.)
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        game = mm.Game(p1=p1, p2=p2)
        rounds, worlds_trace = game.simulate_game(max_rounds=max_rounds, verbose=False)

    winner_p = _winner_label(game)
    final_worlds = worlds_trace[-1] if worlds_trace else len(game.kripke.worlds)

    return {
        "rounds": rounds,
        "winner_p": winner_p,          # p1 / p2 / both / none
        "final_worlds": final_worlds,
    }


def main():
    # 5 lambda values spanning extremes + middle
    lambdas = [0.5, 1.0, 2.0, 5.0, 10.0]

    pool: List[PlayerSpec] = [
        PlayerSpec("GuessingFocused", lambda idx: mm.Guessing_Focused_Player(idx)),
        PlayerSpec("HidingFocused", lambda idx: mm.Hiding_Focused_Player(idx)),
        *[
            PlayerSpec(
                f"Balanced(lam={lam})",
                (lambda lam: (lambda idx: mm.Balanced_Player(idx, lambda_=lam)))(lam)
            )
            for lam in lambdas
        ],
    ]

    games_per_matchup = 10
    max_rounds = 60

    n = len(pool)
    unordered_pairs = n * (n - 1) // 2
    matchups_including_self = unordered_pairs + n
    total_games_expected = matchups_including_self * games_per_matchup

    rows = []
    matchup_id = 0
    game_counter = 0

    # round-robin -including- self-play: j starts from i
    for i in range(len(pool)):
        for j in range(i, len(pool)):
            A = pool[i]
            B = pool[j]
            matchup_id += 1

            for g in range(games_per_matchup):
                game_counter += 1
                swap = (g % 2 == 1)
                p1_spec, p2_spec = (B, A) if swap else (A, B)

                # Progress line
                print(
                    f"Game {game_counter}/{total_games_expected} | "
                    f"Matchup {matchup_id}/{matchups_including_self} | "
                    f"{A.name} vs {B.name} | game {g+1}/{games_per_matchup} | "
                    f"p1={p1_spec.name}, p2={p2_spec.name}"
                )

                metrics = run_one_game(p1_spec, p2_spec, max_rounds=max_rounds)
                
                print(f"  -> result: winner={metrics['winner_p']}, # rounds={metrics['rounds']}")

                # winner labels:
                # - if A != B, report winner in A/B terms as before
                # - if A == B (self-play), report winner as p1/p2/both/none
                if A.name != B.name:
                    if metrics["winner_p"] == "p1":
                        winner = "B" if swap else "A"
                    elif metrics["winner_p"] == "p2":
                        winner = "A" if swap else "B"
                    else:
                        winner = metrics["winner_p"]  # both/none
                else:
                    winner = metrics["winner_p"]

                rows.append({
                    "matchup_id": matchup_id,
                    "player_A": A.name,
                    "player_B": B.name,
                    "self_play": (A.name == B.name),
                    "game_in_matchup": g + 1,
                    "roles_swapped": swap,
                    "winner": winner,                 # A/B/both/none OR p1/p2/both/none for self-play
                    "winner_p": metrics["winner_p"],  # always in p1/p2 terms
                    "rounds": metrics["rounds"],
                    "final_worlds": metrics["final_worlds"],
                })

    df = pd.DataFrame(rows)

    out_csv = "tournament_results_selfplay.csv"
    df.to_csv(out_csv, index=False)

    print("\nDone.")
    print(f"Player pool size: {n}")
    print(f"Matchups (including self-play): {matchups_including_self}  (= C(n,2)+n)")
    print(f"Games per matchup: {games_per_matchup}")
    print(f"Total games: {len(df)} (expected {total_games_expected})")
    print(f"Saved CSV: {out_csv}")


if __name__ == "__main__":
    main()
