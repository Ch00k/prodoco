import logging
import logging.config
import time


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "utc": {
            "()": UTCFormatter,
            "format": "{asctime}.{msecs:03.0f}Z {levelname:<8s} {message}",
            "style": "{",
            # "format": "%(asctime)s.%(msecs)03dZ %(levelname)s\t %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "utc",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "apscheduler": {
            "level": "WARNING",
        },
    },
}
