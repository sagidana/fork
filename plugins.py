from subprocess import Popen, PIPE, DEVNULL
from os import environ
from os import path
import string
import random
import sys
import re

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
        env = environ.copy()
        env["FZF_DEFAULT_COMMAND"] = "rg --files"
        p = Popen(cmd, stdout=PIPE, env=env)
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
                "--max-columns","200",
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

def _get_comment_syntax(language):
    comment_syntax = "#"
    if language in ['c', 'cpp', 'rust', 'javascript', 'java']:
        comment_syntax = "//"
    if language == 'python':
        comment_syntax = "#"
    if language == 'vimscript':
        comment_syntax = "\""
    return comment_syntax

def _index_of_first_nonspace_char(string):
    m = re.match('(\s*)', string)
    if m: return len(m.group(0))
    return -1

def comment(editor, start_y, end_y):
    comment_syntax = _get_comment_syntax(editor.get_curr_buffer().language)

    # check if any lines are commented.
    commented = True
    for y in range(start_y, end_y + 1):
        line = editor.get_curr_window().get_line(y)
        if re.match('^\s*$', line): continue # skip empty lines
        if not re.match(f'^\s*{comment_syntax} .*$', line):
            commented = False
            break

    if not commented:
        # lets comment
        for y in range(start_y, end_y + 1):
            line = editor.get_curr_window().get_line(y)
            if re.match('^\s*$', line): continue # skip empty lines
            i = _index_of_first_nonspace_char(line)
            if i == -1:
                elog(f"i: {i} {line}")
                continue
            line = f"{line[:i]}{comment_syntax} {line[i:]}"
            editor.get_curr_window().set_line(y, line)
    else:
        # lets uncomment
        for y in range(start_y, end_y + 1):
            line = editor.get_curr_window().get_line(y)
            if re.match('^\s*$', line): continue # skip empty lines
            i = _index_of_first_nonspace_char(line)
            if i == -1:
                elog(f"i: {i} {line}")
                continue
            line = f"{line[:i]}{line[i+len(comment_syntax)+1:]}"
            editor.get_curr_window().set_line(y, line)

def clipboard(text):
    ''' Copy `text` to the clipboard '''
    text = ''.join(text)

    with Popen(['xclip','-selection', 'clipboard'], stdin=PIPE,
                                                    stdout=DEVNULL,
                                                    stderr=DEVNULL) as pipe:
        pipe.communicate(input=text.encode('utf-8'))
