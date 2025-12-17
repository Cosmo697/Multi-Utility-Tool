import os
import pytest
import tkinter as tk
from tkinter import ttk
from multi_utility_tool.plugins import audio_separator_plugin

pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") in {None, ""}, reason="requires Tk display"
)

class DummyAPI:
    def trigger_hook(self, *args, **kwargs):
        pass

def test_audio_separator_ui_loads():
    root = tk.Tk()
    tab = ttk.Frame(root)
    ui = audio_separator_plugin.AudioSeparatorUI(tab, DummyAPI())
    # Check that tabs exist
    assert hasattr(ui, 'demucs_tab')
    assert hasattr(ui, 'dpf_tab')
    # Check that main widgets exist
    assert hasattr(ui, 'console_dmx')
    assert hasattr(ui, 'console_dpf')
    root.destroy()
