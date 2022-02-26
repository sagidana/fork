from window import *

class Tab():
    def __init__(self):
        self.windows = []
        self.windows.append(Window())
        self.curr_window = 0

    def get_curr_window(self):
        return self.windows[self.curr_window]
