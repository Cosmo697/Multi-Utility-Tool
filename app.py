#!/usr/bin/env python
import logging
from tkinterdnd2 import TkinterDnD
from ttkthemes import ThemedStyle
from core.app_core import AppCore
from plugins.plugin_manager import load_plugins
from utils.diagnostics import time_block

def main():
    root = TkinterDnD.Tk()
    style = ThemedStyle(root)
    try:
        style.set_theme("equilux")
    except Exception:
        style.set_theme("arc")
    root.configure(background="#2e2e2e")
    style.configure('.', background='#2e2e2e', foreground='#d3d3d3', font=('Segoe UI', 10))
    style.configure('TFrame', background='#2e2e2e')
    style.configure('TLabel', background='#2e2e2e', foreground='#d3d3d3')
    style.configure('TButton', background='#3e3e3e', foreground='#d3d3d3')
    style.configure('TNotebook', background='#2e2e2e')
    style.configure('TNotebook.Tab', background='#3e3e3e', foreground='#d3d3d3')
    
    logging.getLogger(__name__).info("Launching the Multi-Utility Tool with Plugins...")

    with time_block("app_startup"):
        app = AppCore(root)
        load_plugins(app.plugin_api)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

if __name__ == "__main__":
    main()
