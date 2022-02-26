#!/usr/bin/python3

from signal import signal, SIGWINCH
import curses

from buffer import Buffer
from window import Window
from tab import Tab

from hooks import *
from events import *


class Context():
    def on_buffer_destroy_callback1(self, buf): 
        self.buffers.remove(buf)
    def on_buffer_create_callback1(self, buf): 
        self.buffers.append(buf)

    def __init__(self, stdscr):
        self.stdscr = stdscr

        self.HEIGHT, self.WIDTH = stdscr.getmaxyx()
        signal(SIGWINCH, self.screen_resize_handler)

        self.tabs = []
        self.windows = []
        self.buffers = []

        self.curr_tab = -1

        # Register to global events!
        Hooks.register(ON_BUFFER_CREATE_END, self.on_buffer_create_callback1)
        Hooks.register(ON_BUFFER_DESTROY_END, self.on_buffer_destroy_callback1)


    def _create_tab(self):
        self.tabs.append(Tab())
        self.curr_tab = len(self.tabs) - 1
        return self.tabs[-1]

    def get_curr_tab(self):
        return self.tabs[self.curr_tab]

    def bootstrap(self):
        tab = self._create_tab()

        self.cursor_x = 0
        self.cursor_y = 0

    def screen_resize_handler(self, signum, frame):
        self.HEIGHT, self.WIDTH = self.stdscr.getmaxyx()

    def on_key(self, key):
        if key == ord('j'):
            # self.get_curr_tab().get_curr_window().move_down()
            self.cursor_y += 1
        elif key == ord('k'):
            self.cursor_y -= 1
        elif key == ord('l'):
            self.cursor_x += 1
        elif key == ord('h'):
            self.cursor_x -= 1
        elif key == ord('q'):
            return True
            
        try:
            self.stdscr.addstr(0, 0, f"KEY: {curses.keyname(key).decode()}")
        except Exception as e:
            pass

        self.stdscr.addstr(1, 0, f"{Hooks.registry}")
        self.stdscr.addstr(2, 0, f"{self.buffers}")

        self.cursor_x = max(0, self.cursor_x)
        self.cursor_x = min(self.WIDTH-1, self.cursor_x)
        self.cursor_y = max(0, self.cursor_y)
        self.cursor_y = min(self.HEIGHT-1, self.cursor_y)

        self.stdscr.move(self.cursor_y, self.cursor_x)
        return False

def _main(stdscr):
    context = Context(stdscr)
    context.bootstrap()

    stdscr.clear()
    stdscr.refresh()

    k = 0
    while True:
        stdscr.clear()

        to_exit = context.on_key(k)
        if to_exit: break

        stdscr.refresh() # refresh the screen
        k = stdscr.getch()

def main():
    curses.wrapper(_main)


if __name__ == "__main__":
    main()
