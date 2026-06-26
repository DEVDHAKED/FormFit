import json
from pathlib import Path
from typing import Any


SETTINGS_FILE = Path.home() / ".govform_assistant" / "settings.json"

_DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "last_output_dir": str(Path.home() / "Desktop"),
    "default_dpi": 96,
    "last_preset": "ssc",
    "window_width": 1100,
    "window_height": 750,
}


class Settings:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        for key, value in _DEFAULTS.items():
            self._data.setdefault(key, value)

    def _save(self) -> None:
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._save()

    @property
    def theme(self) -> str:
        return self._data.get("theme", "dark")

    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)

    @property
    def last_output_dir(self) -> str:
        p = self._data.get("last_output_dir", str(Path.home() / "Desktop"))
        if not Path(p).exists():
            return str(Path.home() / "Desktop")
        return p

    @last_output_dir.setter
    def last_output_dir(self, value: str) -> None:
        self.set("last_output_dir", value)

    @property
    def default_dpi(self) -> int:
        return int(self._data.get("default_dpi", 96))

    @default_dpi.setter
    def default_dpi(self, value: int) -> None:
        self.set("default_dpi", int(value))

    @property
    def last_preset(self) -> str:
        return self._data.get("last_preset", "ssc")

    @last_preset.setter
    def last_preset(self, value: str) -> None:
        self.set("last_preset", value)


settings = Settings()
