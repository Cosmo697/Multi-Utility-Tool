#!/usr/bin/env python
import logging

from .core.app_core import AppCore
from .utils.diagnostics import time_block


def main():
    logging.getLogger(__name__).info("Launching the Multi-Utility Tool with Plugins...")

    with time_block("app_startup"):
        app = AppCore()
    try:
        app.root.mainloop()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Application interrupted by user")
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
