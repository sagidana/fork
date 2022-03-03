#!/usr/bin/python3

from signal import signal, SIGWINCH
import curses

from buffer import Buffer
from window import Window
from tab import Tab
from log import elog

from hooks import *
from events import *


NORMAL = 'normal'
INSERT = 'insert'
VISUAL = 'visual'
VISUAL_BLOCK = 'visual_block'
REPLACE = 'replace'

class Context():
    def on_buffer_destroy_after_callback(self, buf): 
        self.buffers.remove(buf)

    def on_buffer_create_after_callback(self, buf): 
        self.buffers.append(buf)

    def draw(self):
        self.get_curr_tab().draw()
        pass

    def initialize_maps(self):
        def q_map(self):
            return True
        self.maps[NORMAL][ord('q')] = q_map

        # Legends
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

        # Mainstream
        def w_map(self):
            self.get_curr_tab().get_curr_window().move_word()
            return False
        self.maps[NORMAL][ord('w')] = w_map
        def W_map(self):
            self.get_curr_tab().get_curr_window().move_WORD()
            return False
        self.maps[NORMAL][ord('W')] = W_map
        def b_map(self):
            self.get_curr_tab().get_curr_window().move_back()
            return False
        self.maps[NORMAL][ord('b')] = b_map
        def B_map(self):
            self.get_curr_tab().get_curr_window().move_BACK()
            return False
        self.maps[NORMAL][ord('B')] = B_map
        def e_map(self):
            self.get_curr_tab().get_curr_window().move_end()
            return False
        self.maps[NORMAL][ord('e')] = e_map
        def E_map(self):
            self.get_curr_tab().get_curr_window().move_END()
            return False
        self.maps[NORMAL][ord('E')] = E_map
        def f_map(self):
            self.get_curr_tab().get_curr_window().find()
            return False
        self.maps[NORMAL][ord('f')] = f_map
        def F_map(self):
            self.get_curr_tab().get_curr_window().find_back()
            return False
        self.maps[NORMAL][ord('F')] = F_map
        def t_map(self):
            self.get_curr_tab().get_curr_window().till()
            return False
        self.maps[NORMAL][ord('t')] = t_map
        def T_map(self):
            self.get_curr_tab().get_curr_window().till_back()
            return False
        self.maps[NORMAL][ord('T')] = T_map
        def o_map(self):
            self.get_curr_tab().get_curr_window().new_line()
            return False
        self.maps[NORMAL][ord('o')] = o_map
        def O_map(self):
            self.get_curr_tab().get_curr_window().new_line_before()
            return False
        self.maps[NORMAL][ord('O')] = O_map

        def ctrl_u_map(self):
            self.get_curr_tab().get_curr_window().scroll_up_half_page()
            return False
        self.maps[NORMAL][21] = ctrl_u_map
        def ctrl_d_map(self):
            self.get_curr_tab().get_curr_window().scroll_down_half_page()
            return False
        self.maps[NORMAL][4] = ctrl_d_map

    
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

    def _create_tab(self, buffer=None):
        self.tabs.append(Tab(self.stdscr, self.width, self.height, buffer))
        self.curr_tab = len(self.tabs) - 1

        # Tell movim to draw the newly created tab
        Hooks.execute(ON_DRAW_TAB, None)

        return self.tabs[-1]

    def get_curr_tab(self):
        return self.tabs[self.curr_tab]

    def bootstrap(self):
        buffer = Buffer('./editor.py')
        tab = self._create_tab(buffer)

    def screen_resize_handler(self, signum, frame):
        curses.endwin()
        curses.initscr()
        self.height, self.width = self.stdscr.getmaxyx()

        Hooks.execute(ON_RESIZE, (self.width, self.height))

    def on_key(self, key):
        try: elog(f"KEY: '{chr(key)}' -> ord({key}) -> {curses.keyname(key).decode()}")
        except Exception as e: pass

        if key in self.maps[self.mode]:
            return self.maps[self.mode][key](self)

def _main(stdscr):
    context = Context(stdscr)

    stdscr.clear()

    context.bootstrap()
    stdscr.refresh()

    k = 0
    while True:
        to_exit = context.on_key(k)
        if to_exit: break

        stdscr.refresh() # refresh the screen
        k = stdscr.getch()

def main():
    curses.wrapper(_main)


if __name__ == "__main__":
    main()
