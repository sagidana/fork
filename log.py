LOG_INFO = "INFO"
LOG_DEBUG = "DEBUG"

LOG_PATH = "/tmp/editor.log"

def elog(message, type=LOG_INFO):
    with open(LOG_PATH, "a") as log:
        log.write(f"{type} -> {message}\n")

