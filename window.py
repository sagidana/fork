from log import elog
from settings import *
from idr import *
from buffer import *
from hooks import *
from syntax import get_syntax_highlights, get_scope_style

from popup import *
from utils import *

from intervaltree import Interval, IntervalTree
from string import printable
from os import path
import traceback
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

    def on_buffer_reload_callback(self, priv):
        orig_x = self.buffer_cursor[0]
        orig_y = self.buffer_cursor[1]
        self.window_cursor = [0,0]
        self.buffer_cursor = [0,0]
        self.move_cursor_to_buf_location(orig_x, orig_y)
        self.draw()

    def on_buffer_change_callback(self, priv):
        # TODO: update cursor pos if needed
        if self.tab.is_window_visible(self.id):
            self.draw()

    def describe(self):
        buffer_description = self.buffer.describe()
        return f"[window {self.id}] {buffer_description}"

    def __init__(   self,
                    tab,
                    screen,
                    width,
                    height,
                    position=(0,0),
                    buffer=None,
                    window_cursor=[0,0],
                    buffer_cursor=[0,0],
                    jumpslist=list()):
        if not buffer: raise Exception("Not implemented.")

        self.id = get_id(WINDOW_ID)
        self.tab = tab
        self.screen = screen

        self.buffer = buffer
        handlers = {}
        handlers[ON_BUFFER_RELOAD] = self.on_buffer_reload_callback
        handlers[ON_BUFFER_CHANGE] = self.on_buffer_change_callback
        self.buffer.register_events(handlers)

        self.set_lines_margin()

        self.position = list(position)

        self.width = width
        self.height = height

        self.content_position = [position[0], position[1]]
        self.content_width = self.width
        self.content_height = self.height

        self._need_to_clear_pairs = False

        self.line_numbers = get_setting('line_numbers')
        self.status_line = get_setting('status_line')

        self.window_cursor = window_cursor.copy()
        self.buffer_cursor = buffer_cursor.copy()
        self.remember = 0

        self.events = {}

        self.jumpslist = jumpslist.copy()
        self.jumpslist_cursor = -1
        self.discarded_jumps = []

        self.quickfix = []
        self.quickfix_pos = -1

    def close(self):
        handlers = {}
        handlers[ON_BUFFER_RELOAD] = self.on_buffer_reload_callback
        handlers[ON_BUFFER_CHANGE] = self.on_buffer_change_callback
        self.buffer.unregister_events(handlers)

    def change_buffer(self, buffer):
        handlers = {}
        handlers[ON_BUFFER_RELOAD] = self.on_buffer_reload_callback
        handlers[ON_BUFFER_CHANGE] = self.on_buffer_change_callback
        self.buffer.unregister_events(handlers)

        self.buffer = buffer
        self.buffer.register_events(handlers)

        self.window_cursor = [0,0]
        self.buffer_cursor = [0,0]
        self.remember = 0

        self.set_lines_margin()

        if self.line_numbers:
            self.content_position[0] = self.position[0] + self.lines_margin
            self.content_width = self.width - self.lines_margin

        self.draw()

    def enable_status_line(self):
        if self.status_line: return
        self.content_height -= 1
        self.status_line = True
        self.draw()

    def disable_status_line(self):
        if not self.status_line: return
        self.content_height += 1
        self.status_line = False
        self.draw()

    def enable_lines_numbers(self):
        if self.line_numbers: return
        self.content_position[0] = self.position[0] + self.lines_margin
        self.content_width = self.width - self.lines_margin
        self.line_numbers = True
        self.draw()

    def disable_lines_numbers(self):
        if not self.line_numbers: return
        self.content_position[0] = self.position[0]
        self.content_width = self.width
        self.line_numbers = False
        self.draw()

    def add_jump(self):
        jump =  {
                "file_path": self.buffer.file_path,
                "buffer_id": self.buffer.id,
                "col": self.buffer_cursor[0],
                "line": self.buffer_cursor[1]
                }
        # elog(f"{self.jumpslist_cursor}")
        # for j in self.jumpslist: elog(f"{json.dumps(j, indent=2)}")

        # do not add jump if it is already the current one.
        if  self.jumpslist_cursor >= 0 and \
            self.jumpslist[self.jumpslist_cursor]['file_path'] == jump['file_path'] and \
            self.jumpslist[self.jumpslist_cursor]['col'] == jump['col'] and \
            self.jumpslist[self.jumpslist_cursor]['line'] == jump['line']:
            return
        if self.jumpslist_cursor < len(self.jumpslist) - 1:
            self.discarded_jumps.append(self.jumpslist[self.jumpslist_cursor+1:])
            self.jumpslist = self.jumpslist[:self.jumpslist_cursor+1]
        self.jumpslist.append(jump)
        self.jumpslist_cursor += 1

    def prev_jump(self):
        if self.jumpslist_cursor < 1: return None
        self.jumpslist_cursor -= 1
        return self.jumpslist[self.jumpslist_cursor]
    def next_jump(self):
        if self.jumpslist_cursor >= len(self.jumpslist) - 1: return None
        self.jumpslist_cursor += 1
        return self.jumpslist[self.jumpslist_cursor]

    def register_events(self, handlers):
        for event in handlers:
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(handlers[event])

    def _draw_cursor(self):
        cursor = [pos for pos in self.window_cursor]

        cursor[0] = self.window_cursor[0]
        cursor[1] = self.window_cursor[1]

        x = self._expanded_x(self.buffer_cursor[1], self.buffer_cursor[0])
        # self._screen_move(cursor[0], cursor[1])
        self._screen_move(x, cursor[1])

    def _translate_buf_x_y_to_win_x_y(self, x, y):
        # maybe is_visible
        buf_x = self.buffer_cursor[0]
        buf_y = self.buffer_cursor[1]
        win_x = self.window_cursor[0]
        win_y = self.window_cursor[1]

        win_start_buf_y = buf_y - win_y
        win_end_buf_y = buf_y + (self.content_height - 1 - win_y)
        if y < win_start_buf_y: return None
        if y > win_end_buf_y: return None
        ret_y = y - win_start_buf_y

        ret_x = self._expanded_x(y, x)
        return ret_x, ret_y

    def _draw_pairs(self):
        try:
            if self._need_to_clear_pairs:
                self.draw()
                self._need_to_clear_pairs = False

            x_1 = self.buffer_cursor[0]
            y_1 = self.buffer_cursor[1]
            char_1 = self.get_curr_line()[x_1]
            if char_1 not in "(){}[]": return

            char_2 = self.buffer.negate_char(char_1)
            x_2 = x_1
            x_2 = y_1
            if char_1 in "({[":
                ret = self.buffer.find_next_char(x_1, y_1, char_2, smart=True)
                if not ret: return
                x_2, y_2 = ret
            else:
                ret = self.buffer.find_prev_char(x_1, y_1, char_2, smart=True)
                if not ret: return
                x_2, y_2 = ret

            ret = self._translate_buf_x_y_to_win_x_y(x_1, y_1)
            if not ret: return
            x_1, y_1 = ret
            ret = self._translate_buf_x_y_to_win_x_y(x_2, y_2)
            if not ret: return
            x_2, y_2 = ret

            style = {}
            style['background'] = "#FF00FF"
            self._screen_write(x_1, y_1, char_1, style)
            self._screen_write(x_2, y_2, char_2, style)
            self._need_to_clear_pairs = True
        except Exception as e:
            elog(f"_draw_pairs bug..: {e}", type="ERROR")
            pass

    def draw_cursor(self):
        if self.status_line: self.draw_status_line()
        if self.line_numbers: self.draw_line_numbers()
        self.visualize()
        self.highlight()
        self.multi_cursors()
        self._draw_pairs()
        self._draw_cursor()

    def set_lines_margin(self):
        self.lines_margin = len(str(len(self.buffer.lines))) + 1

    def tailing_spaces(self):
        style = {}
        style['background'] = "#FF00FF"

        buffer_height = len(self.buffer.lines) - 1
        screen_start_y = self.buffer_cursor[1] - self.window_cursor[1]
        screen_end_y = min(screen_start_y + self.content_height, buffer_height)

        for scree_y, y in enumerate(range(screen_start_y, screen_end_y)):
            line = self.get_line(y)
            trailing_spaces = (len(line) - 1) - len(line.rstrip())
            if trailing_spaces <= 0: continue
            trailing_string_index = len(line) - 1 - trailing_spaces
            trailing_screen_length = self._expanded_x(y, len(line) - 1) - \
                                     self._expanded_x(y, trailing_string_index)

            self._screen_write( self._expanded_x(y, trailing_string_index),
                                scree_y,
                                " "*trailing_screen_length,
                                style)

    def highlight(self):
        buffer_height = len(self.buffer.lines) - 1

        screen_start_y = self.buffer_cursor[1] - self.window_cursor[1]
        screen_end_y = min(screen_start_y + self.content_height, buffer_height)

        for start_x, start_y, end_x, end_y, style in self.buffer.highlights:
            if start_y >= screen_end_y: return
            if end_y < screen_start_y: continue

            if start_y == end_y:
                string = self.get_line(start_y)[start_x:end_x]

                self._screen_write( self._expanded_x(start_y, start_x),
                                    start_y - screen_start_y,
                                    string,
                                    style)
                continue

            # first line
            string = self.get_line(start_y)[start_x:]
            self._screen_write( self._expanded_x(start_y, start_x),
                                start_y - screen_start_y,
                                string,
                                style)

            # lines in between
            for y in range(start_y + 1, end_y):
                string = self.get_line(y)
                self._screen_write( 0,
                                    y - screen_start_y,
                                    string,
                                    style)

            # last line
            string = self.get_line(end_y)[:end_x]
            self._screen_write( 0,
                                end_y - screen_start_y,
                                string,
                                style)

    def get_syntax(self):
        MAX_COLS = 1000
        syntax_map = IntervalTree()
        if not self.buffer.treesitter: return syntax_map

        buffer_height = len(self.buffer.lines) - 1

        screen_start_y = self.buffer_cursor[1] - self.window_cursor[1]
        screen_end_y = min(screen_start_y + self.content_height, buffer_height)

        for node, style in get_syntax_highlights(   self.buffer.treesitter,
                                                    start_point=(screen_start_y, 0),
                                                    end_point=(screen_end_y+1, 0)):
            # elog(f"{dir(node)}")
            # start_pos = self.buffer.get_file_pos(node.start_point[1],node.start_point[0])
            # end_pos = self.buffer.get_file_pos(node.end_point[1],node.end_point[0])
            # start_pos = node.start_byte
            # end_pos = node.end_byte
            start_pos = (node.start_point[0] * MAX_COLS) + node.start_point[1]
            end_pos = (node.end_point[0] * MAX_COLS) + node.end_point[1]

            if start_pos == end_pos: continue

            syntax_map[start_pos:end_pos] = style
        return syntax_map

    def _visualize_block(self):
        style = {}
        style['foreground'] = get_settings()['theme']['colors']['editor.foreground']
        style['background'] = get_settings()['theme']['colors']['selection.background']

        orig_start_x, orig_start_y, orig_end_x, orig_end_y = self.buffer.visual_get_scope()
        if orig_start_x > orig_end_x:
            temp = orig_start_x
            orig_start_x = orig_end_x
            orig_end_x = temp
        orig_end_x += 1
        buffer_height = len(self.buffer.lines) - 1
        screen_start_y = self.buffer_cursor[1] - self.window_cursor[1]
        screen_end_y = min(screen_start_y + self.content_height, buffer_height)

        if orig_start_y > screen_end_y: return
        if orig_end_y < screen_start_y: return

        start_y = max(orig_start_y, screen_start_y)
        if start_y == orig_start_y: start_x = orig_start_x
        else: start_x = 0

        end_y = min(orig_end_y, screen_end_y)
        if end_y == orig_end_y: end_x = orig_end_x
        else: end_x = len(self.get_line(end_y)) - 1

        for y in range(start_y, end_y+1):
            try:
                string = self.get_line(y)[start_x:end_x]
                self._screen_write( self._expanded_x(y, start_x),
                                    y - screen_start_y,
                                    string,
                                    style)
            except: pass

    def _visualize(self):
        style = {}
        style['foreground'] = get_settings()['theme']['colors']['editor.foreground']
        style['background'] = get_settings()['theme']['colors']['selection.background']
        # style['reverse'] = None

        orig_start_x, orig_start_y, orig_end_x, orig_end_y = self.buffer.visual_get_scope()
        orig_end_x += 1
        buffer_height = len(self.buffer.lines) - 1
        screen_start_y = self.buffer_cursor[1] - self.window_cursor[1]
        screen_end_y = min(screen_start_y + self.content_height, buffer_height)

        if orig_start_y > screen_end_y: return
        if orig_end_y < screen_start_y: return

        start_y = max(orig_start_y, screen_start_y)
        if start_y == orig_start_y: start_x = orig_start_x
        else: start_x = 0

        end_y = min(orig_end_y, screen_end_y)
        if end_y == orig_end_y: end_x = orig_end_x
        else: end_x = len(self.get_line(end_y)) - 1

        if start_y == end_y:
            string = self.get_line(start_y)[start_x:end_x]
            self._screen_write( self._expanded_x(start_y, start_x),
                                start_y - screen_start_y,
                                string,
                                style)
            return

        # first line
        string = self.get_line(start_y)[start_x:]
        self._screen_write( self._expanded_x(start_y, start_x),
                            start_y - screen_start_y,
                            string,
                            style)

        # lines in between
        for y in range(start_y + 1, end_y):
            string = self.get_line(y)
            self._screen_write( 0,
                                y - screen_start_y,
                                string,
                                style)

        # last line
        string = self.get_line(end_y)[:end_x]
        self._screen_write( 0,
                            end_y - screen_start_y,
                            string,
                            style)

    def _visualize_line(self):
        style = {}
        style['foreground'] = get_settings()['theme']['colors']['editor.foreground']
        style['background'] = get_settings()['theme']['colors']['selection.background']
        # style['reverse'] = None
        start_x, start_y, end_x, end_y = self.buffer.visual_get_scope()

        buffer_height = len(self.buffer.lines) - 1
        screen_start_y = self.buffer_cursor[1] - self.window_cursor[1]
        screen_end_y = min(screen_start_y + self.content_height, buffer_height)

        if start_y > screen_end_y: return
        if end_y < screen_start_y: return

        start_y = max(start_y, screen_start_y)
        end_y = min(end_y, screen_end_y)

        for y in range(start_y, end_y + 1):
            string = self.get_line(y)
            self._screen_write( 0,
                                y - screen_start_y,
                                string[:-1],
                                style)

    def visualize(self):
        if not self.buffer.visual_mode: return

        if self.buffer.visual_mode == 'visual':
            self._visualize()
        if self.buffer.visual_mode == 'visual_line':
            self._visualize_line()
        if self.buffer.visual_mode == 'visual_block':
            self._visualize_block()

    def multi_cursors(self):
        try:
            buffer_height = len(self.buffer.lines) - 1

            screen_start_y = self.buffer_cursor[1] - self.window_cursor[1]
            screen_end_y = min(screen_start_y + self.content_height, buffer_height)

            style = {}
            style['background'] = get_setting("multi_cursors_background")
            style['foreground'] = get_setting("multi_cursors_foreground")

            for x,y in self.buffer.cursors:
                if y >= screen_end_y: continue
                if y < screen_start_y: continue

                char = self.get_line(y)[x]
                # elog(f"line: {self.get_line(y)} {x} {char}")
                self._screen_write( self._expanded_x(y, x),
                                    y - screen_start_y,
                                    char,
                                    style)
        except Exception as e:
            elog(f"[!] multi_cursors {e}")

    def _get_curr_highlight(self):
        buf_x = self.buffer_cursor[0]
        buf_y = self.buffer_cursor[1]
        index = "?"
        for i, (start_x, start_y, end_x, end_y, style) in enumerate(self.buffer.highlights):
            if start_x <= buf_x <= end_x and \
               start_y <= buf_y <= end_y:
                index = str(i+1)
                break
        return index

    def _get_highlights_status(self):
        total = len(self.buffer.highlights)
        if total == 0: return ""
        curr = self._get_curr_highlight()
        return f"[{curr}/{total}]"

    def draw_status_line(self):
        style = {}
        style['background'] = get_setting("status_line_background")
        style['foreground'] = get_setting("status_line_foreground")

        buffer_name = path.basename(self.buffer.file_path) if self.buffer.file_path else "<in_memory>"
        buffer_id = self.buffer.id
        buffer_language = self.buffer.language
        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]

        if buffer_language:
            status_line = f"{buffer_id} [{buffer_language}] {buffer_name} {y}:{x}"
        else:
            status_line = f"{buffer_id} {buffer_name} {y}:{x}"

        highlights_status = self._get_highlights_status()
        if len(highlights_status) > 0: status_line += f" {highlights_status}"

        if len(status_line) < self.width:
            status_line = f"{status_line}{' '*(self.width - len(status_line))}"
        else:
            status_line = status_line[:self.width]
        self._screen_write_raw( 0,
                                self.height - 1,
                                status_line,
                                style,
                                to_flush=False)

    def draw_line_numbers(self):
        style = {}
        style['background'] = get_setting("line_numbers_background")
        style['foreground'] = get_setting("line_numbers_foreground")

        buf_start_y = self.buffer_cursor[1] - self.window_cursor[1]

        for y in range(self.content_height):
            try:
                if y == self.window_cursor[1]:
                    lineno = str(buf_start_y + y + 1).ljust(self.lines_margin - 1)
                else: # relative numbers
                    lineno = str(abs(self.window_cursor[1] - y)).rjust(self.lines_margin - 1)
                lineno = lineno.ljust(self.lines_margin)

                self._screen_write_raw( 0,
                                        y,
                                        lineno,
                                        style,
                                        to_flush=False)
            except Exception as e:
                elog(f"Exception: {e}", type="ERROR")
                elog(f"traceback: {traceback.format_exc()}", type="ERROR")

    def clear(self):
        for y in range(self.height):
            start_x = 0
            end_x = self.width - 1
            self._screen_clear_line_partial(y, start_x, end_x)

    def _get_scope_text(self, start_x, start_y, end_x, end_y):
        if start_y == end_y:
            return self.buffer.lines[start_y][start_x:end_x]

        # first line
        text = self.buffer.lines[start_y][start_x:]

        # middle
        curr_line_number = start_y + 1
        while curr_line_number < end_y:
            text += self.buffer.lines[curr_line_number]
            curr_line_number += 1

        # last line
        text += self.buffer.lines[end_y][:end_x]

        return text

    def draw(self):
        # elog(f"drawing window: {self.id}")
        # import traceback
        # for s in traceback.extract_stack():
            # elog(f"    {path.basename(s.filename)}: {s.name}")
        debug = False
        self.screen.disable_cursor()
        try:
            before = self.window_cursor[1]
            first_line = self.buffer_cursor[1] - before
            buffer_height = len(self.buffer.lines) - 1

            default_style = {}
            default_style['background'] = get_settings()['theme']['colors']['editor.background']
            default_style['foreground'] = get_settings()['theme']['colors']['editor.foreground']

            syntax_map = self.get_syntax()

            for y in range(self.content_height):
                x = 0
                if debug:
                    time.sleep(0.1)
                    self.screen.flush()

                buffer_y = first_line + y
                buffer_start_x = 0

                # we at the end of the buffer, draw background.
                if buffer_y > buffer_height:
                    self._screen_write( x, y,
                                        " "*self.content_width,
                                        default_style,
                                        to_flush=debug)
                    continue

                line = self.get_line(buffer_y)
                buffer_end_x = max(0, len(line) - 1) # minus one because of '\n'

                MAX_COLS = 1000
                _start_pos = (buffer_y * MAX_COLS) + buffer_start_x
                _end_pos = (buffer_y * MAX_COLS) + buffer_end_x

                syntax = sorted(list(syntax_map[_start_pos:_end_pos]))

                if debug:
                    elog(f"syntax query: [{_start_pos},{_end_pos}]")
                    for s in syntax: elog(f"\t{s}")

                # there is not syntax, draw with default style.
                if len(syntax) == 0:
                    self._screen_write( self._expanded_x(buffer_y, x),
                                        y,
                                        line[:-1], # do not draw '\n'
                                        default_style,
                                        to_flush=debug)
                    x += len(line) - 1
                    # draw rest of window background.
                    if x < self.screen.width:
                        x_rest = self.content_width - x
                        self._screen_write( self._expanded_x(buffer_y, x), y,
                                            " "*x_rest,
                                            default_style,
                                            to_flush=debug)
                    continue

                # drawing with syntax highlights...:

                while len(syntax) > 0:
                    if debug:
                        time.sleep(0.1)
                        self.screen.flush()

                    curr_syntax = syntax.pop(0)
                    if curr_syntax.begin <= _start_pos:
                        syntax_start_x = 0
                    else:
                        syntax_start_x = curr_syntax.begin - _start_pos

                    if curr_syntax.end >= _end_pos:
                        syntax_end_x = _end_pos - _start_pos
                    else:
                        syntax_end_x = curr_syntax.end - _start_pos

                    # draw with default until the syntax portion
                    if x < syntax_start_x:
                        self._screen_write( self._expanded_x(buffer_y, x), y,
                                            line[x:syntax_start_x],
                                            default_style,
                                            to_flush=debug)
                    # draw with syntax style
                    x = syntax_start_x
                    self._screen_write( self._expanded_x(buffer_y, x), y,
                                        line[syntax_start_x:syntax_end_x],
                                        curr_syntax.data,
                                        to_flush=debug)
                    x = syntax_end_x
                # draw to the end of the window with default style
                if x < buffer_end_x:
                    self._screen_write( self._expanded_x(buffer_y, x), y,
                                        line[x:buffer_end_x],
                                        default_style,
                                        to_flush=debug)
                    x = buffer_end_x

                # fill end of window with background
                if x < self.screen.width:
                    x_rest = self.content_width - x
                    self._screen_write( self._expanded_x(buffer_y, x), y,
                                        " "*x_rest,
                                        default_style,
                                        to_flush=debug)

            # the rest calls will do implicit flush.
            self.tailing_spaces()
            self.visualize()
            self.highlight()
            self.multi_cursors()
            if self.status_line: self.draw_status_line()
            if self.line_numbers: self.draw_line_numbers()
            # is focused?
            if self.tab.get_curr_window().id == self.id:
                self._draw_cursor()
        except Exception as e:
            elog(f"Exception: {e}", type="ERROR")
            elog(f"traceback: {traceback.format_exc()}", type="ERROR")
        self.screen.enable_cursor()

    def _expanded_string_len(self, string):
        _x = 0
        for c in string:
            if c == '\t': _x += len(get_setting("tab_representation"))
            else: _x += 1
        return _x

    def _expanded_x(self, y, x):
        return self._expanded_string_len(self.get_line(y)[:x])

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
        self.clear()

        self.width = width
        self.height = height

        if not self.line_numbers:
            self.content_width = width
        else:
            self.content_width = width - self.lines_margin

        if not self.status_line:
            self.content_height = height
        else:
            self.content_height = height - 1

        if self.window_cursor[0] >= self.content_width- 1:
            diff = self.window_cursor[0] - (self.content_width - 1)
            for i in range(diff): self._move_left()
        else: pass

        if self.window_cursor[1] >= self.content_height - 1:
            diff = self.window_cursor[1] - (self.content_height - 1)
            for i in range(diff): self._move_up()
        else: pass

    def set_position(self, x, y):
        self.clear()
        self.position[0] = x
        if not self.line_numbers:
            self.content_position[0] = x
        else:
            self.content_position[0] = x + self.lines_margin
        self.position[1] = y
        self.content_position[1] = y

    def _move_up(self):
        scrolled = False
        # We are at the bottom
        if self.buffer_cursor[1] == 0: return False

        # We need to scroll up
        if self.window_cursor[1] == 0:
            self._scroll_up()
            scrolled = True
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
        return True,  scrolled

    def _move_down(self):
        scrolled = False
        # We are at the bottom
        if self.buffer_cursor[1] == len(self.buffer.lines) - 1: return False

        # We need to scroll down
        if self.window_cursor[1] == self.content_height - 1:
            self._scroll_down()
            scrolled = True
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
        return True, scrolled

    def _move_right(self):
        if self.buffer_cursor[0] == len(self.buffer.lines[self.buffer_cursor[1]]) - 1:
            return

        self.buffer_cursor[0] += 1

        if self.window_cursor[0] == self.width - 1:
            pass # TODO scroll horizontally
        else:
            self.window_cursor[0] += 1

        # self.buffer.visual_set_current( self.buffer_cursor[0],
                                        # self.buffer_cursor[1])

    def _move_left(self):
        if self.buffer_cursor[0] == 0: return

        self.buffer_cursor[0] -= 1

        if self.window_cursor[0] == 0:
            pass # TODO scroll horizontally
        else:
            self.window_cursor[0] -= 1
            self.remember = 0

        # self.buffer.visual_set_current( self.buffer_cursor[0],
                                        # self.buffer_cursor[1])

    def _align_center(self):
        center = int(self.content_height / 2)
        if self.buffer_cursor[1] < center:
            self.window_cursor[1] = self.buffer_cursor[1]
        # elif self.buffer_cursor[1] :
        else:
            self.window_cursor[1] = center

    def _align_top(self):
        top = 0
        self.window_cursor[1] = top

    def _align_bottom(self):
        bottom = self.content_height - 1

        if self.buffer_cursor[1] < bottom:
            self.window_cursor[1] = self.buffer_cursor[1]
        else:
            self.window_cursor[1] = bottom

    def align_center(self):
        self._align_center()
        self.draw()

    def align_top(self):
        self._align_top()
        self.draw()

    def align_bottom(self):
        self._align_bottom()
        self.draw()

    def is_visible(self, buf_x, buf_y):
        return True # TODO:

    def move_cursor_to_buf_location(self, buf_x, buf_y, to_draw=True):
        if len(self.buffer.lines) - 1 < buf_y: return
        if len(self.buffer.lines[buf_y]) - 1 < buf_x: return

        if self.is_visible(buf_x, buf_y):
            scrolled = False
            if self.buffer_cursor[1] > buf_y:
                y_diff = self.buffer_cursor[1] - buf_y
                for i in range(y_diff):
                    ret = self._move_up()
                    if ret and ret[1]: scrolled = True
            else:
                y_diff = buf_y - self.buffer_cursor[1]
                for i in range(y_diff):
                    ret = self._move_down()
                    if ret and ret[1]: scrolled = True

            if self.buffer_cursor[0] > buf_x:
                x_diff = self.buffer_cursor[0] - buf_x
                for i in range(x_diff): self._move_left()
            else:
                x_diff = buf_x - self.buffer_cursor[0]
                for i in range(x_diff): self._move_right()

            if scrolled:
                if to_draw: self.draw()
            else:
                if to_draw: self.draw_cursor()
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
            elog(f"Exception: {e}", type="ERROR")
            elog(f"traceback: {traceback.format_exc()}", type="ERROR")
            return None

    def half_page_down(self):
        half = int(self.content_height / 2)
        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]
        max_y = len(self.buffer.lines) - 1

        y = min(max_y, y + half)
        x = min(x, len(self.get_line(y)) - 1)
        return x, y

    def half_page_up(self):
        half = int(self.content_height / 2)
        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]

        y = max(y - half, 0)
        x = min(x, len(self.get_line(y)) - 1)
        return x, y

    def _scroll_up_half_page(self):
        half = int(self.content_height / 2)
        for i in range(half): self._move_up()
        self._align_center()

    def scroll_up_half_page(self):
        self._scroll_up_half_page()
        self.draw()

    def _scroll_down_half_page(self):
        half = int(self.content_height / 2)
        for i in range(half): self._move_down()
        self._align_center()

    def scroll_down_half_page(self):
        self._scroll_down_half_page()
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

        if buffer_len > self.content_height - 1:
            self.window_cursor[1] = self.content_height - 1
        else:
            self.window_cursor[1] = buffer_len
        self.draw()

    def move_begin_visible(self):
        while self.window_cursor[1] > 0: self._move_up()
        self.draw_cursor()

    def move_middle_visible(self):
        middle =  int(self.content_height / 2)
        while self.window_cursor[1] < middle:
            if not self._move_down(): break
        while self.window_cursor[1] > middle:
            if not self._move_up(): break
        self.draw_cursor()

    def move_end_visible(self):
        while self.window_cursor[1] < self.content_height - 1:
            if not self._move_down(): break
        self.draw_cursor()

    def move_line(self, line): pass

    def _move_to_x(self, x):
        while self.buffer_cursor[0] > x: self._move_left()
        while self.buffer_cursor[0] < x: self._move_right()

    def move_to_x(self, x):
        self._move_to_x(x)
        self.draw_cursor()

    def _move_line_begin(self, ignore_spaces=False):
        while self.buffer_cursor[0] > 0: self._move_left()

        if ignore_spaces:
            line = self.get_line(self.buffer_cursor[1])
            while self.buffer_cursor[0] < len(line) - 1:
                if not re.match(r"\s", line[self.buffer_cursor[0]]): break
                self._move_right()

    def move_line_begin(self, ignore_spaces=False):
        self._move_line_begin(ignore_spaces)
        self.draw_cursor()

    def move_line_end(self):
        self.buffer_cursor[0] = min(self.buffer_cursor[0], len(self.get_curr_line()) - 1)
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

    def get_key(self):
        return self.screen.get_key()

    def upper(self):
        line = self.get_curr_line()
        char = line[self.buffer_cursor[0]]
        if char.isupper():
            char = char.lower()
        else:
            char = char.upper()
        self.buffer.replace_char(   self.buffer_cursor[0],
                                    self.buffer_cursor[1],
                                    char)
        # self.draw()

    def replace(self):
        try:
            key = self.get_key()
            char = chr(key)
            self.buffer.replace_char(   self.buffer_cursor[0],
                                        self.buffer_cursor[1],
                                        char)
            # self.draw()

        except Exception as e:
            elog(f"Exception: {e}", type="ERROR")
            elog(f"traceback: {traceback.format_exc()}", type="ERROR")

    def _find(self, char):
        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]
        loc = self.buffer.find_next_char(x, y, char)
        if not loc: return
        x, y = loc[0], loc[1]
        self.move_cursor_to_buf_location(x, y)

    def find(self):
        try: key = self.get_key()
        except: key = None

        try:
            char = chr(key)
            self._find(char)
            return char
        except: pass

    def _find_back(self, char):
        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]
        loc = self.buffer.find_prev_char(x, y, char)
        if not loc: return
        x, y = loc[0], loc[1]
        self.move_cursor_to_buf_location(x, y)

    def find_back(self):
        try: key = self.get_key()
        except: key = None

        try:
            char = chr(key)
            self._find_back(char)
            return char
        except: pass

    def _till(self, char):
        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]
        loc = self.buffer.find_next_char(x, y, char)
        if not loc: return
        x, y = loc[0], loc[1]
        x = x - 1 if x > 0 else x
        self.move_cursor_to_buf_location(x, y)

    def till(self):
        try: key = self.get_key()
        except: key = None

        try:
            char = chr(key)
            self._till(char)
            return char
        except: pass

    def _till_back(self, char):
        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]
        loc = self.buffer.find_prev_char(x, y, char)
        if not loc: return
        x, y = loc[0], loc[1]
        x = x + 1 if x < len(self.get_line(y)) - 1 else x
        self.move_cursor_to_buf_location(x, y)

    def till_back(self):
        try: key = self.get_key()
        except: key = None

        try:
            char = chr(key)
            self._till_back(char)
            return char
        except: pass

    def remove_line_at(self, y, propagate=True):
        y = self.buffer.remove_line(y, propagate=propagate)
        x = self.buffer_cursor[0]

        if y >= len(self.buffer.lines) - 1: y = len(self.buffer.lines) - 1
        if x >= len(self.get_line(y)) - 1: x = len(self.get_line(y)) - 1

        self.move_cursor_to_buf_location(x, y, to_draw=propagate)

    def set_line(self, y, new_line, propagate=True):
        _x = self.buffer_cursor[0]
        _y = self.buffer_cursor[1]

        self.buffer.replace_line(y, new_line, propagate=propagate)

        if _y == y and _x >= len(self.get_line(_y)) - 1:
            _x = len(self.get_line(_y)) - 1

        self.move_cursor_to_buf_location(_x, _y, to_draw=propagate)

    def empty_line(self, keep_whitespaces=False):
        y = self.buffer_cursor[1]
        line = self.get_line(y)

        if re.match(r'^\s*$', line) or not keep_whitespaces: # if only whitespaces
            self.move_cursor_to_buf_location(0, y)
            # replace with empty line (including the newline char)
            self.buffer.replace_line(y, "\n", propagate=False)
        else:
            indent = len(line) - len(line.lstrip())
            self.move_cursor_to_buf_location(indent, y)
            # replace with empty line (including the newline char)
            self.buffer.replace_line(y, line[:indent]+'\n', propagate=False)
        self.buffer.flush_changes()

    def remove_line(self):
        to_remove = self.buffer_cursor[1]

        x = self.buffer_cursor[0]
        y = self.buffer_cursor[1]

        last_line = y == len(self.buffer.lines) - 1

        y = min(y, len(self.buffer.lines) - 2)
        if last_line:
            dest_line = self.get_line(y)
            x = min(x, len(dest_line) - 1)
        else:
            dest_line = self.get_line(y+1)
            x = min(x, len(dest_line) - 1)

        self.move_cursor_to_buf_location(x, y)

        self.buffer.remove_line(to_remove)

    def indent_lines(   self,
                        start_y,
                        end_y,
                        is_right):
        indent_content = get_setting('tab_insert')
        if is_right:
            for y in range(start_y, end_y + 1):
                line = self.get_line(y)
                if len(line) - 1 <= 0: continue
                if not re.search('\S', line): continue
                line = indent_content + line
                self.buffer.replace_line(y, line, propagate=False)
            curr_y = self.buffer_cursor[1]
            if start_y <= self.buffer_cursor[1] < end_y + 1:
                for i in range(len(indent_content)):
                    self._move_right()
        else:
            for y in range(start_y, end_y + 1):
                line = self.get_line(y)
                if len(line) - 1 <= 0: continue
                m = re.search('\S', line)
                if not m: continue
                num_of_spaces = m.start()
                num_to_remove = min(len(indent_content), num_of_spaces)
                self.buffer.replace_line(y, line[num_to_remove:], propagate=False)
                if self.buffer_cursor[1] == y:
                    for i in range(num_to_remove):
                        self._move_left()
        self.buffer.flush_changes()
        self.draw_cursor()

    def remove_scope(   self,
                        start_x,
                        start_y,
                        end_x,
                        end_y):
        self.move_cursor_to_buf_location(start_x, start_y, to_draw=False)
        x, y = self.buffer.remove_scope(start_x, start_y, end_x, end_y)

    def search_replace_scope(   self,
                                start_x,
                                start_y,
                                end_x,
                                end_y,
                                pattern,
                                dest):
        self.move_cursor_to_buf_location(start_x, start_y, to_draw=False)
        self.buffer.search_replace_scope(   start_x,
                                            start_y,
                                            end_x,
                                            end_y,
                                            pattern,
                                            dest)

    def new_line_after(self):
        line = self.get_curr_line()
        num_of_spaces_at_start = len(line) - len(line.lstrip())
        num_of_spaces_at_start = min(num_of_spaces_at_start, len(line) - 1)
        prefix_new_line = line[:num_of_spaces_at_start]

        self.buffer.insert_line(self.buffer_cursor[1] + 1, f"{prefix_new_line}\n")
        self.move_down()
        self.move_line_end()

    def new_line_before(self):
        line = self.get_curr_line()
        num_of_spaces_at_start = len(line) - len(line.lstrip())
        num_of_spaces_at_start = min(num_of_spaces_at_start, len(line) - 1)
        prefix_new_line = line[:num_of_spaces_at_start]

        self.buffer.insert_line(self.buffer_cursor[1], f"{prefix_new_line}\n")
        self.move_line_end()

    def remove_char_special(self, x):
        if x > self.get_curr_line_len() - 1: return
        if x <= 0: return

        self.buffer.remove_char(    x,
                                    self.buffer_cursor[1])

    def _remove_char(self, propagate=True):
        if self.buffer_cursor[0] == 0:
            if self.buffer_cursor[1] == 0: return
            # we are about to move line up because of our removal. this is our
            # new x after joining the lines
            new_x = len(self.buffer.lines[self.buffer_cursor[1] - 1]) - 1

            self.buffer.remove_char(    self.buffer_cursor[0],
                                        self.buffer_cursor[1],
                                        propagate=propagate)

            self._move_up()
            self._move_to_x(new_x)
        else:
            self.buffer.remove_char(    self.buffer_cursor[0],
                                        self.buffer_cursor[1],
                                        propagate=propagate)
            self._move_left()

    def remove_chars(self, num):
        for i in range(num):
            self._remove_char(propagate=False)
        self.buffer.flush_changes()
        # self.draw()
        self.draw_cursor()

    def remove_char(self):
        self._remove_char()
        # self.draw()
        self.draw_cursor()

    def _insert_char(self, char, to_draw=True):
        self.buffer.insert_char(    self.buffer_cursor[0],
                                    self.buffer_cursor[1],
                                    char)
        if char == '\n' or char == '\r':
            ret = self._move_down()
            if ret and ret[1]:
                if to_draw: self.draw() # scrolled
            self._move_line_begin(ignore_spaces=True)
        else:
            self._move_right()

    def replace_char_backward(self, char, to_draw=True):
        self._move_left()
        self.buffer.replace_char(   self.buffer_cursor[0],
                                    self.buffer_cursor[1],
                                    char, propagate=False)
        self.buffer.flush_changes()
        self.draw_cursor()

    def replace_char_forward(self, char, to_draw=True):
        self.buffer.replace_char(   self.buffer_cursor[0],
                                    self.buffer_cursor[1],
                                    char, propagate=False)
        self.buffer.flush_changes()
        if char == '\n' or char == '\r':
            ret = self._move_down()
            if ret and ret[1]:
                if to_draw: self.draw() # scrolled
            self._move_line_begin()
        else:
            self._move_right()
        self.draw_cursor()

    def insert_char(self, char):
        self._insert_char(char)
        self.draw_cursor()

    def insert_string(self, string):
        x, y = self.buffer.insert_string(   self.buffer_cursor[0],
                                            self.buffer_cursor[1],
                                            string)

        self.move_cursor_to_buf_location(   x,
                                            y)

    def insert_line_before(self, line, propagate=True):
        self.buffer.insert_line(self.buffer_cursor[1],
                                line,
                                propagate=propagate)
        if propagate: self.move_line_begin()
        else: self._move_line_begin()
        # self.draw()

    def insert_line_after(self, line, propagate=True):
        self.buffer.insert_line(self.buffer_cursor[1]+1,
                                line,
                                propagate=propagate)
        if propagate:
            self.move_down()
            self.move_line_begin()
        else:
            self._move_down()
            self._move_line_begin()

    def join_line(self):
        curr_line = self.buffer_cursor[1]
        if curr_line + 1 > len(self.buffer.lines) - 1: return

        next_line = self.get_line(curr_line + 1)

        next_line = " " + next_line.lstrip() # make only one space at the begining

        self.buffer.replace_line(curr_line + 1, next_line)

        self.move_line_end()

        self.buffer.remove_char(0, curr_line + 1) # to trigger join

    def undo(self):
        position = self.buffer.undo()
        if not position: return
        self.move_cursor_to_buf_location(   position[0],
                                            position[1])

    def redo(self):
        position = self.buffer.redo()
        if not position: return

        # in vim the redo does not return cursor location.. wonder why?
        self.move_cursor_to_buf_location(   position[0],
                                            position[1])

    def visual_begin(self, mode):
        self.buffer.visual_begin(   mode,
                                    self.buffer_cursor[0],
                                    self.buffer_cursor[1])

    def visual_end(self):
        self.buffer.visual_end()

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
        ret = self._move_up()
        if not ret: return
        if ret[1]:
            self.draw()
        else:
            self.draw_cursor()

    @raise_event
    def move_down(self):
        ret = self._move_down()
        if not ret: return
        if ret[1]:
            self.draw()
        else:
            self.draw_cursor()

    @raise_event
    def move_right(self):
        self._move_right()
        self.draw_cursor()

    @raise_event
    def move_left(self):
        self._move_left()
        self.draw_cursor()

    def quickfix_set(self, locations):
        self.quickfix = locations
        self.quickfix_pos = -1

    def quickfix_clear(self):
        self.quickfix = []
        self.quickfix_pos = -1

    def quickfix_pop(self, get_or_create_buffer_cb):
        popup = QuickfixPopup(self)
        location = popup.pop()
        self.draw() # redraw after pop
        if not location: return

        # update pos according to popup
        for i, loc in enumerate(self.quickfix):
            if loc == location:
                self.quickfix_pos = i
                break

        file_path, file_line, file_col = extract_destination(location)

        buffer = get_or_create_buffer_cb(file_path)

        self.add_jump()
        self.change_buffer(buffer)
        self.move_cursor_to_buf_location(file_col, file_line)
        self.add_jump()
        self.align_center()

    def quickfix_next(self, get_or_create_buffer_cb):
        if len(self.quickfix) == 0: return
        self.quickfix_pos += 1
        self.quickfix_pos = self.quickfix_pos % len(self.quickfix)
        location = self.quickfix[self.quickfix_pos]
        file_path, file_line, file_col = extract_destination(location)

        buffer = get_or_create_buffer_cb(file_path)

        self.add_jump()
        self.change_buffer(buffer)
        self.move_cursor_to_buf_location(file_col, file_line)
        self.add_jump()
        self.align_center()

    def quickfix_prev(self, get_or_create_buffer_cb):
        if len(self.quickfix) == 0: return
        self.quickfix_pos -= 1
        self.quickfix_pos = self.quickfix_pos % len(self.quickfix)
        location = self.quickfix[self.quickfix_pos]
        file_path, file_line, file_col = extract_destination(location)

        buffer = get_or_create_buffer_cb(file_path)

        self.add_jump()
        self.change_buffer(buffer)
        self.move_cursor_to_buf_location(file_col, file_line)
        self.add_jump()
        self.align_center()

    def _screen_move(self, x, y):
        x_margin = self.content_position[0] - self.position[0]
        y_margin = self.content_position[1] - self.position[1]
        if x >= self.width - x_margin: return
        if y >= self.content_height - y_margin: return

        self.screen.move_cursor(    self.content_position[1] + y,
                                    self.content_position[0] + x)

    def _screen_clear_line_raw(self, y):
        if y >= self.height: return

        self.screen.clear_line(y)

    def _screen_clear_line(self, y):
        y_margin = self.content_position[1] - self.position[1]
        if y >= self.content_height - y_margin: return

        self.screen.clear_line(self.content_position[1] + y)

    def _screen_clear_line_partial(self, y, start_x, end_x):
        x_margin = self.content_position[0] - self.position[0]
        y_margin = self.content_position[1] - self.position[1]

        if y >= self.content_height - y_margin: return
        if start_x >= self.width - x_margin: return
        if end_x > self.width - x_margin:
            end_x = self.width - x_margin

        self.screen.clear_line_partial( self.content_position[1] + y,
                                        self.content_position[0] + start_x,
                                        self.content_position[0] + end_x)

    def _screen_write_raw(self, x, y, string, style, to_flush=True):
        if x >= self.width: return
        if y >= self.height: return

        # optimize in casa of a very long lines..
        if x + len(string) - 1 >= self.width: string = string[:self.width]

        if x + self._expanded_string_len(string) - 1 >= self.width:
            space_for = self.width - x
            while self._expanded_string_len(string) - 1 >= space_for:
                string  = string[:-1]

        tabs = [m.start() for m in re.finditer('\t', string)]
        if len(tabs) == 0:
            self.screen.write(  self.position[1] + y,
                                self.position[0] + x,
                                string,
                                style,
                                to_flush=to_flush)
            return

        # tab_style = get_scope_style('meta.embedded')
        tab_style = get_scope_style('comment')

        if not tab_style:
            elog(f"failed to find style for tab", type="ERROR")
            return
        if 'reverse' in style: tab_style = style

        string_index = 0
        screen_index = 0
        for i in tabs:
            part = string[string_index:i]
            self.screen.write(  self.position[1] + y,
                                self.position[0] + x + screen_index,
                                part,
                                style,
                                to_flush=to_flush)
            string_index += len(part)
            screen_index += len(part)

            self.screen.write(  self.position[1] + y,
                                self.position[0] + x + screen_index,
                                get_setting("tab_representation"),
                                tab_style,
                                to_flush=to_flush)

            string_index += 1
            screen_index += len(get_setting("tab_representation"))
        if string_index <= len(string) - 1:
            part = string[string_index:]
            self.screen.write(  self.position[1] + y,
                                self.position[0] + x + screen_index,
                                part,
                                style,
                                to_flush=to_flush)

    def _screen_write(self, x, y, string, style, to_flush=True):
        try:
            x_margin = self.content_position[0] - self.position[0]
            y_margin = self.content_position[1] - self.position[1]
            if x >= self.width - x_margin: return
            if y >= self.content_height - y_margin: return

            self._screen_write_raw( x_margin + x,
                                    y_margin + y,
                                    string,
                                    style,
                                    to_flush=to_flush)
        except Exception as e:
            elog(f"Exception: {e}", type="ERROR")
            elog(f"traceback: {traceback.format_exc()}", type="ERROR")
