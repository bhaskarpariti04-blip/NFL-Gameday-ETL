from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


REQUIRED_FIELDS = {
    "event_id", "game_id", "event_ts", "season", "week", "home_team", "away_team",
    "posteam", "qtr", "game_clock", "play_type", "yards_gained", "home_score", "away_score",
}
VALID_PLAY_TYPES = {"kickoff", "run", "pass", "punt", "field_goal", "extra_point", "timeout", "end_period"}


@dataclass(frozen=True)
class PlayEvent:
    event_id: str
    game_id: str
    event_ts: str
    season: int
    week: int
    home_team: str
    away_team: str
    posteam: str
    qtr: int
    game_clock: str
    play_type: str
    yards_gained: int
    home_score: int
    away_score: int
    description: str
    epa: float | None = None

    @property
    def game_status(self) -> str:
        return "FINAL" if self.qtr >= 5 else f"Q{self.qtr} {self.game_clock}"


def validate_and_parse(payload: dict[str, Any]) -> PlayEvent:
    missing = REQUIRED_FIELDS - payload.keys()
    if missing:
        raise ValueError("missing required fields: " + ", ".join(sorted(missing)))
    if payload["play_type"] not in VALID_PLAY_TYPES:
        raise ValueError(f"unsupported play_type: {payload['play_type']}")
    if not 1 <= int(payload["qtr"]) <= 5:
        raise ValueError("qtr must be from 1 to 5")
    datetime.fromisoformat(payload["event_ts"].replace("Z", "+00:00"))
    for field in ("home_team", "away_team", "posteam"):
        if not 2 <= len(str(payload[field])) <= 3:
            raise ValueError(f"{field} must be a 2- or 3-character NFL team code")
    if payload["posteam"] not in {payload["home_team"], payload["away_team"]}:
        raise ValueError("posteam must be one of the competing teams")
    return PlayEvent(
        event_id=str(payload["event_id"]), game_id=str(payload["game_id"]),
        event_ts=str(payload["event_ts"]), season=int(payload["season"]), week=int(payload["week"]),
        home_team=str(payload["home_team"]).upper(), away_team=str(payload["away_team"]).upper(),
        posteam=str(payload["posteam"]).upper(), qtr=int(payload["qtr"]), game_clock=str(payload["game_clock"]),
        play_type=str(payload["play_type"]), yards_gained=int(payload["yards_gained"]),
        home_score=int(payload["home_score"]), away_score=int(payload["away_score"]),
        description=str(payload.get("description", "")),
        epa=float(payload["epa"]) if payload.get("epa") is not None else None,
    )
