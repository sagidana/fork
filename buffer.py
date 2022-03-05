from log import elog

from events import *
from hooks import *

from difflib import Differ
import json
import re

class Buffer():
    def __init__(self, file_path=None):
        Hooks.execute(ON_BUFFER_CREATE_BEFORE, self)

        # When change is starting, this is where original is saved
        self.shadow = None
        self.change_start_position = None
        self.undo_stack = []
        self.redo_stack = []

        self.lines = []
        self.file_path = file_path


        if not file_path: 
            Hooks.execute(ON_BUFFER_CREATE_AFTER, self)
            return
        
        try:
            with open(file_path, 'r') as f:
                self.lines = f.readlines()
        except:pass
        Hooks.execute(ON_BUFFER_CREATE_AFTER, self)

    def destroy(self):
        Hooks.execute(ON_BUFFER_DESTROY_BEFORE, self)
        Hooks.execute(ON_BUFFER_DESTROY_AFTER, self)

    def write_to_file(self, file_path):
        if not self.file_path: 
            self.file_path = file_path

        with open(file_path, 'w+') as f:
            f.writelines(self.lines)

    def write(self):
        if not self.file_path: 
            raise Exception("No file attached to buffer.")

        with open(self.file_path, 'w+') as f:
            f.writelines(self.lines)

    def _insert_char_to_line(self, x, y, char):
        try:
            line = self.lines[y]
            line = line[:x] + char + line[x:]
            self.lines[y] = line
            return True
        except: return False

    def _split_line(self, x, y):
        line = self.lines[y]
        first = line[:x] + '\n'
        second = line[x:]
        self.lines[y] = first
        self.lines.insert(y + 1, second) 

    def _join_line(self, y):
        line = self.lines[y]
        next_line = self.lines.pop(y + 1)
        joined = line[:-1] + next_line
        self.lines[y] = joined

    def remove_char(self, x, y):
        if x == 0: 
            if y == 0: return 
            self._join_line(y - 1)
        else:
            line = self.lines[y]
            line = line[:x-1] + line[x:]
            self.lines[y] = line

    def insert_char(self, x, y, char):
        if char == '\n':
            self._split_line(x, y)
        else:
            self._insert_char_to_line(x, y, char)

    def find_next_word(self, x, y):
        word_regex = r"\w+"
        pattern = re.compile(word_regex)

        curr_x = x
        curr_y = y
    
        line = self.lines[y]

        m = pattern.search(line, curr_x)
        if m and m.span()[0] == curr_x:
            start_next = m.span()[1]
            m = pattern.search(line, start_next)
        
        while not m and curr_y < len(self.lines) - 1:
            curr_y += 1
            m = pattern.search(self.lines[curr_y])

        if m:
            ret = (curr_y, m.span()[0], m.span()[1])
            return ret
        return None

    def find_prev_word(self, x, y):
        word_regex = r"\w+"
        pattern = re.compile(word_regex)

        curr_x = x
        curr_y = y
        line = self.lines[y]

        start = len(line) - curr_x

        m = pattern.search(line[::-1], start)
        # # skip first
        # if m and m.span()[0] == start:
            # start_next = m.span()[1]
            # m = pattern.search(line[::-1], start_next)
        
        if m:
            reversed_start = m.span()[0] 
            reversed_end = m.span()[1] 
            start = len(line) - reversed_end
            end = len(line) - reversed_start

            ret = (curr_y, start, end)
            return ret

        while curr_y > 0:
            curr_y -= 1
            line = self.lines[curr_y]
            m = pattern.search(line[::-1])
            if m:
                reversed_start = m.span()[0] 
                reversed_end = m.span()[1] 
                start = len(line) - reversed_end
                end = len(line) - reversed_start

                ret = (curr_y, start, end)
                return ret
        return None

    def replace_line(self, y, new_line):
        self.lines[y] = new_line

    def insert_line(self, y, new_line):
        self.lines.insert(y, new_line)

    def remove_line(self, y):
        self.lines.pop(y)

    def remove_scope(   self,
                        start_x,
                        start_y,
                        end_x,
                        end_y):
        pass

    def _change(self, change, undo=True):
        lines_for_deletion = []
        lines_for_insertion = {}
        lines_for_replacement = {}

        _from = "new" if undo else "old"
        _to = "old" if undo else "new"

        for line_num in change:
            # new lines needs to be removed
            if  _from in change[line_num] and \
                _to not in change[line_num]:
                lines_for_deletion.append(line_num)
                # self._remove_line(line_num)

            # changed lines needs to be replaced
            elif    _from in change[line_num] and \
                    _to in change[line_num]:
                lines_for_replacement[line_num] = change[line_num][_to]
                # self._replace_line(line_num, change[line_num]['old'])

            # removed lines neeeds to be reinserted
            elif    _to in change[line_num] and \
                    _from not in change[line_num]:
                lines_for_insertion[line_num] = change[line_num][_to]
                # self._insert_line(line_num, change[line_num]['old'])

        # lines removals must be in decreasing order to no mess up with the
        # line numbers
        for line in reversed(sorted(lines_for_deletion)):
            self.remove_line(line)

        # lines insertions must be in increasing order to no mess up with the
        # line numbers
        for line in sorted(lines_for_insertion):
            self.insert_line(line, lines_for_insertion[line])

        # for line replacements order is not important.
        for line in lines_for_replacement:
            self.replace_line(line, lines_for_replacement[line])

    def undo(self): 
        if len(self.undo_stack) == 0: return
        change_wrapper = self.undo_stack.pop()
        change = change_wrapper['change']

        self._change(change)

        self.redo_stack.append(change_wrapper)
        return change_wrapper['start_position']

    def redo(self): 
        if len(self.redo_stack) == 0: return
        change_wrapper = self.redo_stack.pop()
        change = change_wrapper['change']

        self._change(change, undo=False)

        self.undo_stack.append(change_wrapper)
        return change_wrapper['end_position']

    def change_begin(self, x, y):
        if self.shadow: elog("BUFFER: WTF, already in a change?")
        if self.change_start_position: elog("BUFFER: WTF, already in a change?")
        self.shadow = self.lines.copy()
        self.change_start_position = (x, y)
        self.redo_stack = [] # reset the redo stack on new edit.

    def _analyze_change(self):
        """
        The change format is as follows:
        A list of chnages per line:
        [
        <line_nume>, <old_line>, <new_line>
        ...
        <line_nume>, <old_line>, <new_line>
        ]

        In case there are no old/new line (removal/addition) the apropriate
        action is done correspondingly.
        """
        change = {}

        d = Differ()
        old_line_num = 0
        new_line_num = 0
        for line in d.compare(self.shadow, self.lines):
            if not (line.startswith('?') or \
                    line.startswith('-') or \
                    line.startswith('+')): 
                old_line_num += 1
                new_line_num += 1
                continue

            if line.startswith('+'): 
                if new_line_num not in change: change[new_line_num] = {}

                elog(f"BUFFER: {new_line_num}: {line.strip()}")
                change[new_line_num]['new'] = line[2:]

                new_line_num += 1
            elif line.startswith('-'):
                if old_line_num not in change: change[old_line_num] = {}

                elog(f"BUFFER: {old_line_num}: {line.strip()}")
                change[old_line_num]['old'] = line[2:]
                old_line_num += 1

        return change
            
    def change_end(self, x, y):
        change = self._analyze_change()

        if change: 
            change_wrapper = {}
            change_wrapper['change'] = change
            change_wrapper['start_position'] = self.change_start_position
            change_wrapper['end_position'] = (x,y)
            self.undo_stack.append(change_wrapper)

        self.shadow = None
        self.change_start_position = None
    
    def _find_relevant_object(self, pattern, x, y):
        curr_index = len(''.join(self.lines[:y])) + x

        found = None
        for m in pattern.finditer(''.join(self.lines)):
            start, end = m.span()
            if start <= curr_index <= end:
                found = m
                break
        if not found: return None
        start, end = found.span()

        start_x = 0
        start_y = 0
        end_x = 0
        end_y = 0

        curr_offset = 0
        curr_y = 0
        for i in range(len(self.lines)):
            if curr_offset <= start <= curr_offset + (len(self.lines[i]) - 1):
                start_y = i
                start_x = start - curr_offset
            if curr_offset <= end <= curr_offset + (len(self.lines[i]) - 1):
                end_y = i
                end_x = end - curr_offset
                break
            curr_offset += len(self.lines[i])
        return start_x, start_y, end_x, end_y

    def inner_parentheses(self, x, y): 
        ret = self.arround_parentheses(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y
    def inner_quotation(self, x, y): 
        ret = self.arround_quotation(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y
    def inner_square_brackets(self, x, y): 
        ret = self.arround_square_brackets(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y
    def inner_curly_brackets(self, x, y): 
        ret = self.arround_curly_brackets(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y
    def inner_greater_than(self, x, y): 
        ret = self.arround_greater_than(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y
    def inner_apostrophe(self, x, y): 
        ret = self.arround_apostrophe(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y
    def inner_backtick(self, x, y): 
        ret = self.arround_backtick(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y
    def inner_word(self, x, y): 
        ret = self.arround_word(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y
    def inner_WORD(self, x, y): 
        ret = self.arround_WORD(x, y)
        if not ret: return None
        start_x, start_y, end_x, end_y = ret

        start_x += 1
        end_x -= 1

        return start_x, start_y, end_x, end_y

    def arround_parentheses(self, x, y): 
        r = r"\(.*\)"
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
    def arround_quotation(self, x, y): 
        r = r"\".*\""
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
    def arround_square_brackets(self, x, y): 
        r = r"\[.*\]"
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
    def arround_curly_brackets(self, x, y): 
        r = r"\{.*\}"
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
    def arround_greater_than(self, x, y): 
        r = r"\<.*\>"
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
    def arround_apostrophe(self, x, y): 
        r = r"\'.*\'"
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
    def arround_backtick(self, x, y): 
        r = r"\`.*\`"
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
    def arround_word(self, x, y): 
        r = r"\`.*\`"
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
    def arround_WORD(self, x, y): 
        r = r"\`.*\`"
        pattern = re.compile(r, re.MULTILINE)

        return self._find_relevant_object(pattern, x, y)
