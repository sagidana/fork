from settings import g_settings
from log import elog
from window import *
from hooks import *
from events import *
from idr import *

class Tab():
    def raise_event(func):
        def event_wrapper(*args):
            self = args[0]
            func_name = func.__name__
            event = f"on_tab_{func_name}_before"
            if event in self.events:
                for cb in self.events[event]: cb(self)
            func(args)
            event = f"on_tab_{func_name}_after"
            if event in self.events:
                for cb in self.events[event]: cb(self)

    def __init__(   self,
                    screen,
                    width,
                    height,
                    buffer=None):
        self.id = get_id(TAB_ID)
        self.screen = screen
        self.width = width
        self.height = height

        self.zoom_mode = False
        self.zoom_x = -1
        self.zoom_y = -1
        self.zoom_height = -1
        self.zoom_width = -1

        self.windows = []
        window = Window(self.screen,
                        self.width,
                        self.height,
                        position=(0,0),
                        buffer=buffer)
        self.add_window(window)

        self.events = {}

    def register_events(self, handlers):
        for event in handlers:
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(handlers[event])

    def _get_index_by_window(self, window):
        for index, win in enumerate(self.windows):
            if win == window: return index
        return None

    def _adjust_sizes(self):
        todo = []
        for index, curr in enumerate(self.windows):
            num_of_left_windows = 0
            num_of_right_windows = 0
            num_of_up_windows = 0
            num_of_down_windows = 0

            inner = curr
            while self._find_left_window(inner):
                num_of_left_windows += 1
                inner = self._find_left_window(inner)
            inner = curr
            while self._find_right_window(inner):
                num_of_right_windows += 1
                inner = self._find_right_window(inner)

            inner = curr
            while self._find_up_window(inner):
                num_of_up_windows += 1
                inner = self._find_up_window(inner)
            inner = curr
            while self._find_down_window(inner):
                num_of_down_windows += 1
                inner = self._find_down_window(inner)

            num_of_horizontal_windows = num_of_left_windows + num_of_right_windows + 1
            num_of_vertical_windows = num_of_up_windows + num_of_down_windows + 1

            width = self.width - num_of_horizontal_windows + 1
            height = self.height - num_of_vertical_windows + 1

            width = int(width / num_of_horizontal_windows)
            height = int(height / num_of_vertical_windows)

            x = (width + 1) * num_of_left_windows
            y = (height + 1) * num_of_up_windows

            item = (curr, x, y, width, height)
            todo.append(item)

        for curr, x, y, width, height in todo:
            curr.set_position(x, y)
            curr.resize(width, height)

    def _windows_distance(self, win_1, win_2):
        x_1 = win_1.position[0]
        y_1 = win_1.position[1]
        x_2 = win_2.position[0]
        y_2 = win_2.position[1]
        return ((((x_2 - x_1)**2) + ((y_2 - y_1)**2))**0.5)

    def _find_left_window(self, window):
        index = self._get_index_by_window(window)
        left_top_x = window.position[0]
        left_top_y = window.position[1]
        left_bot_x = left_top_x
        left_bot_y = left_top_y + window.height - 1

        found = None
        for curr_index, curr in enumerate(self.windows):
            if curr_index == index: continue
            curr_right_top_x = curr.position[0] + curr.width - 1
            curr_right_top_y = curr.position[1]
            curr_right_bot_x = curr_right_top_x
            curr_right_bot_y = curr_right_top_y + curr.height - 1

            if curr_right_top_x >= left_top_x: continue
            if curr_right_top_y >= left_bot_y: continue
            if curr_right_bot_y < left_top_y: continue

            if not found:
                found = curr
                continue

            if self._windows_distance(curr, window) < self._windows_distance(found, window):
                found = curr
        return found

    def _find_right_window(self, window):
        index = self._get_index_by_window(window)
        right_top_x = window.position[0] + window.width - 1
        right_top_y = window.position[1]
        right_bot_x = right_top_x
        right_bot_y = right_top_y + window.height - 1

        found = None
        for curr_index, curr in enumerate(self.windows):
            if curr_index == index: continue
            curr_left_top_x = curr.position[0]
            curr_left_top_y = curr.position[1]
            curr_left_bot_x = curr_left_top_x
            curr_left_bot_y = curr_left_top_y + curr.height - 1

            if curr_left_top_x <= right_top_x: continue
            if curr_left_top_y >= right_bot_y: continue
            if curr_left_bot_y < right_top_y: continue

            if not found:
                found = curr
                continue

            if self._windows_distance(curr, window) < self._windows_distance(found, window):
                found = curr
        return found

    def _find_up_window(self, window):
        index = self._get_index_by_window(window)
        top_left_x = window.position[0]
        top_left_y = window.position[1]
        top_right_x = top_left_x + window.width - 1
        top_right_y = top_left_y

        found = None
        for curr_index, curr in enumerate(self.windows):
            if curr_index == index: continue
            curr_bot_left_x = curr.position[0]
            curr_bot_left_y = curr.position[1] + curr.height - 1
            curr_bot_right_x = curr_bot_left_x + curr.width - 1
            curr_bot_right_y = curr_bot_left_y

            if curr_bot_left_y >= top_left_y: continue
            if curr_bot_left_x >= top_right_x: continue
            if curr_bot_right_x <= top_left_x: continue

            if not found:
                found = curr
                continue

            if self._windows_distance(curr, window) < self._windows_distance(found, window):
                found = curr
        return found

    def _find_down_window(self, window):
        index = self._get_index_by_window(window)
        bot_left_x = window.position[0]
        bot_left_y = window.position[1] + window.height - 1
        bot_right_x = bot_left_x + window.width - 1
        bot_right_y = bot_left_y

        found = None
        for curr_index, curr in enumerate(self.windows):
            if curr_index == index: continue
            curr_top_left_x = curr.position[0]
            curr_top_left_y = curr.position[1]
            curr_top_right_x = curr_top_left_x + curr.width - 1
            curr_top_right_y = curr_top_left_y

            if curr_top_left_y <= bot_left_y: continue
            if curr_top_left_x >= bot_right_x: continue
            if curr_top_right_x <= bot_left_x: continue

            if not found:
                found = curr
                continue

            if self._windows_distance(curr, window) < self._windows_distance(found, window):
                found = curr
        return found

    def resize(self, width, height):
        self.width = width
        self.height = height

        self._adjust_sizes()

    def set_curr_window(self, index):
        self.curr_window_index = index

    def get_curr_window(self):
        return self.windows[self.curr_window_index]

    def remove_window(self, window):
        if self.zoom_mode: self.zoom_toggle()
        index = self._get_index_by_window(window)
        if index is False: return # distinguish False from 0

        self.windows.pop(index)

        if len(self.windows) == 0: raise Exception('close tab')
        if index == self.curr_window_index: self.set_curr_window(0)

        self._adjust_sizes()

    def add_window(self, window):
        if self.zoom_mode: self.zoom_toggle()
        index = len(self.windows)

        self.windows.append(window)
        self.set_curr_window(index)

        self._adjust_sizes()

    def focus_window(self, window):
        index = self._get_index_by_window(window)
        if index is False: return # distinguish False from 0

        self.set_curr_window(index)

    def close_window(self, window):
        self.remove_window(window)
        window.close()
        self.draw()

    def move_to_left_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_left_window(self.get_curr_window())
        if not found: return False

        self.focus_window(found)
        self.get_curr_window().draw_cursor()
        return True

    def move_to_right_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_right_window(self.get_curr_window())
        if not found: return False

        self.focus_window(found)
        self.get_curr_window().draw_cursor()
        return True

    def move_to_up_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_up_window(self.get_curr_window())
        if not found: return False

        self.focus_window(found)
        self.get_curr_window().draw_cursor()
        return True

    def move_to_down_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_down_window(self.get_curr_window())
        if not found: return False

        self.focus_window(found)
        self.get_curr_window().draw_cursor()
        return True

    def split(self, buffer=None):
        if self.zoom_mode: self.zoom_toggle()
        curr_window = self.get_curr_window()
        window_cursor = [0,0]
        buffer_cursor = [0,0]
        jumpslist = list()

        if not buffer:
            buffer = curr_window.buffer
            window_cursor = curr_window.window_cursor
            buffer_cursor = curr_window.buffer_cursor
            jumpslist = curr_window.jumpslist


        total_height = curr_window.height

        height = int(total_height / 2)
        width = curr_window.width

        seperator_y = curr_window.position[1] + height

        self.draw_horizontal_seperator( seperator_y,
                                        curr_window.position[0],
                                        width)

        curr_window.resize(width, height)

        new_window = Window(    self.screen,
                                width,
                                height,
                                position=(  curr_window.position[0],
                                            curr_window.position[1] + height + 1),
                                buffer=buffer,
                                window_cursor=window_cursor,
                                buffer_cursor=buffer_cursor,
                                jumpslist=jumpslist)
        self.add_window(new_window)
        self.focus_window(new_window)

        self.draw()

    def vsplit(self):
        if self.zoom_mode: self.zoom_toggle()
        curr_window = self.get_curr_window()
        curr_buffer = curr_window.buffer

        height = curr_window.height
        width = int(curr_window.width / 2)

        seperator_x = curr_window.position[0] + width

        self.draw_vertical_seperator(   seperator_x,
                                        curr_window.position[1],
                                        height)

        curr_window.resize(width, height)

        new_window = Window(    self.screen,
                                width,
                                height,
                                position=(  curr_window.position[0] + width + 1,
                                            curr_window.position[1]),
                                buffer=curr_buffer,
                                window_cursor=curr_window.window_cursor,
                                buffer_cursor=curr_window.buffer_cursor,
                                jumpslist=curr_window.jumpslist)

        self.add_window(new_window)
        self.focus_window(new_window)

        self.draw()

    def draw_vertical_seperator(self, x, y, size):
        for i in range(size):
            self.screen.write(  y + i,
                                x,
                                " ",
                                {'background': g_settings['windows_separator_color']})

    def draw_horizontal_seperator(self, y, x, size):
        self.screen.write(  y,
                            x,
                            " "*size,
                            {'background': g_settings['windows_separator_color']})

    def draw_seperators(self):
        for index, curr in enumerate(self.windows):
            inner = curr
            while self._find_left_window(inner):
                self.draw_vertical_seperator(   inner.position[0] - 1,
                                                inner.position[1],
                                                inner.height)
                inner = self._find_left_window(inner)

            inner = curr
            while self._find_right_window(inner):
                self.draw_vertical_seperator(   inner.position[0] + inner.width,
                                                inner.position[1],
                                                inner.height)
                inner = self._find_right_window(inner)

            inner = curr
            while self._find_up_window(inner):
                self.draw_horizontal_seperator( inner.position[1] - 1,
                                                inner.position[0],
                                                inner.width)
                inner = self._find_up_window(inner)

            inner = curr
            while self._find_down_window(inner):
                self.draw_horizontal_seperator( inner.position[1] + inner.height,
                                                inner.position[0],
                                                inner.width)
                inner = self._find_down_window(inner)

    def zoom_toggle(self):
        if self.zoom_mode:
            curr = self.get_curr_window()

            curr.set_position(self.zoom_x, self.zoom_y)
            curr.resize(self.zoom_width, self.zoom_height)

            self.zoom_x = -1
            self.zoom_y = -1
            self.zoom_height = -1
            self.zoom_width = -1
            self.zoom_mode = False
        else:
            curr = self.get_curr_window()

            self.zoom_x = curr.position[0]
            self.zoom_y = curr.position[1]
            self.zoom_height = curr.height
            self.zoom_width = curr.width

            curr.set_position(0, 0)
            curr.resize(self.width, self.height)

            self.zoom_mode = True
        self.draw()

    def draw(self):
        if self.zoom_mode:
            self.get_curr_window().draw()
        else:
            for window in self.windows:
                window.draw()
            self.draw_seperators()
        self.get_curr_window().draw_cursor()

        Hooks.execute(ON_DRAW_TAB, None)

