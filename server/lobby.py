"""Race lobby -- collects players and triggers races."""
import threading
import time
import uuid

MAX_PLAYERS = 20
MIN_PLAYERS = 4
LOBBY_TIMEOUT = 60.0


class Lobby:
    def __init__(self) -> None:
        self._players: list[dict] = []
        self._triggered = False
        self._race_id: str | None = None
        self._lock = threading.Lock()
        self._created_at = time.monotonic()
        self._fill_cars: list[dict] = []

    def join(self, car_config: dict) -> dict:
        """Add a player's car to the lobby. Returns lobby status."""
        with self._lock:
            if self._triggered:
                raise LobbyClosedError("Lobby already triggered")
            if len(self._players) >= MAX_PLAYERS:
                raise LobbyFullError("Lobby is full")
            for p in self._players:
                if p["player_id"] == car_config["player_id"]:
                    raise LobbyDuplicateError("Already in lobby")
            self._players.append(car_config)
            return self.status()

    def status(self) -> dict:
        """Current lobby state."""
        elapsed = time.monotonic() - self._created_at
        remaining = max(0.0, LOBBY_TIMEOUT - elapsed)
        return {
            "player_count": len(self._players),
            "max_players": MAX_PLAYERS,
            "time_remaining": round(remaining, 1),
            "triggered": self._triggered,
            "race_id": self._race_id,
            "player_names": [p["name"] for p in self._players],
        }

    def check_trigger(self) -> bool:
        """Check if lobby should trigger (timer expired or full)."""
        with self._lock:
            if self._triggered:
                return True
            elapsed = time.monotonic() - self._created_at
            if elapsed >= LOBBY_TIMEOUT or len(self._players) >= MAX_PLAYERS:
                self._trigger()
                return True
            return False

    def _trigger(self) -> None:
        """Fire the lobby -- generate race_id."""
        self._triggered = True
        self._race_id = str(uuid.uuid4())

    def get_all_cars(self) -> list[dict]:
        """Get all cars (players + AI fill). Only valid after trigger."""
        return self._players + self._fill_cars

    def set_fill_cars(self, fill: list[dict]) -> None:
        """Set AI fill cars (called by the route/orchestrator)."""
        self._fill_cars = fill

    @property
    def triggered(self) -> bool:
        return self._triggered

    @property
    def race_id(self) -> str | None:
        return self._race_id


class LobbyClosedError(Exception):
    pass


class LobbyFullError(Exception):
    pass


class LobbyDuplicateError(Exception):
    pass
