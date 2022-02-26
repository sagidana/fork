
from buffer import *

class Window():
    def __init__(self, buffer=None):
        if not buffer:
            self.buffer = Buffer()
        else:
            self.buffer = buffer
