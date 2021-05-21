#
import logging
import sys

logging.basicConfig(stream=sys.stderr)
logging.debug("Loading ping")


def run(payload):
    logging.debug("Running ping")
    return {"msg": "pong"}


if __name__ == "__main__":
    logging.warning("Main ping")
