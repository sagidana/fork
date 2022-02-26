#!/usr/bin/python3

from signal import signal, SIGWINCH
import curses

from buffer import Buffer
from window import Window
from tab import Tab

from hooks import *
from events import *


class Context():
    def on_cursor_move_after_callback(self, cursor):
        self.stdscr.move(cursor[1], cursor[0])

    def on_buffer_destroy_after_callback(self, buf): 
        self.buffers.remove(buf)

    def on_buffer_create_after_callback(self, buf): 
        self.buffers.append(buf)

    def draw(self):
        self.get_curr_tab().draw()

        # self.stdscr.addstr()
        pass

    def __init__(self, stdscr):
        self.stdscr = stdscr

        self.height, self.width = stdscr.getmaxyx()
        signal(SIGWINCH, self.screen_resize_handler)

        self.tabs = []
        self.windows = []
        self.buffers = []

        self.curr_tab = -1

        # Register to global events!
        Hooks.register(ON_BUFFER_CREATE_AFTER, self.on_buffer_create_after_callback)
        Hooks.register(ON_BUFFER_DESTROY_AFTER, self.on_buffer_destroy_after_callback)
        Hooks.register(ON_CURSOR_MOVE_AFTER, self.on_cursor_move_after_callback)

    def _create_tab(self):
        self.tabs.append(Tab(self.width, self.height))
        self.curr_tab = len(self.tabs) - 1
        return self.tabs[-1]

    def get_curr_tab(self):
        return self.tabs[self.curr_tab]

    def bootstrap(self):
        tab = self._create_tab()

        self.cursor_x = 0
        self.cursor_y = 0

    def screen_resize_handler(self, signum, frame):
        curses.endwin()
        curses.initscr()
        self.height, self.width = self.stdscr.getmaxyx()

        Hooks.execute(ON_RESIZE, (self.width, self.height))


    def on_key(self, key):
        # try:
            # self.stdscr.addstr(0, 0, f"KEY: {curses.keyname(key).decode()}")
        # except Exception as e:
            # pass

        if key == ord('j'):
            self.get_curr_tab().get_curr_window().move_down()
            # self.cursor_y += 1
        elif key == ord('k'):
            self.get_curr_tab().get_curr_window().move_up()
            # self.cursor_y -= 1
        elif key == ord('l'):
            self.get_curr_tab().get_curr_window().move_right()
            # self.cursor_x += 1
        elif key == ord('h'):
            self.get_curr_tab().get_curr_window().move_left()
            # self.cursor_x -= 1
        elif key == ord('q'):
            return True
        return False

def _main(stdscr):
    context = Context(stdscr)
    context.bootstrap()

    stdscr.clear()
    stdscr.refresh()

    k = 0
    while True:
        # stdscr.clear()

        to_exit = context.on_key(k)
        if to_exit: break

        stdscr.refresh() # refresh the screen
        k = stdscr.getch()

def main():
    curses.wrapper(_main)


if __name__ == "__main__":
    main()
