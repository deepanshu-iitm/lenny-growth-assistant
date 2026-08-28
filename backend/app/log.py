import json
import logging
import sys
from datetime import datetime, timezone

KEYS = ("event", "provider", "model", "hits", "kind", "error", "session_id")


class JsonLog(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        for key in KEYS:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, default=str)


def setup_logging() -> logging.Logger:
    log = logging.getLogger("lenny")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLog())
    log.addHandler(handler)
    log.propagate = False
    return log


log = logging.getLogger("lenny")
