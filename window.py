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
        
        elog(f"window: ({self.window_cursor[0]}, {self.window_cursor[1]})")
        elog(f"buffer: ({self.buffer_cursor[0]}, {self.buffer_cursor[1]})")

        self.stdscr.move(cursor[1], cursor[0])

    def draw(self):
        self.stdscr.clear()
        index = 0
        before = self.window_cursor[1]
        first_line = self.buffer_cursor[1] - before

        for i in range(self.height):
            try:
                line = self.buffer.lines[first_line + i]
                self.stdscr.addstr( i, 
                                    self.position[1] + 0, 
                                    line[:self.width])
            except: break

        self.draw_cursor()

    def _scroll_up(self):
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

    def _scroll_down(self):
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

    def resize(self, width, height):
        self.width = width
        self.height = height

        elog(f"width:{self.width}, height:{self.height}")

        if self.window_cursor[0] >= self.width - 1:
            diff = self.window_cursor[0] - (self.width - 1)
            for i in range(diff): self._move_left()
        else: pass

        if self.window_cursor[1] >= self.height - 1:
            diff = self.window_cursor[1] - (self.height - 1)
            for i in range(diff): self._move_up()
        else: pass

        self.draw()

    def _move_up(self):
        # We are at the bottom
        if self.buffer_cursor[1] == 0: return

        # We need to scroll up
        if self.window_cursor[1] == 0:
            self._scroll_up()
            self.draw()
        else: # Simple up action
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

    def _move_down(self):
        # We are at the bottom
        if self.buffer_cursor[1] == len(self.buffer.lines) - 1: return

        # We need to scroll down
        if self.window_cursor[1] == self.height - 1:
            self._scroll_down()
            self.draw()
        else: # Simple down action
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

    def _move_right(self):
        if self.buffer_cursor[0] == len(self.buffer.lines[self.buffer_cursor[1]]) - 1:
            return

        self.buffer_cursor[0] += 1

        if self.window_cursor[0] == self.width - 1:
            pass # TODO scroll horizontally
        else:
            self.window_cursor[0] += 1

    def _move_left(self):
        if self.buffer_cursor[0] == 0: return

        self.buffer_cursor[0] -= 1

        if self.window_cursor[0] == 0:
            pass # TODO scroll horizontally
        else:
            self.window_cursor[0] -= 1
            self.remember = 0

    @raise_event
    def move_up(self):
        self._move_up()
        self.draw_cursor()

    @raise_event
    def move_down(self):
        self._move_down()
        self.draw_cursor()

    @raise_event
    def move_right(self):
        self._move_right()
        self.draw_cursor()

    @raise_event
    def move_left(self):
        self._move_left()
        self.draw_cursor()
