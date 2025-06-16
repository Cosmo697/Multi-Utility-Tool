import pytest
from core.app_core import AppCore

def test_appcore_initializes_agents():
    app = AppCore()
    assert hasattr(app, 'ui')
    assert hasattr(app, 'plugins')
    assert hasattr(app, 'hotkeys')
    assert hasattr(app, 'tray')
    assert hasattr(app, 'threads')

def test_thread_tracking():
    import threading
    app = AppCore()
    t = threading.Thread(target=lambda: None)
    app.register_thread(t)
    assert t in app.threads
