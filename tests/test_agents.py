from multi_utility_tool.core.app_core import AppCore


def _make_app():
    return AppCore(headless=True, enable_hotkeys=False, enable_tray=False, load_plugins=False)


def test_appcore_initializes_agents():
    app = _make_app()
    assert hasattr(app, "ui")
    assert hasattr(app, "plugins")
    assert hasattr(app, "hotkeys")
    assert hasattr(app, "tray")
    assert hasattr(app, "threads")
    app.shutdown()


def test_thread_tracking():
    import threading

    app = _make_app()
    t = threading.Thread(target=lambda: None)
    app.register_thread(t)
    assert t in app.threads
    app.shutdown()
