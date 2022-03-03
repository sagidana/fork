from buffer import *
from hooks import *

from log import elog

class Window():
    def raise_event(func):
        def event_wrapper(self):
            # self = args[0]
            func_name = func.__name__
            event = f"on_window_{func_name}_before"
            if event in self.events:
                for cb in self.events[event]: cb(self)
            func(self)
            event = f"on_window_{func_name}_after"
            if event in self.events:
                for cb in self.events[event]: cb(self)


        return event_wrapper

    def __init__(   self, 
                    stdscr, 
                    width, 
                    height, 
                    position=(0,0), 
                    buffer=None):

        self.stdscr = stdscr
        self.position = list(position)
        self.width = width
        self.height = height
        self.window_cursor = [0,0]
        self.buffer_cursor = [0,0]
        self.remember = 0

        if not buffer:
            self.buffer = Buffer()
        else:
            self.buffer = buffer

        self.events = {}

        self.draw()

    def register_events(self, handlers):
        for event in handlers:
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(handlers[event])

    def draw_cursor(self):
        cursor = [pos for pos in self.window_cursor]

        cursor[0] = self.position[0] + self.window_cursor[0]
        cursor[1] = self.position[1] + self.window_cursor[1]
        
        self.stdscr.move(cursor[1], cursor[0])

    def draw(self):
        index = 0
        for i in range(self.height):
            try:
                line = self.buffer.lines[i]
                self.stdscr.addstr( i, 
                                    self.position[1] + 0, 
                                    line[:self.width])
            except: break

        self.draw_cursor()

    def scroll_up(self):
        pass

    def scroll_down(self):
        pass

    def resize(self, width, height):
        self.width = width
        self.height = height

        self.draw()

    @raise_event
    def move_up(self):
        if self.window_cursor[1] == 0:
            if self.buffer_cursor[1] == 0: pass
            else:
                self.buffer_cursor[1] -= 1

                if self.remember > self.buffer_cursor[0]:
                    self.buffer_cursor[0] = self.remember
                    self.window_cursor[0] = self.remember
                    self.remember = 0

                line_len = len(self.buffer.lines[self.buffer_cursor[1]]) - 1
                if line_len < self.window_cursor[0]:
                    self.remember = self.window_cursor[0]
                    self.window_cursor[0] = line_len
                    self.buffer_cursor[0] = line_len
        else:
            if self.buffer_cursor[1] == 0: raise Exception('Should never happen.')

            self.window_cursor[1] -= 1
            self.buffer_cursor[1] -= 1

            if self.remember > self.buffer_cursor[0]:
                self.buffer_cursor[0] = self.remember
                self.window_cursor[0] = self.remember
                self.remember = 0

            line_len = len(self.buffer.lines[self.buffer_cursor[1]]) - 1
            if line_len < self.window_cursor[0]:
                self.remember = self.window_cursor[0]
                self.window_cursor[0] = line_len
                self.buffer_cursor[0] = line_len
        self.draw_cursor()

    @raise_event
    def move_down(self):
        if self.buffer_cursor[1] == len(self.buffer.lines) - 1: return

        if self.window_cursor[1] == self.height - 1:
            self.buffer_cursor[1] += 1

            if self.remember > self.buffer_cursor[0]:
                self.buffer_cursor[0] = self.remember
                self.window_cursor[0] = self.remember
                self.remember = 0

            line_len = len(self.buffer.lines[self.buffer_cursor[1]]) - 1
            if line_len < self.window_cursor[0]:
                self.remember = self.window_cursor[0]
                self.window_cursor[0] = line_len
                self.buffer_cursor[0] = line_len
        else:
            self.window_cursor[1] += 1
            self.buffer_cursor[1] += 1

            if self.remember > self.buffer_cursor[0]:
                self.buffer_cursor[0] = self.remember
                self.window_cursor[0] = self.remember
                self.remember = 0

            line_len = len(self.buffer.lines[self.buffer_cursor[1]]) - 1
            if line_len < self.window_cursor[0]:
                self.remember = self.window_cursor[0]
                self.window_cursor[0] = line_len
                self.buffer_cursor[0] = line_len
        self.draw_cursor()

    @raise_event
    def move_right(self):
        elog(f"{len(self.buffer.lines[self.buffer_cursor[1]])}")
        if self.buffer_cursor[0] == len(self.buffer.lines[self.buffer_cursor[1]]) - 1:
            return

        self.buffer_cursor[0] += 1

        if self.window_cursor[0] == self.width - 1:
            pass # TODO scroll horizontally
        else:
            self.window_cursor[0] += 1
        self.draw_cursor()

    @raise_event
    def move_left(self):
        if self.buffer_cursor[0] == 0: return

        self.buffer_cursor[0] -= 1

        if self.window_cursor[0] == 0:
            pass # TODO scroll horizontally
        else:
            self.window_cursor[0] -= 1
        self.draw_cursor()
