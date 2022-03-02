#!/usr/bin/python3

from signal import signal, SIGWINCH
import curses

from buffer import Buffer
from window import Window
from tab import Tab

from hooks import *
from events import *


NORMAL = 'normal'
INSERT = 'insert'
VISUAL = 'visual'
VISUAL_BLOCK = 'visual_block'
REPLACE = 'replace'

class Context():
    def on_draw_tab_callback(self, arg):
        index = 0
        for line in self.get_curr_tab().get_curr_window().buffer.lines:
            self.stdscr.addstr(index, 0, line)
            index += 1
        self.stdscr.move(0,0)

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

    def initialize_maps(self):
        # self.maps[NORMAL][ord('j')] = lambda s : s.get_curr_tab().get_curr_window.move_down()
        def j_map(self):
            self.get_curr_tab().get_curr_window().move_down()
            return False
        self.maps[NORMAL][ord('j')] = j_map
        def k_map(self):
            self.get_curr_tab().get_curr_window().move_up()
            return False
        self.maps[NORMAL][ord('k')] = k_map
        def l_map(self):
            self.get_curr_tab().get_curr_window().move_right()
            return False
        self.maps[NORMAL][ord('l')] = l_map
        def h_map(self):
            self.get_curr_tab().get_curr_window().move_left()
            return False
        self.maps[NORMAL][ord('h')] = h_map
        def q_map(self):
            return True
        self.maps[NORMAL][ord('q')] = q_map

    
    def __init__(self, stdscr):
        self.stdscr = stdscr

        self.height, self.width = stdscr.getmaxyx()
        signal(SIGWINCH, self.screen_resize_handler)

        self.maps = {}
        self.maps[NORMAL] = {}
        self.maps[INSERT] = {}
        self.maps[VISUAL] = {}
        self.maps[VISUAL_BLOCK] = {}
        self.maps[REPLACE] = {}
        self.mode = NORMAL # start in normal mode
        self.initialize_maps()

        self.tabs = []
        self.windows = []
        self.buffers = []

        self.curr_tab = -1

        # Register to global events!
        Hooks.register(ON_BUFFER_CREATE_AFTER, self.on_buffer_create_after_callback)
        Hooks.register(ON_BUFFER_DESTROY_AFTER, self.on_buffer_destroy_after_callback)
        Hooks.register(ON_CURSOR_MOVE_AFTER, self.on_cursor_move_after_callback)
        Hooks.register(ON_DRAW_TAB, self.on_draw_tab_callback)

    def _create_tab(self, buffer=None):
        self.tabs.append(Tab(self.width, self.height, buffer))
        self.curr_tab = len(self.tabs) - 1

        # Tell movim to draw the newly created tab
        Hooks.execute(ON_DRAW_TAB, None)

        return self.tabs[-1]

    def get_curr_tab(self):
        return self.tabs[self.curr_tab]

    def bootstrap(self):
        buffer = Buffer('/tmp/topics')
        tab = self._create_tab(buffer)

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

        if key in self.maps[self.mode]:
            return self.maps[self.mode][key](self)

def _main(stdscr):
    context = Context(stdscr)

    stdscr.clear()

    context.bootstrap()
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
