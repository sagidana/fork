from events import *
from hooks import *
import re

class Buffer():
    def __init__(self, file_path=None):
        Hooks.execute(ON_BUFFER_CREATE_BEFORE, self)

        self.lines = []
        self.file_path = None


        if not file_path: 
            Hooks.execute(ON_BUFFER_CREATE_AFTER, self)
            return
        
        try:
            with open(file_path, 'r') as f:
                self.lines = f.readlines()
                # self.lines = [l.strip() for l in f.readlines()]
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

    def insert(self, x, y, char):
        try:
            line = self.lines[y]
            line = line[:x] + char + line[x:]
            self.lines[y] = line
            return True
        except: return False

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
        if m and m.span()[0] == start:
            start_next = m.span()[1]
            m = pattern.search(line[::-1], start_next)
        
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
