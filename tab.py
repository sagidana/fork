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

    def on_resize_callbak(self, size):
        self.width = size[0]
        self.height = size[1]

        self._adjust_sizes()

    def __init__(   self, 
                    screen, 
                    width, 
                    height, 
                    buffer=None):
        self.id = get_id(TAB_ID)
        self.screen = screen
        self.width = width
        self.height = height

        self.windows = []
        window = Window(self.screen,
                        self.width, 
                        self.height, 
                        position=(0,0),
                        buffer=buffer)
        self.add_window(window)

        self.events = {}
        Hooks.register(ON_RESIZE, self.on_resize_callbak)

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
        for index, curr in enumerate(self.windows):
            num_of_vertical_windows = 0
            num_of_horizontal_windows = 0

            inner = curr
            while self._find_left_window(inner):
                num_of_horizontal_windows += 1
                inner = self._find_left_window(inner)
            inner = curr
            while self._find_right_window(inner):
                num_of_horizontal_windows += 1
                inner = self._find_right_window(inner)

            inner = curr
            while self._find_up_window(inner):
                num_of_vertical_windows += 1
                inner = self._find_up_window(inner)
            inner = curr
            while self._find_down_window(inner):
                num_of_vertical_windows += 1
                inner = self._find_down_window(inner)
            
            num_of_horizontal_windows = max(num_of_horizontal_windows, 1)
            num_of_vertical_windows = max(num_of_vertical_windows, 1)

            curr.resize(int(self.width / num_of_horizontal_windows),
                        int(self.height / num_of_vertical_windows))

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

    def set_curr_window(self, index):
        self.curr_window_index = index

    def get_curr_window(self):
        return self.windows[self.curr_window_index]

    def remove_window(self, window):
        index = self._get_index_by_window(window)
        if not index: return 

        self.windows.pop(index)

        if len(self.windows) == 0: raise Exception('close tab')
        if index == self.curr_window_index: self.set_curr_window(0)

        self._adjust_sizes()

    def add_window(self, window):
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

        # TODO fix sizes

    def move_left_window(self): 
        found = self._find_left_window(self.get_curr_window())
        if not found: return False 

        self.focus_window(found)
        return True

    def move_right_window(self): 
        found = self._find_right_window(self.get_curr_window())
        if not found: return False 

        self.focus_window(found)
        return True

    def move_up_window(self): 
        found = self._find_up_window(self.get_curr_window())
        if not found: return False 

        self.focus_window(found)
        return True

    def move_down_window(self): 
        found = self._find_down_window(self.get_curr_window())
        if not found: return False 

        self.focus_window(found)
        return True

    def split(self):
        curr_window = self.get_curr_window()
        curr_buffer = curr_window.buffer

        height = int(curr_window.height / 2)
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
                                buffer=curr_buffer)
        self.add_window(new_window)
        self.focus_window(new_window)

        curr_window.draw()
        new_window.draw()

    def vsplit(self):
        curr_window = self.get_curr_window()
        curr_buffer = curr_window.buffer

        height = curr_window.height
        width = int(curr_window.width / 2)

        seperator_x = curr_window.position[0] + width

        self.draw_vertical_seperator(   curr_window.position[1], 
                                        seperator_x,
                                        height)

        curr_window.resize(width, height)

        new_window = Window(    self.screen,
                                width, 
                                height, 
                                position=(  curr_window.position[0] + width + 1,
                                            curr_window.position[1]),
                                buffer=curr_buffer)
        self.add_window(new_window)
        self.focus_window(new_window)

        curr_window.draw()
        new_window.draw()

    def draw_vertical_seperator(self, y, x, size):
        for i in range(size):
            self.screen.write(  y + i,
                                x,
                                " ",
                                {'background': '#000000'})

    def draw_horizontal_seperator(self, y, x, size):
        self.screen.write(  y, 
                            x,
                            " "*size,
                            {'background': '#000000'})
    
    def draw(self):
        for window in self.windows:
            window.draw()
        self.get_curr_window().draw_cursor()

