#!/usr/bin/python3

# VT100 escape codes:
# https://www.csie.ntu.edu.tw/~r92094/c++/VT100.html

from settings import g_settings
from log import elog
from events import *
from hooks import *

from signal import signal, SIGWINCH

from termios import tcgetattr, tcsetattr, TCSADRAIN
from sys import stdout, stdin
from tty import setraw


BACKGROUND_TRUE_COLOR = "\x1b[48;2;{}m"
FOREGROUND_TRUE_COLOR = "\x1b[38;2;{}m"
BACKGROUND_256_COLOR = "\x1b[48;5;{}m"
FOREGROUND_256_COLOR = "\x1b[38;5;{}m"

REVERSE = "\x1b[7m"
MOVE = "\x1b[{};{}H"

ECHO = "\x1b[28m"
NO_ECHO = "\x1b[8m"

WRAP = "\x1b[?7h"
NO_WRAP = "\x1b[?7l"

CURSOR_I_BEAM = "\x1b[6 q"
CURSOR_I_BEAM_BLINK = "\x1b[5 q"
CURSOR_UNDERLINE = "\x1b[4 q"
CURSOR_UNDERLINE_BLINK = "\x1b[3 q"
CURSOR_BLOCK = "\x1b[2 q"
CURSOR_BLOCK_BLINK = "\x1b[1 q"
CURSOR_RESET = "\x1b[0 q"

DIM = "\x1b[2m"
NO_DIM = "\x1b[22m"

SAVE_CURSOR = "\x1b[s"
RESTORE_CURSOR = "\x1b[u"

CLEAR_LINE = "\x1b[2K"
CLEAR = "\x1b[2J"


ENTER_KEY = 13
TAB_KEY = 9
ESC_KEY = 27
CTRL_W_KEY = 23
CTRL_L_KEY = 12
CTRL_D_KEY = 4
CTRL_U_KEY = 21
CTRL_H_KEY = 8
CTRL_J_KEY = 10
CTRL_K_KEY = 11
CTRL_R_KEY = 18
BACKSPACE_KEY = 127


def convert(a):
    r, g, b = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    return f"{r};{g};{b}"

def get_terminal_size():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)

    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        ### Use get(key[, default]) instead of a try/catch
        #try:
        #    cr = (env['LINES'], env['COLUMNS'])
        #except:
        #    cr = (25, 80)
    return int(cr[1]), int(cr[0])

class Screen():
    def screen_resize_handler(self, signum, frame):
        size = get_terminal_size()
        self.width, self.height = size
        Hooks.execute(ON_RESIZE, size)

    def __init__(self):
        size = get_terminal_size()
        self.width, self.height = size

        signal(SIGWINCH, self.screen_resize_handler)
        self._disable_wrap()

        self.fd = stdin.fileno()
        self.old_stdin_settings = tcgetattr(self.fd)
        setraw(self.fd)

    def __del__(self):
        tcsetattr(  self.fd, 
                    TCSADRAIN, 
                    self.old_stdin_settings)
        self._enable_wrap()

    def _write_to_stdout(self, to_write):
        stdout.write(to_write)
        stdout.flush()

    def get_key(self):
        try: return ord(stdin.read(1))
        except: return None

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def _enable_wrap(self):
        self._write_to_stdout(WRAP)

    def _disable_wrap(self):
        self._write_to_stdout(NO_WRAP)

    def _enable_echo(self):
        self._write_to_stdout(ECHO)

    def _disable_echo(self):
        self._write_to_stdout(NO_ECHO)

    def _save_cursor(self):
        self._write_to_stdout(SAVE_CURSOR)

    def _restore_cursor(self):
        self._write_to_stdout(RESTORE_CURSOR)

    def clear_line(self, y):
        self._save_cursor()

        self.move_cursor(y, 0)
        self._write_to_stdout(CLEAR_LINE)

        self._restore_cursor()

    def clear_line_partial(self, y, start_x, end_x):
        empty = " " * (end_x - start_x)
        self.write(y, start_x, empty)

    def clear(self):
        self._write_to_stdout(CLEAR)

    def set_cursor_i_beam(self):
        self._write_to_stdout(CURSOR_I_BEAM)

    def set_cursor_block_blink(self):
        self._write_to_stdout(CURSOR_BLOCK_BLINK)

    def move_cursor(self, y, x):
        y += 1; x += 1
        escape = MOVE.format(y, x)
        self._write_to_stdout(escape)

    def _set_style(self, style):
        if not style: style = {}
        fg =    style['foreground'] if 'foreground' in style else  \
                g_settings['theme']['colors']['editor.foreground']
        bg =    style['background'] if 'background' in style else  \
                g_settings['theme']['colors']['editor.background']

        if fg: self._write_to_stdout(FOREGROUND_TRUE_COLOR.format(convert(fg)))
        if bg: self._write_to_stdout(BACKGROUND_TRUE_COLOR.format(convert(bg)))

        if 'reverse' in style: 
            self._write_to_stdout(REVERSE)

    def write(self, y, x, string, style=None): 
        self._save_cursor()

        self.move_cursor(y, x)
        self._set_style(style)
        self._write_to_stdout(string)

        self._restore_cursor()


if __name__ == '__main__':
    screen = Screen()

    screen.clear()

    screen.write(0,0,
                "Hello World",
                # {"foreground": "#A6E22E"})
                {"foreground": "#F9262E"})

    screen.move_cursor(0,0)

    # screen._write_to_stdout("\x1b[5m") # set blink
    # screen._write_to_stdout("\x1b[25m") # set blink
    # screen._write_to_stdout("\x1b[4h") # set insert mod

    # screen._write_to_stdout("\x1b[6 q") # set i-beam
    # screen._write_to_stdout("\x1b[5 q") # set i-beam blnking
    # screen._write_to_stdout("\x1b[4 q") # set underline
    # screen._write_to_stdout("\x1b[3 q") # set underline blinking
    # screen._write_to_stdout("\x1b[2 q") # set block
    # screen._write_to_stdout("\x1b[1 q") # set block blinking
    # screen._write_to_stdout("\x1b[0 q") # reset
    
    # screen._write_to_stdout("\x1b[?17;14;224c")
    # screen._write_to_stdout("\x1b[?17;14;224c")
    # screen._write_to_stdout("\x1b[?16;1000]")
    # screen._write_to_stdout("\x1b[4h")
    # screen._write_to_stdout("\x1b[?16;20]")

    for i in range(1):
        c = screen.get_key()
        print(f"{c}")
