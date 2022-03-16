from log import elog

from colors import get_curses_color_pair
from settings import g_settings
from buffer import *
from hooks import *
from highlight import get_highlights

import timeout_decorator
import curses
import time
import re

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
        
        # elog(f"window: ({self.window_cursor[0]}, {self.window_cursor[1]})")
        # elog(f"buffer: ({self.buffer_cursor[0]}, {self.buffer_cursor[1]})")

        self.stdscr.move(cursor[1], cursor[0])

    def draw_line(self):
        y = self.window_cursor[1]
        line = self.get_curr_line()

        self.stdscr.addstr( y, 
                            self.position[0] + 0, 
                            line[:self.width])
        self.draw_cursor()

    def color_pair_to_curses(self, fg, bg):
        return get_curses_color_pair(fg, bg)

    def style_to_attr(self, style):
        fg = style['foreground'] if 'foreground' in style else g_settings['theme']['colors']['editor.foreground']
        bg = style['background'] if 'background' in style else g_settings['theme']['colors']['editor.background']

        pair = self.color_pair_to_curses(fg, bg)
        attr = curses.color_pair(pair)
        return attr

    def highlight(self):
        buffer_height = len(self.buffer.lines) - 1

        start_y = self.buffer_cursor[1] - self.window_cursor[1]
        end_y = min(start_y + self.height, buffer_height)

        for node, style in get_highlights(  self.buffer.treesitter, 
                                            # g_settings['theme']):
                                            g_settings['theme_opt']):
            if node.start_point[0] >= end_y: return
            if node.end_point[0] < start_y: continue

            attr = self.style_to_attr(style)

            y = node.start_point[0]
            x = node.start_point[1]
            length = node.end_point[1] - x

            self.stdscr.chgat(  y - start_y, 
                                x, 
                                length, attr)

    def draw(self):
        # - Draw with defaut colors of theme
        self.stdscr.clear()

        before = self.window_cursor[1]
        first_line = self.buffer_cursor[1] - before
        buffer_height = len(self.buffer.lines) - 1

        style = {}
        style['background'] = g_settings['theme']['colors']['editor.background']
        style['foreground'] = g_settings['theme']['colors']['editor.foreground']
        attr = self.style_to_attr(style)

        for y in range(self.height):
            buffer_y = first_line + y

            if buffer_y > buffer_height: 
                line = ""
            else:
                line = self.buffer.lines[first_line + y]

            x_range = min(self.width, max(0, len(line) - 1))
            for buffer_x in range(x_range):
                try:
                    self.stdscr.addstr( y, 
                                        self.position[0] + buffer_x, 
                                        line[buffer_x],
                                        attr)
                except Exception as e: elog(f"Exception: 1 {e}")

            for x in range(self.width - x_range):
                try:
                    self.stdscr.addstr( y, 
                                        self.position[0] + x_range + x,
                                        ' ',
                                        attr)
                except Exception as e: elog(f"Exception: {x} {x_range} {e}")

        # - on top of thaat draw highlights
        self.highlight()

        self.draw_cursor()
    
    def _draw(self):
        self.stdscr.clear()
        index = 0
        before = self.window_cursor[1]
        first_line = self.buffer_cursor[1] - before
        buffer_height = len(self.buffer.lines) - 1

        for y in range(self.height):
            buffer_y = first_line + y

            if buffer_y > buffer_height: 
                line = ""
            else:
                line = self.buffer.lines[first_line + y]

            x_range = min(self.width, max(0, len(line) - 1))
            for buffer_x in range(x_range):
                style = self.buffer.syntax.get_style(buffer_x, buffer_y)
                attr = self.style_to_attr(style)
                try:
                    self.stdscr.addstr( y, 
                                        self.position[0] + buffer_x, 
                                        line[buffer_x],
                                        attr)
                except Exception as e: elog(f"Exception: 1 {e}")

            style = self.buffer.syntax.get_default_style()
            attr = self.style_to_attr(style)
            for x in range(self.width - x_range):
                try:
                    self.stdscr.addstr( y, 
                                        self.position[0] + x_range + x,
                                        ' ',
                                        attr)
                except Exception as e: elog(f"Exception: {x} {x_range} {e}")
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
        if self.buffer_cursor[1] == 0: return False

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
        return True

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

    def _align_center(self):
        center = int(self.height / 2)
        if self.buffer_cursor[1] < center:
            self.window_cursor[1] = self.buffer_cursor[1]
        # elif self.buffer_cursor[1] :
        else:
            self.window_cursor[1] = center

    def is_visible(self, buf_x, buf_y):
        return True # TODO:

    def move_cursor_to_buf_location(self, buf_x, buf_y):
        if self.is_visible(buf_x, buf_y):
            elog(f"{buf_x}, {buf_y}")
            if self.buffer_cursor[1] > buf_y:
                y_diff = self.buffer_cursor[1] - buf_y
                for i in range(y_diff): self._move_up()
            else:
                y_diff = buf_y - self.buffer_cursor[1]
                for i in range(y_diff): self._move_down()

            if self.buffer_cursor[0] > buf_x:
                x_diff = self.buffer_cursor[0] - buf_x
                for i in range(x_diff): self._move_left()
            else:
                x_diff = buf_x - self.buffer_cursor[0]
                for i in range(x_diff): self._move_right()

            self.draw_cursor()
            # self.window_cursor[0] = buf_x
            # self.window_cursor[1] = buf_y

            # self.buffer_cursor[0] = buf_x
            # self.buffer_cursor[1] = buf_y
        else:
            pass

    def get_curr_line(self):
        return self.buffer.lines[self.buffer_cursor[1]]

    def get_curr_line_len(self):
        return len(self.get_curr_line())

    def get_line(self, line_num):
        try:
            return self.buffer.lines[line_num]
        except Exception as e:
            elog(f"{e}")
            return None

    def scroll_up_half_page(self):
        half = int(self.height / 2)
        for i in range(half): self._move_up()
        self._align_center()

        self.draw()

    def scroll_down_half_page(self):
        half = int(self.height / 2)
        for i in range(half): self._move_down()
        self._align_center()

        self.draw()

    def move_begin(self): 
        self.window_cursor[0] = 0
        self.window_cursor[1] = 0
        self.buffer_cursor[0] = 0
        self.buffer_cursor[1] = 0
        self.draw()

    def move_end(self): 
        self.window_cursor[0] = 0
        self.buffer_cursor[0] = 0
        
        buffer_len = len(self.buffer.lines) - 1 
        self.buffer_cursor[1] = buffer_len

        if buffer_len > self.height - 1:
            self.window_cursor[1] = self.height - 1
        else:
            self.window_cursor[1] = buffer_len
        self.draw()

    def move_line(self, line): pass

    def move_to_x(self, x): 
        while self.buffer_cursor[0] > x: self._move_left()
        while self.buffer_cursor[0] < x: self._move_right()
        self.draw_cursor()

    def move_line_begin(self):
        while self.buffer_cursor[0] > 0: self._move_left()
        self.draw_cursor()

    def move_line_end(self):
        while self.buffer_cursor[0] < len(self.get_curr_line()) - 1: 
            self._move_right()
        self.draw_cursor()

    def move_word_forward(self): 
        ret = self.buffer.find_next_word(   self.buffer_cursor[0],
                                            self.buffer_cursor[1])
        if not ret: return
        x, y = ret
        self.move_cursor_to_buf_location(x, y)

    def move_word_backward(self): 
        ret = self.buffer.find_prev_word(   self.buffer_cursor[0],
                                            self.buffer_cursor[1])
        if not ret: return
        x, y = ret
        self.move_cursor_to_buf_location(x, y)


    def move_WORD_forward(self): 
        ret = self.buffer.find_next_WORD(   self.buffer_cursor[0],
                                            self.buffer_cursor[1])
        if not ret: return
        x, y = ret
        self.move_cursor_to_buf_location(x, y)

    def move_WORD_backward(self): 
        ret = self.buffer.find_prev_WORD(   self.buffer_cursor[0],
                                            self.buffer_cursor[1])
        if not ret: return
        x, y = ret
        self.move_cursor_to_buf_location(x, y)

    def move_word_end(self): 
        ret = self.buffer.find_word_end(    self.buffer_cursor[0],
                                            self.buffer_cursor[1])
        if not ret: return
        x, y = ret
        self.move_cursor_to_buf_location(x, y)

    def move_WORD_end(self):
        ret = self.buffer.find_WORD_end(    self.buffer_cursor[0],
                                            self.buffer_cursor[1])
        if not ret: return
        x, y = ret
        self.move_cursor_to_buf_location(x, y)


    @timeout_decorator.timeout(2)
    def get_key(self):
        return self.stdscr.getch()

    def find(self): 
        try: key = self.get_key()
        except: key = None

        try:
            char = chr(key)

            x = self.buffer_cursor[0]
            y = self.buffer_cursor[1]
            loc = self.buffer.find_next_char(x, y, char)
            if not loc: return
            x, y = loc[0], loc[1]
            self.move_cursor_to_buf_location(x, y)
        except: pass
        
    def find_back(self): 
        try: key = self.get_key()
        except: key = None

        try:
            char = chr(key)
            x = self.buffer_cursor[0]
            y = self.buffer_cursor[1]
            loc = self.buffer.find_prev_char(x, y, char)
            if not loc: return
            x, y = loc[0], loc[1]
            self.move_cursor_to_buf_location(x, y)
        except: pass

    def till(self): 
        try: key = self.get_key()
        except: key = None

        try:
            char = chr(key)
            x = self.buffer_cursor[0]
            y = self.buffer_cursor[1]
            loc = self.buffer.find_next_char(x, y, char)
            if not loc: return
            x, y = loc[0], loc[1]
            x = x - 1 if x > 0 else x
            self.move_cursor_to_buf_location(x, y)
        except: pass

    def till_back(self): 
        try: key = self.get_key()
        except: key = None

        try:
            char = chr(key)
            x = self.buffer_cursor[0]
            y = self.buffer_cursor[1]
            loc = self.buffer.find_prev_char(x, y, char)
            if not loc: return
            x, y = loc[0], loc[1]
            x = x + 1 if x < len(self.get_line(y)) - 1 else x
            self.move_cursor_to_buf_location(x, y)
        except: pass
    
    def remove_line(self):
        self.buffer.remove_line(self.buffer_cursor[1])

        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]

        if y >= len(self.buffer.lines) - 1: y = len(self.buffer.lines) - 1
        if x >= len(self.get_line(y)) - 1: x = len(self.get_line(y)) - 1

        self.move_cursor_to_buf_location(x, y)
        self.draw()

    def remove_scope(   self,
                        start_x,
                        start_y,
                        end_x,
                        end_y):
        x, y = self.buffer.remove_scope(start_x, start_y, end_x, end_y)

        self.move_cursor_to_buf_location(x, y)
        self.draw()

    def new_line_after(self): 
        self.buffer.insert_line(self.buffer_cursor[1] + 1, "\n")
        self.move_down()
        self.move_line_begin()
        self.draw()

    def new_line_before(self): 
        self.buffer.insert_line(self.buffer_cursor[1], "\n")
        self.move_line_begin()
        self.draw()

    def remove_char_special(self, x): 
        if x > self.get_curr_line_len() - 1: return
        if x <= 0: return

        self.buffer.remove_char(    x,
                                    self.buffer_cursor[1])
        self.draw()

    def remove_char(self): 
        if self.buffer_cursor[0] == 0:
            if self.buffer_cursor[1] == 0: return
            # we are about to move line up because of our removal. this is our
            # new x after joining the lines
            new_x = len(self.buffer.lines[self.buffer_cursor[1] - 1]) - 1

            self.buffer.remove_char(    self.buffer_cursor[0],
                                        self.buffer_cursor[1])

            self.move_up()
            self.move_to_x(new_x)
            self.draw()
        else:
            self.buffer.remove_char(    self.buffer_cursor[0],
                                        self.buffer_cursor[1])
            self.move_left()
            self.draw()

    def insert_char(self, char):
        self.buffer.insert_char(    self.buffer_cursor[0],
                                    self.buffer_cursor[1],
                                    char)
        if char == '\n':
            self.move_down()
            self.move_line_begin()
            self.draw()
        else:
            self.move_right()
            self.draw()

    def insert_line_before(self, line):
        self.buffer.insert_line(self.buffer_cursor[1],
                                line)
        self.move_line_begin()
        self.draw()

    def insert_line_after(self, line):
        self.buffer.insert_line(self.buffer_cursor[1]+1,
                                line)
        self.move_down()
        self.move_line_begin()
        self.draw()

    def undo(self): 
        position = self.buffer.undo()
        if not position: return
        self.move_cursor_to_buf_location(   position[0],
                                            position[1])
        self.draw()

    def redo(self): 
        position = self.buffer.redo()
        if not position: return

        # in vim the redo does not return cursor location.. wonder why?
        self.move_cursor_to_buf_location(   position[0],
                                            position[1])
        self.draw()

    @raise_event
    def change_begin(self):
        self.buffer.change_begin(   self.buffer_cursor[0],
                                    self.buffer_cursor[1])

    @raise_event
    def change_end(self):
        self.buffer.change_end( self.buffer_cursor[0],
                                self.buffer_cursor[1])

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
