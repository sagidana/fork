from log import elog

from settings import g_settings
from screen import *


class Completion():
    def __init__(   self,
                    screen,
                    width,
                    height,
                    position,
                    options):
        self.screen = screen
        self.width = width
        self.height = height
        self.position = list(position)
        self.options = options
        self.selected = 0

    def pop(self):
        try:
            while True:
                self.draw()
                key = self.screen.get_key()
                if key != CTRL_N_KEY or key != CTRL_P_KEY: break

                if key == CTRL_N_KEY:
                    self.selected = (self.selected + 1) % len(self.options)
                if key == CTRL_P_KEY:
                    self.selected = (self.selected - 1) % len(self.options)
        except Exception as e: elog(f"Exception: {e}")

        return self.options[self.selected]

    def draw(self):
        try:
            style = {}
            style['background'] = g_settings['theme']['colors']['menu.background']
            style['foreground'] = g_settings['theme']['colors']['menu.foreground']
            selected_style = {}
            selected_style['background'] = g_settings['theme']['colors']['terminal.ansiMagenta']
            selected_style['foreground'] = g_settings['theme']['colors']['menu.foreground']

            for y, option in enumerate(self.options):
                if len(option)  + 1 < self.width:
                    line = f"{option}{' '*(self.width - len(option) - 1)}"
                option = option[:self.width]
                if y == self.selected:
                    self.__draw(0, y, f" {option}", selected_style)
                else:
                    self.__draw(0, y, f" {option}", style)
        except Exception as e: elog(f"Exception: {e}")

    def __draw(self, x, y, string, style):
        try:
            if x >= self.width: return
            if y >= self.height: return

            if x + len(string) - 1 >= self.width:
                space_for = self.width  - x
                string = string[:space_for]

            self.screen.write(  self.position[1]  + y,
                                self.position[0]  + x,
                                string,
                                style)
        except Exception as e:
            elog(f"Exception: {e}")
