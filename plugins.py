from subprocess import Popen, PIPE, DEVNULL
from datetime import datetime, date
from os import environ
from os import path
import string
import random
import sys
import re
import os

from settings import *
from log import elog

def fzf(editor):
    """
    This is so cool, fzf print out to stderr the fuzzing options,
    and only the chosen result spit to the stdout.. this enables scripts like
    this to work out of the box, no redirection of the stderr is need - and
    only the result is redirected to our pipe (which contain the result)
    FZF - good job :)
    """
    try:
        stdin = editor.screen.stdin
        stderr = editor.screen.stdout

        cmd = ["fzf"]
        env = environ.copy()
        env["FZF_DEFAULT_COMMAND"] = "rg --files"
        p = Popen(cmd,
                  stdin=stdin,
                  stdout=PIPE,
                  stderr=stderr,
                  env=env)
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

def gd(editor, search):
    try:
        cmd = [ "/home/s/github/gd/gd",
                "--language", editor.get_curr_buffer().language,
                "--symbol", search,
                # "--action", "goto-definition"
              ]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        output, errors = p.communicate()

        if len(output) > 0:
            return output
    except Exception as e: elog(f"ripgrep exception: {e}")
    return None

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
            editor.get_curr_window().set_line(y, line, propagate=False)
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
            editor.get_curr_window().set_line(y, line, propagate=False)
    editor.get_curr_buffer().flush_changes()

def clipboard(text):
    ''' Copy `text` to the clipboard '''
    text = ''.join(text)

    with Popen(['xclip','-selection', 'clipboard'], stdin=PIPE,
                                                    stdout=DEVNULL,
                                                    stderr=DEVNULL) as pipe:
        pipe.communicate(input=text.encode('utf-8'))

def trim_lines(text, max_chars=80):
    words = iter(text.split())
    lines, current = [], next(words)
    for word in words:
        if len(current) + 1 + len(word) > max_chars:
            lines.append(current)
            current = word
        else:
            current += " " + word
    lines.append(current)
    return '\n'.join(lines)

def format(editor, start_x, start_y, end_x, end_y):
    start_x = 0
    end_x = len(editor.get_curr_window().get_line(end_y)) - 2
    lines = editor.get_curr_buffer().get_scope_text(start_x,
                                                    start_y,
                                                    end_x,
                                                    end_y)
    if len(lines) == 0: return

    stream = ''.join(lines)

    stream = trim_lines(stream)

    editor.get_curr_buffer().replace_scope( start_x,
                                            start_y,
                                            end_x,
                                            end_y,
                                            stream)

def _doc_code(editor):
    time = datetime.now().strftime("%H:%M:%S")
    y = editor.get_curr_window().buffer_cursor[1] + 1
    file_path = editor.get_curr_buffer().file_path
    if not file_path: return None

    scope = editor.get_curr_buffer().visual_get_scope()
    if not scope: return None
    start_x, start_y, end_x, end_y = scope
    start_x = 0
    end_x = len(editor.get_curr_window().get_line(end_y)) - 1
    text = editor.get_curr_buffer().get_scope_text(start_x, start_y, end_x, end_y)
    if len(text) == 0: return None
    text = ''.join(text)

    to_write = f"[{time}] [CODE] `{file_path}:{y}`\n"
    to_write += "```\n"
    to_write += f"{text}\n"
    to_write += "```\n"
    return to_write

def _doc_note(editor):
    time = datetime.now().strftime("%H:%M:%S")
    file_path = editor.get_curr_buffer().file_path
    if not file_path: file_path = ""

    scope = editor.get_curr_buffer().visual_get_scope()
    if not scope: return
    start_x, start_y, end_x, end_y = scope
    start_x = 0
    end_x = len(editor.get_curr_window().get_line(end_y)) - 1
    text = editor.get_curr_buffer().get_scope_text(start_x, start_y, end_x, end_y)
    if len(text) == 0: return
    text = ''.join(text)

    to_write = f"[{time}] [NOTE] {file_path}:\n"
    to_write += f"{text}\n"
    return to_write

def _doc_location(editor):
    time = datetime.now().strftime("%H:%M:%S")
    x = editor.get_curr_window().buffer_cursor[0]
    y = editor.get_curr_window().buffer_cursor[1] + 1
    file_path = editor.get_curr_buffer().file_path
    if not file_path: return None

    to_write = f"[{time}] [LOCATION] `{file_path}:{y}:{x}`\n"
    return to_write

def doc_get_latest_file():
    # create doc folder if not exist
    default_doc_path = path.expanduser('~/.doc/')
    doc_path = get_setting("doc_path", default=default_doc_path)
    if not path.exists(doc_path): os.makedirs(doc_path)
    file_name = f"{date.today()}.md"
    doc_path = path.join(doc_path, file_name)
    return doc_path

def doc(mode, editor):
    # create doc folder if not exist
    default_doc_path = path.expanduser('~/.doc/')
    doc_path = get_setting("doc_path", default=default_doc_path)
    if not path.exists(doc_path): os.makedirs(doc_path)
    file_name = f"{date.today()}.md"
    doc_path = path.join(doc_path, file_name)

    if mode == 'note':
        to_write = _doc_note(editor)
        if not to_write: return
        with open(doc_path, 'a+') as doc_file:
            doc_file.write(to_write)
        return
    if mode == 'location':
        to_write = _doc_location(editor)
        if not to_write: return
        with open(doc_path, 'a+') as doc_file:
            doc_file.write(to_write)
        return
    if mode == 'code':
        to_write = _doc_code(editor)
        if not to_write: return
        with open(doc_path, 'a+') as doc_file:
            doc_file.write(to_write)
        return
