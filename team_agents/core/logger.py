import logging
import os

def get_logger(name: str):
    log_dir = os.path.join("data", "logs")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "system.log")),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)
