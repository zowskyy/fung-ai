from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

import app.notifications as notifications
from app.notifications import (
    notifications_enabled,
    set_notifications_enabled,
)


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_config_toggle(app):
    set_notifications_enabled(False)
    assert notifications_enabled() is False
    set_notifications_enabled(True)
    assert notifications_enabled() is True


def test_notify_complete_shows_tray_message(app, monkeypatch):
    set_notifications_enabled(True)
    events: list[str] = []

    class _FakeTray:
        def __init__(self, *a, **k):
            events.append("init")

        def show(self):
            events.append("show")

        def showMessage(self, *a, **k):
            events.append("message")

    monkeypatch.setattr(QSystemTrayIcon, "__init__", _FakeTray.__init__)
    monkeypatch.setattr(QSystemTrayIcon, "show", _FakeTray.show)
    monkeypatch.setattr(QSystemTrayIcon, "showMessage", _FakeTray.showMessage)

    notifications.notify_complete()
    assert "message" in events
    assert "show" in events


def test_notify_complete_respects_disabled(app, monkeypatch):
    set_notifications_enabled(False)
    called = []
    monkeypatch.setattr(
        QSystemTrayIcon, "showMessage", lambda self, *a, **k: called.append(True)
    )
    notifications.notify_complete()
    assert called == []
    set_notifications_enabled(True)
