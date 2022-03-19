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

        self.adjust_sizes()

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

    def _find_left_window(self, window): pass
    def _find_right_window(self, window): pass
    def _find_up_window(self, window): pass
    def _find_down_window(self, window): pass

    def set_curr_window(self, index):
        self.curr_window_index = index

    def get_curr_window(self):
        return self.windows[self.curr_window_index]

    def remove_window(self, window):
        pass

    def add_window(self, window):
        index = len(self.windows)

        self.windows.append(window)
        self.curr_window_index = index

    def focus_window(self, window):
        index = self._get_index_by_window(window)
        if not index: return 

        self.set_curr_window(index)

    def close_window(self, window):
        index = self._get_index_by_window(window)

        self.windows.pop(index)

        # TODO: if this is the last window close the tab.
        if len(self.windows) == 0: raise Exception('close tab')

        if index == self.curr_window_index: self.set_curr_window(0)

        # TODO fix sizes

    def move_left_window(self): 
        x = self.get_curr_window().position[0]
        y = self.get_curr_window().position[1]

        nearest = self.curr_window_index
        for index, window in enumerate(self.windows):
            if index == self.curr_window_index: continue
            curr_x = window.position[0]
            curr_y = window.position[1]

            if curr_x >= x: continue
            nearest = index

        self.set_curr_window(nearest)

    def move_right_window(self): 
        x = self.get_curr_window().position[0]
        y = self.get_curr_window().position[1]

        nearest = self.curr_window_index
        for index, window in enumerate(self.windows):
            if index == self.curr_window_index: continue
            curr_x = window.position[0]
            curr_y = window.position[1]

            if curr_x <= x: continue
            nearest = index

        self.set_curr_window(nearest)

    def move_up_window(self): 
        x = self.get_curr_window().position[0]
        y = self.get_curr_window().position[1]

        nearest = self.curr_window_index
        for index, window in enumerate(self.windows):
            if index == self.curr_window_index: continue
            curr_x = window.position[0]
            curr_y = window.position[1]

            if curr_y >= y: continue
            nearest = index

        self.set_curr_window(nearest)

    def move_down_window(self): 
        x = self.get_curr_window().position[0]
        y = self.get_curr_window().position[1]

        nearest = self.curr_window_index
        for index, window in enumerate(self.windows):
            if index == self.curr_window_index: continue
            curr_x = window.position[0]
            curr_y = window.position[1]

            if curr_y <= y: continue
            nearest = index

        self.set_curr_window(nearest)

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

