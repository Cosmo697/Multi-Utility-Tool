#!/usr/bin/env python
import logging
import sys
from core.runtime import RuntimeConfig, install_signal_handlers
from utils.diagnostics import time_block, emit_metrics_snapshot


def main(argv: list[str] | None = None) -> int:
    logging.getLogger(__name__).info("Launching the Multi-Utility Tool with Plugins...")

    config = RuntimeConfig.from_env_and_args(argv)
    with time_block("app_startup"):
        app = config.create_app()

    install_signal_handlers(app)

    try:
        app.root.mainloop()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Application interrupted by user")
    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).exception("Application crash detected")
        return 1
    finally:
        app.shutdown()
        emit_metrics_snapshot()
    return 0


if __name__ == "__main__":
    sys.exit(main())
