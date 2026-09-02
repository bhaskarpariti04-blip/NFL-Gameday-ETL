from __future__ import annotations

import argparse

from .warehouse import Warehouse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print current NFL game-day scoreboard")
    parser.add_argument("--database", default="state/gameday.db")
    args = parser.parse_args()
    warehouse = Warehouse(args.database)
    try:
        for game in warehouse.scoreboard():
            print(f"{game['away_team']} {game['away_score']} @ {game['home_team']} {game['home_score']}  |  {game['game_status']}  |  {game['total_plays']} events")
    finally:
        warehouse.close()
