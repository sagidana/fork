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
        self.cursor = [0,0]

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
        self.cursor[1] -= 1
        self.cursor[1] = max(0, self.cursor[1])

    @raise_event
    def move_down(self):
        self.cursor[1] += 1
        self.cursor[1] = min(   self.height - 1, 
                                self.cursor[1])

    @raise_event
    def move_right(self):
        self.cursor[0] += 1
        self.cursor[0] = min(   self.width - 1, 
                                self.cursor[0])
    @raise_event
    def move_left(self):
        self.cursor[0] -= 1
        self.cursor[0] = max(0, self.cursor[0])
