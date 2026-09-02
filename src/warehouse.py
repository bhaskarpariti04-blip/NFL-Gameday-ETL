from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .contracts import PlayEvent


SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_events (
  event_id TEXT PRIMARY KEY, ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rejected_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reason TEXT NOT NULL, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS play_facts (
  event_id TEXT PRIMARY KEY, game_id TEXT NOT NULL, event_ts TEXT NOT NULL, season INTEGER NOT NULL,
  week INTEGER NOT NULL, home_team TEXT NOT NULL, away_team TEXT NOT NULL, posteam TEXT NOT NULL,
  qtr INTEGER NOT NULL, game_clock TEXT NOT NULL, play_type TEXT NOT NULL, yards_gained INTEGER NOT NULL,
  home_score INTEGER NOT NULL, away_score INTEGER NOT NULL, description TEXT NOT NULL, epa REAL,
  game_status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS game_live_metrics (
  game_id TEXT PRIMARY KEY, season INTEGER NOT NULL, week INTEGER NOT NULL, home_team TEXT NOT NULL,
  away_team TEXT NOT NULL, home_score INTEGER NOT NULL, away_score INTEGER NOT NULL, game_status TEXT NOT NULL,
  last_event_ts TEXT NOT NULL, total_plays INTEGER NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS team_live_metrics (
  game_id TEXT NOT NULL, team TEXT NOT NULL, plays INTEGER NOT NULL, yards INTEGER NOT NULL,
  epa REAL NOT NULL, PRIMARY KEY (game_id, team)
);
"""


class Warehouse:
    def __init__(self, database: str):
        Path(database).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(database)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def reset(self) -> None:
        self.conn.executescript("DELETE FROM raw_events; DELETE FROM rejected_events; DELETE FROM play_facts; DELETE FROM game_live_metrics; DELETE FROM team_live_metrics;")
        self.conn.commit()

    def reject(self, payload: object, reason: str) -> None:
        self.conn.execute("INSERT INTO rejected_events(reason, payload) VALUES (?, ?)", (reason, json.dumps(payload)))
        self.conn.commit()

    def load(self, event: PlayEvent, payload: dict) -> bool:
        """Atomically load a play and update serving aggregates. Returns False if duplicate."""
        with self.conn:
            inserted = self.conn.execute("INSERT OR IGNORE INTO raw_events(event_id, payload) VALUES (?, ?)", (event.event_id, json.dumps(payload))).rowcount
            if not inserted:
                return False
            self.conn.execute("""INSERT INTO play_facts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (event.event_id, event.game_id, event.event_ts, event.season, event.week, event.home_team, event.away_team,
                 event.posteam, event.qtr, event.game_clock, event.play_type, event.yards_gained, event.home_score,
                 event.away_score, event.description, event.epa, event.game_status))
            self.conn.execute("""INSERT INTO game_live_metrics(game_id, season, week, home_team, away_team, home_score, away_score, game_status, last_event_ts, total_plays)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(game_id) DO UPDATE SET home_score=excluded.home_score, away_score=excluded.away_score,
                game_status=excluded.game_status, last_event_ts=excluded.last_event_ts, total_plays=total_plays+1, updated_at=CURRENT_TIMESTAMP""",
                (event.game_id, event.season, event.week, event.home_team, event.away_team, event.home_score, event.away_score, event.game_status, event.event_ts))
            self.conn.execute("""INSERT INTO team_live_metrics(game_id, team, plays, yards, epa) VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(game_id, team) DO UPDATE SET plays=plays+1, yards=yards+excluded.yards, epa=epa+excluded.epa""",
                (event.game_id, event.posteam, event.yards_gained, event.epa or 0.0))
        return True

    def summary(self) -> dict[str, int]:
        return {name: self.conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in ("raw_events", "play_facts", "rejected_events", "game_live_metrics")}

    def scoreboard(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM game_live_metrics ORDER BY last_event_ts DESC").fetchall()
