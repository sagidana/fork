from log import elog

from settings import g_settings
from screen import *


class Completion():
    def __init__(   self,
                    screen,
                    position,
                    options):
        self.screen = screen
        self.position = list(position)
        self.options = options
        self.selected = 0
        self.orientation = "down"
        self.height, self.width = self._calculate_dimentions_and_orientation()

    def _calculate_dimentions_and_orientation(self):
        height = len(self.options)
        size_on_screen_down = self.screen.height - self.position[1]
        if len(self.options) > size_on_screen_down:
            size_on_screen_up = self.position[1]
            if size_on_screen_up > size_on_screen_down:
                height = size_on_screen_up
                self.orientation = "up"

        option_max_len = 0
        for option in self.options:
            if len(option) > option_max_len:
                option_max_len = len(option)
        size_on_screen_right = self.screen.width - self.position[0]
        width = min(option_max_len + 1, size_on_screen_right)

        return height, width

    def pop(self):
        try:
            while True:
                self.draw()
                key = self.screen.get_key()
                if key == ENTER_KEY:
                    return self.options[self.selected]
                elif key == CTRL_N_KEY:
                    self.selected = (self.selected + 1) % len(self.options)
                elif key == CTRL_P_KEY:
                    self.selected = (self.selected - 1) % len(self.options)
                else:
                    return None
        except Exception as e: elog(f"Exception: {e}")

    def draw(self):
        try:
            style = {}
            style['background'] = g_settings['theme']['colors']['menu.background']
            style['foreground'] = g_settings['theme']['colors']['menu.foreground']
            selected_style = {}
            selected_style['background'] = g_settings['theme']['colors']['terminal.ansiMagenta']
            selected_style['foreground'] = g_settings['theme']['colors']['menu.foreground']

            for y, option in enumerate(self.options):
                if len(option) < self.width:
                    option = f"{option}{' '*(self.width - len(option))}"
                option = option[:self.width]
                if y == self.selected:
                    self.__draw(0, y, f"{option}", selected_style)
                else:
                    self.__draw(0, y, f"{option}", style)
        except Exception as e: elog(f"Exception: {e}")

    def __draw(self, x, y, string, style):
        try:
            if x >= self.width: return
            if y >= self.height: return

            if x + len(string) - 1 >= self.width:
                space_for = self.width  - x
                string = string[:space_for]

            if self.orientation == "down":
                self.screen.write(  self.position[1] + y,
                                    self.position[0] + x,
                                    string,
                                    style)
            else: # up
                self.screen.write(  self.position[1] - y,
                                    self.position[0] + x,
                                    string,
                                    style)
        except Exception as e:
            elog(f"Exception: {e}")
