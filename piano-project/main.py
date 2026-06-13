# main.py

import time
import logging
import os

from core.controller import Controller
import config


def setup_logging():
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    logging.basicConfig(
        filename=config.LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def main():
    setup_logging()
    logging.info("=== Piano assistant starting ===")

    controller = None

    try:
        controller = Controller()
        controller.start()
        logging.info("Controller started. Entering main loop.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Shutting down.")

    except Exception:
        logging.exception("Unexpected error in main loop")

    finally:
        if controller:
            controller.stop()
        logging.info("=== Piano assistant stopped ===")


if __name__ == "__main__":
    main()
