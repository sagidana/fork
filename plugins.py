from subprocess import Popen, PIPE
import sys

from log import elog

def fzf():
    try:
        cmd = ["fzf"]
        p = Popen(cmd, stdout=PIPE)
        output, errors = p.communicate()
        file_path = output.decode('utf-8').strip()
        file_path = file_path.replace("\n", "")
        if len(file_path) > 0:
            return file_path
    except Exception as e: elog(f"Exception: {e}")
    return None

