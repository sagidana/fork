#!/usr/bin/python3

from signal import signal, SIGWINCH
import curses

from buffer import Buffer
from window import Window
from tab import Tab


class Context():
    def __init__(self, stdscr):
        self.stdscr = stdscr

        self.HEIGHT, self.WIDTH = stdscr.getmaxyx()
        signal(SIGWINCH, self.screen_resize_handler)

        self.tabs = []
        self.windows = []
        self.buffers = []

        self.curr_tab = -1

    def _create_tab(self):
        self.tabs.append(Tab())
        self.curr_tab = len(self.tabs) - 1
        return self.tabs[-1]

    def bootstrap(self):
        tab = self._create_tab()

        self.cursor_x = 0
        self.cursor_y = 0

    def screen_resize_handler(self, signum, frame):
        self.HEIGHT, self.WIDTH = self.stdscr.getmaxyx()
        pass

    def on_key(self, key):
        # if curses.keyname(k).decode() == 'j':
        if key == ord('j'):
            self.cursor_y += 1
        elif key == ord('k'):
            self.cursor_y -= 1
        elif key == ord('l'):
            self.cursor_x += 1
        elif key == ord('h'):
            self.cursor_x -= 1

        try:
            self.stdscr.addstr(0, 0, f"KEY: {curses.keyname(key).decode()}")
        except Exception as e:
            pass

        self.cursor_x = max(0, self.cursor_x)
        self.cursor_x = min(self.WIDTH-1, self.cursor_x)
        self.cursor_y = max(0, self.cursor_y)
        self.cursor_y = min(self.HEIGHT-1, self.cursor_y)

        self.stdscr.move(self.cursor_y, self.cursor_x)

def _main(stdscr):
    context = Context(stdscr)
    context.bootstrap()

    stdscr.clear()
    stdscr.refresh()

    k = 0
    while True:
        stdscr.clear()

        context.on_key(k)

        stdscr.refresh() # refresh the screen
        k = stdscr.getch()

def main():
    curses.wrapper(_main)


if __name__ == "__main__":
    main()
