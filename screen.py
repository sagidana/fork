#!/usr/bin/python3

from settings import g_settings
from log import elog
from events import *
from hooks import *

from signal import signal, SIGWINCH
from sys import stdout

BACKGROUND_TRUE_COLOR = "\x1b[48;2;{}m"
FOREGROUND_TRUE_COLOR = "\x1b[38;2;{}m"
BACKGROUND_256_COLOR = "\x1b[48;5;{}m"
FOREGROUND_256_COLOR = "\x1b[38;5;{}m"

def _screen_move(self, x, y): pass
def _screen_clear_line_raw(self, y): pass
def _screen_clear_line(self, y): pass
def _screen_style(self, x, y, size, style): pass
def _screen_write_raw(self, x, y, string, style): pass
def _screen_write(self, x, y, string, style): pass

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
        self.height, self.width = get_terminal_size()
        Hooks.execute(ON_RESIZE, (self.width, self.height))

    def __init__(self):
        self.height, self.width = get_terminal_size()

        signal(SIGWINCH, self.screen_resize_handler)

    def _write_to_stdout(self, to_write):
        stdout.write(to_write)
        stdout.flush()

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

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
        escape = f"\x1b[{y};{x}H"
        self._write_to_stdout(escape)

    def _set_style(self, style):
        fg =    style['foreground'] if 'foreground' in style else  \
                g_settings['theme']['colors']['editor.foreground']
        bg =    style['background'] if 'background' in style else  \
                g_settings['theme']['colors']['editor.background']

        if fg: self._write_to_stdout(BACKGROUND_TRUE_COLOR.format(convert(fg)))
        if bg: self._write_to_stdout(BACKGROUND_TRUE_COLOR.format(convert(bg)))

        if 'reverse' in style: 
            escape = f"\x1b[7m"
            self._write_to_stdout(escape)
        else:
            escape = f"\x1b[7m"
            self._write_to_stdout(escape)

    def write(self, y, x, string, style): 
        self._save_cursor()

        self.move_cursor(y, x)
        self._set_style(style)
        self._write_to_stdout(string)

        self._restore_cursor()

if __name__ == '__main__':
    screen = Screen()

    screen.clear()

    import time;time.sleep(1)

    screen.move_cursor(1,0)

    import time;time.sleep(1)
    
    screen.move_cursor(2,5)

    for i in range(1000):
        import time;time.sleep(1)
