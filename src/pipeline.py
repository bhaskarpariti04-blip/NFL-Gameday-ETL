from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .contracts import validate_and_parse
from .warehouse import Warehouse


def run(feed: str, database: str, reset: bool = False, replay_delay: float = 0.0) -> dict[str, int]:
    warehouse = Warehouse(database)
    try:
        if reset:
            warehouse.reset()
        for line_no, line in enumerate(Path(feed).read_text().splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                event = validate_and_parse(payload)
                warehouse.load(event, payload)
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                warehouse.reject({"line": line_no, "value": line}, str(exc))
            if replay_delay:
                time.sleep(replay_delay)
        return warehouse.summary()
    finally:
        warehouse.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the NFL game-day ETL pipeline")
    parser.add_argument("--feed", required=True, help="Path to a JSONL event feed")
    parser.add_argument("--database", default="state/gameday.db")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--replay-delay", type=float, default=0.0)
    args = parser.parse_args()
    print(run(args.feed, args.database, args.reset, args.replay_delay))
