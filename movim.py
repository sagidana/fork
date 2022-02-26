#!/usr/bin/python3

import curses

def _main(stdscr):
    stdscr.clear()
    stdscr.refresh()

    Y, X = stdscr.getmaxyx()

    cursor_x = 0
    cursor_y = 0
    k = 0

    while True:
        if k == ord('j'):
            cursor_y += 1
        if k == ord('k'):
            cursor_y -= 1
        if k == ord('l'):
            cursor_x += 1
        if k == ord('h'):
            cursor_x -= 1

        cursor_x = max(0, cursor_x)
        cursor_x = min(X-1, cursor_x)
        cursor_y = max(0, cursor_y)
        cursor_y = min(Y-1, cursor_y)

        stdscr.move(cursor_y, cursor_x)

        # stdscr.addstr(str(c))

        stdscr.refresh() # refresh the screen

        k = stdscr.getch()

def main():
    curses.wrapper(_main)


if __name__ == "__main__":
    main()
