#!/usr/bin/python3

# VT100 escape codes:
# https://www.csie.ntu.edu.tw/~r92094/c++/VT100.html

from settings import g_settings
from log import elog
from events import *
from hooks import *

from signal import signal, SIGWINCH
from sys import stdout, stdin

BACKGROUND_TRUE_COLOR = "\x1b[48;2;{}m"
FOREGROUND_TRUE_COLOR = "\x1b[38;2;{}m"
BACKGROUND_256_COLOR = "\x1b[48;5;{}m"
FOREGROUND_256_COLOR = "\x1b[38;5;{}m"

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

def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch

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

    elog(f"cr: {cr}")
    # cr = ioctl_GWINSZ(0)
    # cr = ioctl_GWINSZ(1)
    # print(cr)
    # cr = ioctl_GWINSZ(2)
    # print(cr)
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
        elog(f"size: {size}")
        self.width, self.height = size
        Hooks.execute(ON_RESIZE, size)

    def __init__(self):
        size = get_terminal_size()
        self.width, self.height = size

        signal(SIGWINCH, self.screen_resize_handler)
        # self._disable_echo()
        self._disable_wrap()

        getch = _find_getch()
        def get_key(): return ord(getch())
        self.get_key = get_key

    def _write_to_stdout(self, to_write):
        stdout.write(to_write)
        stdout.flush()

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def _enable_wrap(self):
        escape = "\x1b[?7h"
        self._write_to_stdout(escape)

    def _disable_wrap(self):
        escape = "\x1b[?7l"
        self._write_to_stdout(escape)

    def _enable_echo(self):
        escape = "\x1b[28m"
        self._write_to_stdout(escape)

    def _disable_echo(self):
        escape = "\x1b[8m"
        self._write_to_stdout(escape)

    def _save_cursor(self):
        escape = f"\x1b[s"
        self._write_to_stdout(escape)

    def _restore_cursor(self):
        escape = f"\x1b[u"
        self._write_to_stdout(escape)

    def clear_line(self, y):
        self._save_cursor()

        self.move_cursor(y, 0)
        escape = f"\x1b[2K"
        self._write_to_stdout(escape)

        self._restore_cursor()

    def clear(self):
        escape = f"\x1b[2J"
        self._write_to_stdout(escape)

    def move_cursor(self, y, x):
        y += 1; x += 1
        escape = f"\x1b[{y};{x}H"
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
            escape = f"\x1b[7m"
            self._write_to_stdout(escape)

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

    for i in range(1000):
        c = screen.get_key()
        print(f"{c}")
