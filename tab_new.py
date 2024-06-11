from settings import *
from log import elog
from window import *
from hooks import *
from events import *
from idr import *

SINGLE = 1
HORIZONTAL= 2
VERTICAL = 3

class WinNode:
    def __init__(   self,
                    x,
                    y,
                    width,
                    height,
                    window=None,
                    orientation=SINGLE):
        self.parent = None
        self.orientation = orientation
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.children = []
        self.window = window

    def add_child(self, child):
        self.children.append(child)

    def del_child(self, child):
        if child in self.children:
            self.children.remove(child)

def iter_windows_tree(node):
    reached_root = False
    cursor = node
    while not reached_root:
        # cb(cursor)
        yield cursor

        if len(cursor.children) > 0:
            cursor = cursor.children[0]
            continue

        parent = cursor.parent
        if not parent:
            reached_root = True
            continue

        curr_index = parent.children.index(cursor)

        if len(parent.children) - 1 > curr_index:
            cursor = parent.children[curr_index + 1]
            continue

        retracing = True
        while retracing:
            parent = cursor.parent
            if not parent:
                retracing = False
                reached_root = True
            else:
                curr_index = parent.children.index(cursor)
                if len(parent.children) - 1 > curr_index:
                    cursor = parent.children[curr_index + 1]
                    retracing = False
                else:
                    cursor = parent

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

        window = Window(self,
                        self.screen,
                        self.width,
                        self.height,
                        position=(0,0),
                        buffer=buffer)

        self.root = WinNode(0, 0, self.width, self.height, window)
        self.curr_winnode = self.root

        self.events = {}

    def get_curr_window(self): return self.curr_winnode.window
    def get_winnode_by_window(self, window):
        for winnode in iter_windows_tree(self.root):
            if winnode.window == window:
                return winnode
        return None

    def hide(self): self.visible = False
    def show(self): self.visible = True

    def register_events(self, handlers):
        for event in handlers:
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(handlers[event])

    def resize(self, width, height):
        self.width = width
        self.height = height

        # TODO: self._adjust_sizes()

    def is_window_visible(self, window_id):
        if not self.visible: return False
        if not self.zoom_mode: return True
        return window_id == self.curr_winnode.window.id

    def _remove_window(self, window):
        if self.zoom_mode: self.zoom_toggle()
        index = self._get_index_by_window(window)
        if index is False: return # distinguish False from 0

        self.windows.pop(index)

        if len(self.windows) == 0: raise Exception('close tab')
        if index == self.curr_window_index: self.set_curr_window(0)

        # self._adjust_sizes()

    def focus_window(self, winnode):
        self.curr_winnode = winnode

    def _resize_winnode(self, winnode, width, height):
        pass

    def _remove_winnode(self, winnode):
        parent = winnode.parent
        if not parent: return

        num_of_siblings = len(parent.children) - 1

        if num_of_siblings == 0:
            self._remove_winnode(parent)
            return

        parent.children.remove(winnode)

        if parent.orientation == HORIZONTAL:
            elog("HORIZONTAL")
            new_width = int(parent.width / num_of_siblings)
            last_width = int(parent.width / num_of_siblings) + (parent.width % num_of_siblings)
            for child in parent.children[:-1]:
                child.width = new_width
                child.window.resize(child.width, child.height)

            parent.children[-1].width = last_width
            parent.children[-1].window.resize(parent.children[-1].width, parent.children[-1].height)

        if parent.orientation == VERTICAL:
            elog("VERTICAL")
            new_height = int(parent.height / num_of_siblings)
            last_height = int(parent.height / num_of_siblings) + (parent.height % num_of_siblings)
            for child in parent.children[:-1]:
                child.height = new_height
                child.window.resize(child.width, child.height)

            parent.children[-1].height = last_height
            parent.children[-1].window.resize(parent.children[-1].width, parent.children[-1].height)

    def close_window(self, window):
        winnode = self.get_winnode_by_window(window)
        if not winnode: return

        self._remove_winnode(winnode)

        window.close()
        self.draw()

    def _windows_distance(self, win_1, win_2):
        x_1 = win_1.position[0]
        y_1 = win_1.position[1]
        x_2 = win_2.position[0]
        y_2 = win_2.position[1]
        return ((((x_2 - x_1)**2) + ((y_2 - y_1)**2))**0.5)

    def _find_left_window(self, window):
        left_top_x = window.position[0]
        left_top_y = window.position[1]
        left_bot_x = left_top_x
        left_bot_y = left_top_y + window.height - 1

        found = None
        for curr_index, winnode in enumerate(iter_windows_tree(self.root)):
            curr = winnode.window
            if not curr: continue
            if curr == window: continue
            curr_right_top_x = curr.position[0] + curr.width - 1
            curr_right_top_y = curr.position[1]
            curr_right_bot_x = curr_right_top_x
            curr_right_bot_y = curr_right_top_y + curr.height - 1

            if curr_right_top_x >= left_top_x: continue
            if curr_right_top_y >= left_bot_y: continue
            if curr_right_bot_y < left_top_y: continue

            if not found:
                found = winnode
                continue

            if self._windows_distance(curr, window) < self._windows_distance(found.window, window):
                found = winnode
        return found

    def _find_right_window(self, window):
        right_top_x = window.position[0] + window.width - 1
        right_top_y = window.position[1]
        right_bot_x = right_top_x
        right_bot_y = right_top_y + window.height - 1

        found = None
        for curr_index, winnode in enumerate(iter_windows_tree(self.root)):
            curr = winnode.window
            if not curr: continue
            if curr == window: continue
            curr_left_top_x = curr.position[0]
            curr_left_top_y = curr.position[1]
            curr_left_bot_x = curr_left_top_x
            curr_left_bot_y = curr_left_top_y + curr.height - 1

            if curr_left_top_x <= right_top_x: continue
            if curr_left_top_y >= right_bot_y: continue
            if curr_left_bot_y < right_top_y: continue

            if not found:
                found = winnode
                continue

            if self._windows_distance(curr, window) < self._windows_distance(found.window, window):
                found = winnode
        return found

    def _find_up_window(self, window):
        top_left_x = window.position[0]
        top_left_y = window.position[1]
        top_right_x = top_left_x + window.width - 1
        top_right_y = top_left_y

        found = None
        for curr_index, winnode in enumerate(iter_windows_tree(self.root)):
            curr = winnode.window
            if not curr: continue
            if curr == window: continue
            curr_bot_left_x = curr.position[0]
            curr_bot_left_y = curr.position[1] + curr.height - 1
            curr_bot_right_x = curr_bot_left_x + curr.width - 1
            curr_bot_right_y = curr_bot_left_y

            if curr_bot_left_y >= top_left_y: continue
            if curr_bot_left_x >= top_right_x: continue
            if curr_bot_right_x <= top_left_x: continue

            if not found:
                found = winnode
                continue

            if self._windows_distance(curr, window) < self._windows_distance(found.window, window):
                found = winnode
        return found

    def _find_down_window(self, window):
        bot_left_x = window.position[0]
        bot_left_y = window.position[1] + window.height - 1
        bot_right_x = bot_left_x + window.width - 1
        bot_right_y = bot_left_y

        found = None
        for curr_index, winnode in enumerate(iter_windows_tree(self.root)):
            curr = winnode.window
            if not curr: continue
            if curr == window: continue
            curr_top_left_x = curr.position[0]
            curr_top_left_y = curr.position[1]
            curr_top_right_x = curr_top_left_x + curr.width - 1
            curr_top_right_y = curr_top_left_y

            if curr_top_left_y <= bot_left_y: continue
            if curr_top_left_x >= bot_right_x: continue
            if curr_top_right_x <= bot_left_x: continue

            if not found:
                found = winnode
                continue

            if self._windows_distance(curr, window) < self._windows_distance(found.window, window):
                found = winnode
        return found

    def focus_to_left_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_left_window(self.curr_winnode.window)
        if not found: return False

        self.focus_window(found)
        self.curr_winnode.window.draw_cursor()
        return True

    def focus_to_right_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_right_window(self.curr_winnode.window)
        if not found: return False

        self.focus_window(found)
        self.curr_winnode.window.draw_cursor()
        return True

    def focus_to_up_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_up_window(self.curr_winnode.window)
        if not found: return False

        self.focus_window(found)
        self.curr_winnode.window.draw_cursor()
        return True

    def focus_to_down_window(self):
        if self.zoom_mode: self.zoom_toggle()
        found = self._find_down_window(self.curr_winnode.window)
        if not found: return False

        self.focus_window(found)
        self.curr_winnode.window.draw_cursor()
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
            curr = self.curr_winnode.window

            curr.set_position(self.zoom_x, self.zoom_y)
            curr.resize(self.zoom_width, self.zoom_height)

            self.zoom_x = -1
            self.zoom_y = -1
            self.zoom_height = -1
            self.zoom_width = -1
            self.zoom_mode = False
        else:
            curr = self.curr_winnode.window

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
            self.curr_winnode.window.draw()
        else:
            for winnode in iter_windows_tree(self.root):
                if not winnode.window: continue
                winnode.window.draw()
            # def _draw(winnode):
                # if not winnode.window: return
                # winnode.window.draw()
            # traverse_windows_tree(self.root, _draw)

            # for window in self.windows:
                # window.draw()
            # self.screen.disable_cursor()
            # self.draw_seperators()
            # self.screen.enable_cursor()
        # self.curr_winnode.window.draw_cursor()

        Hooks.execute(ON_DRAW_TAB, None)

    def close(self):
        for window in self.windows:
            window.close()

    def _adjust_sizes(self):
        pass

    def split(self, buffer=None):
        curr_window = self.curr_winnode.window
        if not buffer:
            buffer = curr_window.buffer
            window_cursor = curr_window.window_cursor
            buffer_cursor = curr_window.buffer_cursor
            jumpslist = curr_window.jumpslist
        else:
            window_cursor = [0,0]
            buffer_cursor = [0,0]
            jumpslist = list()

        x = self.curr_winnode.x
        y = self.curr_winnode.y
        width = self.curr_winnode.width
        height = self.curr_winnode.height

        left_width = int(width / 2)
        left_height = height
        left_x = x
        left_y = y

        right_width = int(width / 2) + (width % 2)
        right_height = height
        right_x = x + int(width / 2)
        right_y = y

        # add seperator
        right_width -= 1
        right_x += 1

        self.curr_winnode.window.resize(left_width, left_height)
        left = WinNode(left_x,
                       left_y,
                       left_width,
                       left_height,
                       self.curr_winnode.window)

        new_window = Window(    self,
                                self.screen,
                                right_width,
                                right_height,
                                position=(  right_x,
                                            right_y),
                                buffer=buffer,
                                window_cursor=window_cursor,
                                buffer_cursor=buffer_cursor,
                                jumpslist=jumpslist)
        right = WinNode(   right_x,
                           right_y,
                           right_width,
                           right_height,
                           new_window)

        self.curr_winnode.window = None
        self.curr_winnode.orientation = HORIZONTAL
        self.curr_winnode.children.append(left)
        self.curr_winnode.children.append(right)
        left.parent = self.curr_winnode
        right.parent = self.curr_winnode
        self.curr_winnode = right

        self.draw()

    def vsplit(self, buffer=None):
        curr_window = self.curr_winnode.window
        if not buffer:
            buffer = curr_window.buffer
            window_cursor = curr_window.window_cursor
            buffer_cursor = curr_window.buffer_cursor
            jumpslist = curr_window.jumpslist
        else:
            window_cursor = [0,0]
            buffer_cursor = [0,0]
            jumpslist = list()

        x = self.curr_winnode.x
        y = self.curr_winnode.y
        width = self.curr_winnode.width
        height = self.curr_winnode.height

        up_width = width
        up_height = int(height/ 2)
        up_x = x
        up_y = y

        down_width = width
        down_height = int(height / 2) + (height % 2)
        down_x = x
        down_y = y + int(height / 2)

        # add seperator
        down_height -= 1
        down_y += 1

        self.curr_winnode.window.resize(up_width, up_height)
        up = WinNode(  up_x,
                       up_y,
                       up_width,
                       up_height,
                       self.curr_winnode.window)

        new_window = Window(    self,
                                self.screen,
                                down_width,
                                down_height,
                                position=(  down_x,
                                            down_y),
                                buffer=buffer,
                                window_cursor=window_cursor,
                                buffer_cursor=buffer_cursor,
                                jumpslist=jumpslist)
        down = WinNode(   down_x,
                          down_y,
                          down_width,
                          down_height,
                          new_window)

        self.curr_winnode.window = None
        self.curr_winnode.orientation = VERTICAL
        self.curr_winnode.children.append(up)
        self.curr_winnode.children.append(down)
        up.parent = self.curr_winnode
        down.parent = self.curr_winnode
        self.curr_winnode = down

        self.draw()

if __name__ == "__main__":
    from screen import *
    import traceback
    try:
        screen = Screen()
        buffer = Buffer("/tmp/editor.log")
        tab = Tab(screen, screen.width, screen.height, buffer)
        while True:
            tab.draw()
            key = screen.get_key()
            if key == ESC_KEY: break
            if key == ord('h'): # focus
                tab.focus_to_left_window()
            if key == ord('j'): # focus
                tab.focus_to_down_window()
            if key == ord('k'): # focus
                tab.focus_to_up_window()
            if key == ord('l'): # focus
                tab.focus_to_right_window()
            if key == ord('s'): # split
                tab.split()
            if key == ord('v'): # vsplit
                tab.vsplit()
            if key == ord('c'): # close
                tab.close_window(tab.get_curr_window())

            if key == ord('H'): pass # move
            if key == ord('J'): pass # move
            if key == ord('K'): pass # move
            if key == ord('L'): pass # move
            if key == ord('n'): pass # resize
            if key == ord('m'): pass # resize
            if key == ord(','): pass # resize
            if key == ord('.'): pass # resize
    except Exception as e:
        elog(f"Exception: {e}", type="ERROR")
        elog(f"traceback: {traceback.format_exc()}", type="ERROR")
