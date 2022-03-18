from log import elog
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

    def on_resize_callbak(self, size):
        self.width = size[0]
        self.height = size[1]

        elog(f"{size}")
        
        self.get_curr_window().resize(  self.width,
                                        self.height)

    def __init__(   self, 
                    stdscr, 
                    width, 
                    height, 
                    buffer=None):

        self.stdscr = stdscr
        self.width = width
        self.height = height

        self.windows = []
        window = Window(self.stdscr,
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

    def add_window(self, window):
        index = len(self.windows)

        self.windows.append(window)
        self.curr_window = index

    def split(self):
        elog('tab.split()')
        curr_window = self.get_curr_window()
        curr_buffer = curr_window.buffer

        height = int(curr_window.height / 2)
        width = curr_window.width

        curr_window.resize( width,
                            height)

        new_window = Window(    self.stdscr,
                                width, 
                                height, 
                                position=(  curr_window.position[0],
                                            curr_window.position[1] + height),
                                buffer=curr_buffer)
        self.add_window(new_window)

        curr_window.draw()
        new_window.draw()

    def vsplit(self):
        elog('tab.vsplit()')
        pass

    def draw(self):
        for window in self.windows:
            window.draw()

    def get_curr_window(self):
        return self.windows[self.curr_window]
