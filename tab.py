from window import *
from hooks import *
from events import *

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

    def on_window_move_up_after_callback(self, win):
        cursor = win.cursor
        Hooks.execute(ON_CURSOR_MOVE_AFTER, cursor)

    def on_window_move_down_after_callback(self, win):
        cursor = win.cursor
        Hooks.execute(ON_CURSOR_MOVE_AFTER, cursor)

    def on_window_move_right_after_callback(self, win):
        cursor = win.cursor
        Hooks.execute(ON_CURSOR_MOVE_AFTER, cursor)

    def on_window_move_left_after_callback(self, win):
        cursor = win.cursor
        Hooks.execute(ON_CURSOR_MOVE_AFTER, cursor)

    def on_resize_callbak(self, size):
        self.width = size[0]
        self.height = size[1]

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.windows = []
        window = Window(self.width, self.height)

        handlers = {}
        handlers[ON_WINDOW_MOVE_UP_AFTER] = self.on_window_move_up_after_callback
        handlers[ON_WINDOW_MOVE_DOWN_AFTER] = self.on_window_move_down_after_callback
        handlers[ON_WINDOW_MOVE_RIGHT_AFTER] = self.on_window_move_right_after_callback
        handlers[ON_WINDOW_MOVE_LEFT_AFTER] = self.on_window_move_left_after_callback 

        window.register_events(handlers)

        self.events = {}
        self.windows.append(window)
        self.curr_window = 0

        Hooks.register(ON_RESIZE, self.on_resize_callbak)

    def register_events(self, handlers):
        for event in handlers:
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(handlers[event])

    def draw(self):
        pass

    def get_curr_window(self):
        return self.windows[self.curr_window]
