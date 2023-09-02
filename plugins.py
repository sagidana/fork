from subprocess import Popen, PIPE
from os import path
import string
import random
import sys

from log import elog

def fzf():
    """
    This is so cool, fzf print out to stderr the fuzzing options,
    and only the chosen result spit to the stdout.. this enables scripts like
    this to work out of the box, no redirection of the stderr is need - and
    only the result is redirected to our pipe (which contain the result)
    FZF - good job :)
    """
    try:
        cmd = ["fzf"]
        p = Popen(cmd, stdout=PIPE)
        output, errors = p.communicate()
        file_path = output.decode('utf-8').strip()
        file_path = file_path.replace("\n", "")
        if len(file_path) > 0: return file_path
    except Exception as e: elog(f"Exception: {e}")
    return None

def random_string(len=10):
    letters = string.ascii_lowercase
    return ''.join([random.choice(letters) for i in range(len)])

def ripgrep(search):
    try:
        # results_path = f"/tmp/rg-{random_string()}"
        # while path.isfile(results_path):
            # results_path = f"/tmp/rg-{random_string()}"
        # results_file = open(results_path, 'w')

        cmd = [ "rg",
                "-g","!tags",
                "--max-columns","100",
                "--vimgrep", search]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        output, errors = p.communicate()

        if len(output) > 0:
            return output
        # if path.getsize(results_path) > 0:
            # return results_path
        # results = []
        # for _result in _results.splitlines():
            # parts = _result.split(':')
            # if len(parts) < 4: continue

            # results.append({
                # "file": parts[0],
                # "line": parts[1],
                # "col": parts[2],
                # "text": parts[3]
                # })
        # return results
    except Exception as e: elog(f"ripgrep exception: {e}")
    return None

