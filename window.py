from buffer import *
from hooks import *


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

    def __init__(self, width, height, buffer=None):
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

    def register_events(self, handlers):
        for event in handlers:
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(handlers[event])

    def resize(width, height):
        self.width = width
        self.height = height

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
                self.remember = 0

            line_len = len(self.buffer.lines[self.buffer_cursor[1]]) - 1
            if line_len < self.window_cursor[0]:
                self.remember = self.window_cursor[0]
                self.window_cursor[0] = line_len

        # self.window_cursor[1] = max(0, self.window_cursor[1])

    @raise_event
    def move_down(self):
        if self.window_cursor[1] == self.height:
            if self.buffer_cursor[1] == len(self.buffer.lines): pass
            else:
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
            if self.buffer_cursor[1] == 0: raise Exception('Should never happen.')

            self.window_cursor[1] -= 1
            self.buffer_cursor[1] -= 1

            if self.remember > self.buffer_cursor[0]:
                self.buffer_cursor[0] = self.remember
                self.remember = 0

            line_len = len(self.buffer.lines[self.buffer_cursor[1]]) - 1
            if line_len < self.window_cursor[0]:
                self.remember = self.window_cursor[0]
                self.window_cursor[0] = line_len

    @raise_event
    def move_right(self):
        self.window_cursor[0] += 1
        self.window_cursor[0] = min(   self.width - 1, 
                                self.window_cursor[0])
    @raise_event
    def move_left(self):
        self.window_cursor[0] -= 1
        self.window_cursor[0] = max(0, self.window_cursor[0])
