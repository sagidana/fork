from settings import *
from log import elog
from window import *
from hooks import *
from events import *
from idr import *

class Tab():
    def raise_event(func):
        def event_wrapper(*args):
            self = args[0]
            func_name = func.__name__
            event = f"on_tab_{func_name}_before"
            if event in self.events:
                for cb in self.events[event]: cb(self)
            func(args)
            event = f"on_tab_{func_name}_after"
            if event in self.events:
                for cb in self.events[event]: cb(self)

    def __init__(   self,
                    screen,
                    width,
                    height,
                    buffer=None):
        self.id = get_id(TAB_ID)
        self.screen = screen
        self.width = width
        self.height = height
        self.visible = True

        self.zoom_mode = False
        self.zoom_x = -1
        self.zoom_y = -1
        self.zoom_height = -1
        self.zoom_width = -1

        self.windows = []
        window = Window(self,
                        self.screen,
                        self.width,
                        self.height,
                        position=(0,0),
                        buffer=buffer)
        self.add_window(window)

        self.events = {}

    def hide(self): self.visible = False
    def show(self): self.visible = True

    def register_events(self, handlers):
        for event in handlers:
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(handlers[event])

    def _get_index_by_window(self, window):
        for index, win in enumerate(self.windows):
            if win == window: return index
        return None

    def resize(self, width, height):
        self.width = width
        self.height = height

        # self._adjust_sizes()

    def is_window_visible(self, window_id):
        if not self.visible: return False
        if not self.zoom_mode: return True
        return window_id == self.get_curr_window().id

    def set_curr_window(self, index):
        self.curr_window_index = index

    def get_curr_window(self):
        return self.windows[self.curr_window_index]

    def remove_window(self, window):
        if self.zoom_mode: self.zoom_toggle()
        index = self._get_index_by_window(window)
        if index is False: return # distinguish False from 0

        self.windows.pop(index)

        if len(self.windows) == 0: raise Exception('close tab')
        if index == self.curr_window_index: self.set_curr_window(0)

        # self._adjust_sizes()

    def add_window(self, window):
        if self.zoom_mode: self.zoom_toggle()
        index = len(self.windows)

        self.windows.append(window)
        self.set_curr_window(index)

        # self._adjust_sizes()

    def focus_window(self, window):
        index = self._get_index_by_window(window)
        if index is False: return # distinguish False from 0

        self.set_curr_window(index)

    def close_window(self, window):
        self.remove_window(window)
        window.close()
        self.draw()

    def focus_to_left_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_left_window(self.get_curr_window())
        if not found: return False

        self.focus_window(found)
        self.get_curr_window().draw_cursor()
        return True

    def focus_to_right_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_right_window(self.get_curr_window())
        if not found: return False

        self.focus_window(found)
        self.get_curr_window().draw_cursor()
        return True

    def focus_to_up_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_up_window(self.get_curr_window())
        if not found: return False

        self.focus_window(found)
        self.get_curr_window().draw_cursor()
        return True

    def focus_to_down_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_down_window(self.get_curr_window())
        if not found: return False

        self.focus_window(found)
        self.get_curr_window().draw_cursor()
        return True


    def draw_vertical_seperator(self, x, y, size):
        for i in range(size):
            self.screen.write(  y + i,
                                x,
                                " ",
                                {'background': get_setting('windows_separator_color')})

    def draw_horizontal_seperator(self, y, x, size):
        self.screen.write(  y,
                            x,
                            " "*size,
                            {'background': get_setting('windows_separator_color')})

    def draw_seperators(self):
        for index, curr in enumerate(self.windows):
            inner = curr
            while self._find_left_window(inner):
                self.draw_vertical_seperator(   inner.position[0] - 1,
                                                inner.position[1],
                                                inner.height)
                inner = self._find_left_window(inner)

            inner = curr
            while self._find_right_window(inner):
                self.draw_vertical_seperator(   inner.position[0] + inner.width,
                                                inner.position[1],
                                                inner.height)
                inner = self._find_right_window(inner)

            inner = curr
            while self._find_up_window(inner):
                self.draw_horizontal_seperator( inner.position[1] - 1,
                                                inner.position[0],
                                                inner.width)
                inner = self._find_up_window(inner)

            inner = curr
            while self._find_down_window(inner):
                self.draw_horizontal_seperator( inner.position[1] + inner.height,
                                                inner.position[0],
                                                inner.width)
                inner = self._find_down_window(inner)

    def zoom_toggle(self):
        if self.zoom_mode:
            curr = self.get_curr_window()

            curr.set_position(self.zoom_x, self.zoom_y)
            curr.resize(self.zoom_width, self.zoom_height)

            self.zoom_x = -1
            self.zoom_y = -1
            self.zoom_height = -1
            self.zoom_width = -1
            self.zoom_mode = False
        else:
            curr = self.get_curr_window()

            self.zoom_x = curr.position[0]
            self.zoom_y = curr.position[1]
            self.zoom_height = curr.height
            self.zoom_width = curr.width

            curr.set_position(0, 0)
            curr.resize(self.width, self.height)

            self.zoom_mode = True
        self.draw()

    def draw(self):
        if self.zoom_mode:
            self.get_curr_window().draw()
        else:
            for window in self.windows:
                window.draw()
            self.screen.disable_cursor()
            # self.draw_seperators()
            self.screen.enable_cursor()
        self.get_curr_window().draw_cursor()

        Hooks.execute(ON_DRAW_TAB, None)

    def close(self):
        for window in self.windows:
            window.close()

    def split(self, buffer=None):
        pass

    def vsplit(self, buffer=None):
        pass

if __name__ == "__main__":
    from screen import *
    try:
        screen = Screen()
        buffer = Buffer("/tmp/editor.log")
        tab = Tab(screen, 80, 80, buffer)
        while True:
            tab.draw()
            key = screen.get_key()
            if key == ESC_KEY: break
            if key == ord('s'): pass # split
            if key == ord('v'): pass # vsplit
            if key == ord('h'): pass # focus
            if key == ord('j'): pass # focus
            if key == ord('k'): pass # focus
            if key == ord('l'): pass # focus
            if key == ord('H'): pass # move
            if key == ord('J'): pass # move
            if key == ord('K'): pass # move
            if key == ord('L'): pass # move
            if key == ord('n'): pass # resize
            if key == ord('m'): pass # resize
            if key == ord(','): pass # resize
            if key == ord('.'): pass # resize
    except Exception as e:
        elog(f"Exception: {e}")
