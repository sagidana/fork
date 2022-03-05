#!/usr/bin/python3

from signal import signal, SIGWINCH
from string import printable
import timeout_decorator
import argparse
import curses
import time
import re
import os

from buffer import Buffer
from window import Window
from log import elog
from tab import Tab

from events import *
from hooks import *

args = None

NORMAL = 'normal'
INSERT = 'insert'
VISUAL = 'visual'
VISUAL_BLOCK = 'visual_block'
REPLACE = 'replace'
MAP_TIMEOOUT = 2 # in seconds

class Context():
    def on_buffer_destroy_after_callback(self, buf): 
        self.buffers.remove(buf)

    def on_buffer_create_after_callback(self, buf): 
        self.buffers.append(buf)

    def draw(self):
        self.get_curr_tab().draw()
        pass

    @timeout_decorator.timeout(MAP_TIMEOOUT)
    def get_key_timeout(self):
        return self.stdscr.getch()

    def change_mode(self, target):
        if self.mode == INSERT and target == NORMAL:
            self.get_curr_window().change_end()
        if self.mode == NORMAL and target == INSERT:
            # in vim the transition from insert mode to normal mode causes the
            # cursor to move one index to the left. should I mimic this?
            self.get_curr_window().change_begin()

        self.mode = target

    def get_inner_key(self):
        try: return self.get_key_timeout()
        except: return None

    def _initialize_normal_legends_maps(self):
        # Legends
        def j_map(self):
            self.get_curr_window().move_down()
            return False
        self.maps[NORMAL][ord('j')] = j_map
        def k_map(self):
            self.get_curr_window().move_up()
            return False
        self.maps[NORMAL][ord('k')] = k_map
        def l_map(self):
            self.get_curr_window().move_right()
            return False
        self.maps[NORMAL][ord('l')] = l_map
        def h_map(self):
            self.get_curr_window().move_left()
            return False
        self.maps[NORMAL][ord('h')] = h_map

    def _initialize_normal_ctrl_maps(self):
        def ctrl_u_map(self):
            self.get_curr_window().scroll_up_half_page()
            return False
        self.maps[NORMAL][21] = ctrl_u_map
        def ctrl_d_map(self):
            self.get_curr_window().scroll_down_half_page()
            return False
        self.maps[NORMAL][4] = ctrl_d_map
        def ctrl_l_map(self):
            self.get_curr_window().draw()
            return False
        self.maps[NORMAL][12] = ctrl_l_map
        def ctrl_r_map(self):
            self.get_curr_window().redo()
            return False
        self.maps[NORMAL][18] = ctrl_r_map

    def _initialize_normal_symbol_maps(self):
        def zero_map(self):
            self.get_curr_window().move_line_begin()
            return False
        self.maps[NORMAL][ord('0')] = zero_map
        def dollar_map(self):
            self.get_curr_window().move_line_end()
            return False
        self.maps[NORMAL][ord('$')] = dollar_map

    def _initialize_normal_mainstream_maps(self):
        self.maps[NORMAL][ord('c')] = {}
        self.maps[NORMAL][ord('d')] = {}
        self.maps[NORMAL][ord('y')] = {}
        self.maps[NORMAL][ord('g')] = {}

        def yy_map(self):
            data = {}
            data["data"] = self.get_curr_window().get_curr_line()
            data["meta"] = "line" # to let the paste know the data is entire line.
            self.registers['"'] = data
            return False
        self.maps[NORMAL][ord('y')][ord('y')] = yy_map
        def dd_map(self):
            self.get_curr_window().change_begin()
            self.get_curr_window().remove_line()
            self.get_curr_window().change_end()
            return False
        self.maps[NORMAL][ord('d')][ord('d')] = dd_map
        def gg_map(self):
            self.get_curr_window().move_begin()
            return False
        self.maps[NORMAL][ord('g')][ord('g')] = gg_map
        def G_map(self):
            self.get_curr_window().move_end()
            return False
        self.maps[NORMAL][ord('G')] = G_map
        def w_map(self):
            self.get_curr_window().move_word_forward()
            return False
        self.maps[NORMAL][ord('w')] = w_map
        def W_map(self):
            self.get_curr_window().move_WORD_forward()
            return False
        self.maps[NORMAL][ord('W')] = W_map
        def b_map(self):
            self.get_curr_window().move_word_backward()
            return False
        self.maps[NORMAL][ord('b')] = b_map
        def B_map(self):
            self.get_curr_window().move_WORD_backward()
            return False
        self.maps[NORMAL][ord('B')] = B_map
        def e_map(self):
            self.get_curr_window().move_word_end()
            return False
        self.maps[NORMAL][ord('e')] = e_map
        def E_map(self):
            self.get_curr_window().move_WORD_end()
            return False
        self.maps[NORMAL][ord('E')] = E_map
        def f_map(self):
            self.get_curr_window().find()
            return False
        self.maps[NORMAL][ord('f')] = f_map
        def F_map(self):
            self.get_curr_window().find_back()
            return False
        self.maps[NORMAL][ord('F')] = F_map
        def t_map(self):
            self.get_curr_window().till()
            return False
        self.maps[NORMAL][ord('t')] = t_map
        def T_map(self):
            self.get_curr_window().till_back()
            return False
        self.maps[NORMAL][ord('T')] = T_map
        def o_map(self):
            self.change_mode(INSERT)
            self.get_curr_window().new_line_after()
            return False
        self.maps[NORMAL][ord('o')] = o_map
        def O_map(self):
            self.change_mode(INSERT)
            self.get_curr_window().new_line_before()
            return False
        self.maps[NORMAL][ord('O')] = O_map
        def A_map(self):
            self.change_mode(INSERT)
            self.get_curr_window().move_line_end()
            return False
        self.maps[NORMAL][ord('A')] = A_map
        def a_map(self):
            self.change_mode(INSERT)
            self.get_curr_window().move_right()
            return False
        self.maps[NORMAL][ord('a')] = a_map
        def I_map(self):
            self.change_mode(INSERT)
            self.get_curr_window().move_line_begin()
            return False
        self.maps[NORMAL][ord('I')] = I_map
        def i_map(self):
            self.change_mode(INSERT)
            return False
        self.maps[NORMAL][ord('i')] = i_map
        def X_map(self):
            self.get_curr_window().change_begin()
            self.get_curr_window().remove_char_special(self.get_curr_window().buffer_cursor[0])
            self.get_curr_window().change_end()
            return False
        self.maps[NORMAL][ord('X')] = X_map
        def x_map(self):
            self.get_curr_window().change_begin()
            self.get_curr_window().remove_char_special(self.get_curr_window().buffer_cursor[0] + 1)
            self.get_curr_window().change_end()
            return False
        self.maps[NORMAL][ord('x')] = x_map
        def P_map(self):
            self.get_curr_window().change_begin()
            data = self.registers['"']
            if data:
                if data['meta'] == 'line':
                    line = data['data']
                    self.get_curr_window().insert_line_before(line)
                elif data['meta'] == 'char': pass
                elif data['meta'] == 'block': pass
            self.get_curr_window().change_end()
            return False
        self.maps[NORMAL][ord('P')] = P_map
        def p_map(self):
            self.get_curr_window().change_begin()
            data = self.registers['"']
            if data:
                if data['meta'] == 'line':
                    line = data['data']
                    self.get_curr_window().insert_line_after(line)
                elif data['meta'] == 'char': pass
                elif data['meta'] == 'block': pass
            self.get_curr_window().change_end()
            return False
        self.maps[NORMAL][ord('p')] = p_map
        def u_map(self):
            self.get_curr_window().undo()
            return False
        self.maps[NORMAL][ord('u')] = u_map

        self._initialize_normal_ctrl_maps()
        self._initialize_normal_symbol_maps()

    def _initialize_normal_maps(self):
        def colon_map(self):
            return self.on_command()
        self.maps[NORMAL][ord(':')] = colon_map

        self._initialize_normal_legends_maps()
        self._initialize_normal_mainstream_maps()
        # self._initialize_normal_inner_maps()

    def _initialize_insert_maps(self): pass
    def _initialize_visual_maps(self): pass

    def initialize_maps(self):
        self._initialize_normal_maps()
        self._initialize_insert_maps()
        self._initialize_visual_maps()

    def initialize_registers(self):
        # we dont add all of vim's registers for now..

        # named registers
        for char in "abcdefghijklmnopqrstuvwxyz": self.registers[char] = None
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ": self.registers[char] = None
        # numbered registers
        for num in "0123456789": self.registers[num] = None
        # unamed register
        self.registers['"'] = None
        # last search pattern register
        self.registers['/'] = None

    def __init__(self, stdscr):
        self.stdscr = stdscr

        self.height, self.width = stdscr.getmaxyx()
        signal(SIGWINCH, self.screen_resize_handler)

        self.registers = {}
        self.initialize_registers()

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
    def get_curr_window(self):
        return self.get_curr_tab().get_curr_window()
    def get_curr_buffer(self):
        return self.get_curr_window().buffer

    def bootstrap(self):
        global args

        if not args.filename:
            raise Exception("No files provided.")

        elog(f"EDITOR: {args.filename}")

        if not os.path.isfile(args.filename[0]):
            raise Exception("No files provided.")
        file = args.filename[0]

        buffer = Buffer(file)
        tab = self._create_tab(buffer)

    def screen_resize_handler(self, signum, frame):
        curses.endwin()
        curses.initscr()
        self.height, self.width = self.stdscr.getmaxyx()

        Hooks.execute(ON_RESIZE, (self.width, self.height))

    def exec_command(self, command):
        if command == 'q': return True
        if command == 'w': 
            self.get_curr_window().buffer.write()
            pass
        return False

    def draw_command(self, command):
        command_position = [0, 0]

        command_position[1] = int(self.height - 1)
        command_length = self.width - 1
        

        cmd = f":{command}"
        self.stdscr.addstr( command_position[1], 
                            command_position[0],
                            cmd.ljust(command_length))
        self.stdscr.move(   command_position[1],
                            command_position[0] + len(cmd))

    def on_insert(self, key):
        ret = False

        if key == 263: # backslash
            self.get_curr_window().remove_char()
            return ret

        if key == 9: # tab
            # expand tab to spaces
            for i in range(4): self.get_curr_window().insert_char(' ')
            return ret

        try: 
            char = chr(key)
            if char in printable:
                self.get_curr_window().insert_char(char)
            else:
                elog(f"INSERT: ({key}) not printable.")
        except Exception as e: elog(f"Exception: {e}")
        return ret

    def on_command(self):
        ret = False
        command = ""
        self.draw_command(command)
        while True:
            self.stdscr.refresh() # refresh the screen
            key = self.stdscr.getch()

            if key == 27: break # esc
            if key == 263: command = command[:-1] # backslash
            if key == 10: # enter
                ret = self.exec_command(command)
                break
 
            try: elog(f"KEY: '{chr(key)}' -> ord({key}) -> {curses.keyname(key).decode()}")
            except Exception as e: elog(f"Exception: {e}")

            try: 
                char = chr(key)
                if re.match("[a-zA-Z 0-9-_()]", char): command += char
            except: pass
            self.draw_command(command)

        self.stdscr.refresh() # refresh the screen
        self.stdscr.clear()
        self.get_curr_tab().draw()
        return ret

    def on_key(self, key):
        try: elog(f"KEY: '{chr(key)}' -> ord({key}) -> {curses.keyname(key).decode()}")
        except Exception as e: pass

        if key == 27: # esc
            self.change_mode(NORMAL)
            return False

        if key in self.maps[self.mode]:
            curr = self.maps[self.mode]
            if callable(curr[key]): return curr[key](self)

            while key in curr and isinstance(curr[key], dict): 
                curr = curr[key]
                key = self.get_inner_key()

                if not key: break
                if key not in curr: break

            if key in curr: curr[key](self)

        if  self.mode == NORMAL and \
            ord('1') <= key <= ord('9'):
            elog(f"EDITOR: key: {chr(key)}")
            return False
            
        if self.mode == INSERT:
            return self.on_insert(key)

        return False


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
    global args

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='+')
    args = parser.parse_args()

    # remove the delay for the esc key!
    os.environ.setdefault('ESCDELAY', '25') 

    curses.wrapper(_main)


if __name__ == "__main__":
    main()