#!/usr/bin/env python
import logging
from core.app_core import AppCore
from utils.diagnostics import time_block

def main():
    logging.getLogger(__name__).info("Launching the Multi-Utility Tool with Plugins...")

    with time_block("app_startup"):
        app = AppCore()
    app.root.protocol("WM_DELETE_WINDOW", app.root.destroy)
    app.root.mainloop()

if __name__ == "__main__":
    main()
