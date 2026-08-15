from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect


_NOTIFICATIONS_FILE = Path.home() / ".creator" / "notifications.json"


def _load_config() -> dict:
    try:
        return json.loads(_NOTIFICATIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"enabled": True, "sounds": True}


def save_config(config: dict) -> None:
    _NOTIFICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _NOTIFICATIONS_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def notifications_enabled() -> bool:
    return _load_config().get("enabled", True)


def sounds_enabled() -> bool:
    return _load_config().get("sounds", True)


def set_notifications_enabled(value: bool) -> None:
    config = _load_config()
    config["enabled"] = value
    save_config(config)


def set_sounds_enabled(value: bool) -> None:
    config = _load_config()
    config["sounds"] = value
    save_config(config)


def notify_complete(parent=None) -> None:
    if not notifications_enabled():
        return
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon

    app = QApplication.instance()
    if app is None:
        return

    tray = QSystemTrayIcon(parent)
    tray.showMessage(
        "Creator",
        "Your project has finished running.",
        QSystemTrayIcon.MessageIcon.Information,
        3000,
    )


def play_sound(event: str = "done") -> None:
    if not sounds_enabled():
        return
    try:
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(""))
        effect.setVolume(0.5)
    except Exception:
        pass
