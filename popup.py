from log import elog

from treesitter import traverse_tree
from settings import g_settings
from screen import *
from os import path

from string import printable


class DetailsPopup():
    def __init__(self, editor):
        self.editor = editor
        self.screen = editor.screen

        buffer = self.editor.get_curr_buffer()
        curr_window = self.editor.get_curr_window()
        curr_tab = self.editor.get_curr_tab()

        x = curr_window.buffer_cursor[0]
        y = curr_window.buffer_cursor[1]
        status = f"current: [tab {curr_tab.id}] {curr_window.describe()} {y}:{x}"
        pending_tasks = self.editor.tasks
        self.details = []
        self.details.append(status)
        if len(pending_tasks) > 0:
            self.details.append("tasks")
            for task in pending_tasks:
                self.details.append(f"{g_settings['tab_insert']}- {task.id}")
        buffers = self.editor.buffers
        if len(buffers) > 0:
            self.details.append("buffers")
            for b in buffers:
                self.details.append(f"{g_settings['tab_insert']}- {b.describe()}")

        self.details.append("tabs")
        for tab in self.editor.tabs:
            self.details.append(f"{g_settings['tab_insert']}- [tab {tab.id}]")
            for window in tab.windows:
                self.details.append(f"{g_settings['tab_insert']*2}- {window.describe()}")

        width_margin = 5
        height_margin = 3
        self.position = list([width_margin, height_margin])
        self.width = self.screen.width - (width_margin * 2)
        self.height = self.screen.height - (height_margin * 2)

        if self.height - 2 > len(self.details): self.height = len(self.details) + 2
        else: self.details = self.details[:self.height - 2]

    def pop(self):
        self.draw()
        # wait for key to release
        self.screen.get_key()

    def draw(self):
        try:
            style = {}
            style['background'] = g_settings['theme']['colors']['menu.background']
            style['foreground'] = g_settings['theme']['colors']['menu.foreground']

            self.__draw_frame()

            for y in range(len(self.details)):
                self.__draw(1, y+1, f"{self.details[y]}", style)

            self.screen.flush()
        except Exception as e: elog(f"Exception: {e}")

    def __draw_frame(self):
        style = {}
        style['background'] = g_settings['theme']['colors']['menu.background']
        style['foreground'] = g_settings['theme']['colors']['menu.foreground']
        frame_style = {}
        frame_style['background'] = g_settings['theme']['colors']['terminal.ansiMagenta']
        frame_style['foreground'] = g_settings['theme']['colors']['menu.foreground']

        self.__draw(0,0," "*self.width, frame_style)
        for y in range(self.height-2):
            self.__draw(0, y+1, " ", frame_style)
            self.__draw(self.width-1, y+1, " ", frame_style)
            self.__draw(1, y+1, " "*(self.width-2), style)
        self.__draw(0,self.height-1," "*self.width, frame_style)

    def __draw(self, x, y, string, style):
        try:
            if x >= self.width: return
            if y >= self.height: return

            if x + len(string) - 1 >= self.width:
                space_for = self.width  - x
                string = string[:space_for]

            self.screen.write(  self.position[1] + y,
                                self.position[0] + x,
                                string,
                                style,
                                to_flush=False)
        except Exception as e: elog(f"Exception: {e}")

class CompletionPopup():
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

class TSNode():
    def __init__(self, node, level):
        self.node = node
        self.level = level

    def __str__(self):
        lines = self.node.text.decode('utf8').splitlines()
        text = lines[0] if len(lines) > 0 else ""
        return f"[{self.level}]{self.node.type}: {text}"

class TreeSitterPopup():
    def __init__(   self,
                    editor,
                    screen,
                    treesitter,
                    position):
        self.editor = editor
        self.screen = screen
        self.treesitter = treesitter
        self.position = position
        self.ret_node = None

        x = self.position[0]
        y = self.position[1]

        closest_node = self.treesitter.tree.root_node
        closest_level = 0

        def find_closest_node(node, level, nth_child):
            nonlocal closest_node
            nonlocal closest_level

            start_y, start_x = node.start_point
            end_y, end_x = node.end_point
            if start_y > y: return
            if end_y < y: return

            # we in lines range

            if start_y == end_y:
                if start_x > x: return
                if end_x < x: return

                if level > closest_level:
                    closest_node = node
                    closest_level = level
                return

            if start_y == y:
                if start_x > x: return

                if level > closest_level:
                    closest_node = node
                    closest_level = level
                return

            if end_y == y:
                if end_x < x: return
                if level > closest_level:
                    closest_node = node
                    closest_level = level
                return

            if level > closest_level:
                closest_node = node
                closest_level = level
            return
        traverse_tree(self.treesitter.tree, find_closest_node)

        self.nodes = []
        if not closest_node.parent:
            self.nodes = [TSNode(closest_node, closest_level)]
            self.selected = 0
        else:
            while True:
                prev = closest_node
                closest_node = closest_node.parent
                if not closest_node: break
                closest_level -= 1
                nodes = closest_node.children
                if len(nodes) > 0:
                    self.selected = nodes.index(prev)
                    self.nodes = [TSNode(node, closest_level + 1) for node in nodes]
                    break

        if len(self.nodes) == 0: raise Exception('should not happend')

        curr_window = self.editor.get_curr_window()
        width_margin = 5
        height_margin = 3
        self.position = list([  curr_window.position[0] + width_margin,
                                curr_window.position[1] + height_margin])
        self.width = curr_window.width - (width_margin * 2)
        self.height = curr_window.height - (height_margin * 2)

    def on_key(self, key):
        if key == ENTER_KEY:
            self.ret_node = self.nodes[self.selected].node
            return True
        if key == ord('h'):
            if not self.nodes[self.selected].node.parent:
                return False
            parent = self.nodes[self.selected].node.parent
            if parent.parent:
                siblings = parent.parent.children
                self.nodes = [TSNode(node, self.nodes[self.selected].level - 1) for node in siblings]
                self.selected = siblings.index(parent)
            else:
                self.nodes = [TSNode(parent, self.nodes[self.selected].level - 1)]
                self.selected = 0
            return False
        if key == ord('j'):
            if self.selected < len(self.nodes) - 1:
                self.selected += 1
            return False
        if key == ord('k'):
            if self.selected > 0:
                self.selected -= 1
            return False
        if key == ord('l'):
            if self.nodes[self.selected].node.children:
                new_nodes = self.nodes[self.selected].node.children
                if len(new_nodes) == 0: return False
                self.nodes = [TSNode(node, self.nodes[self.selected].level + 1) for node in new_nodes]
                self.selected = 0
            return False
        if key == CTRL_U_KEY:
            half = int(self.screen.height / 2)
            if self.selected < half: self.selected = 0
            else: self.selected -= half
            return False
        if key == CTRL_D_KEY:
            half = int(self.screen.height / 2)
            left = len(self.nodes) - self.selected - 1
            if left > half: self.selected += half
            else: self.selected += left
            return False
        if key == ord('g'):
            key = self.screen.get_key()
            if key == ord('g'):
                self.selected = 0
                return False
        if key == ord('G'):
            self.selected = len(self.nodes) - 1
            return False
        if key == ord('?'):
            pattern = ""
            success = False
            original_nodes = self.nodes
            original_selected = self.selected
            while True:
                filtered_nodes = []
                def search(node, level, nth_child):
                    nonlocal filtered_nodes
                    nonlocal pattern
                    node = TSNode(node, original_nodes[original_selected].level + level)
                    if pattern in str(node):
                        filtered_nodes.append(node)
                traverse_tree(original_nodes[original_selected].node, search)

                if len(filtered_nodes) > 0:
                    self.nodes = filtered_nodes
                    if self.selected >= len(self.nodes):
                        self.selected = len(self.nodes) - 1
                    self.draw()
                key = self.screen.get_key()

                if key == ENTER_KEY:
                    if len(pattern) > 0: success = True
                    break
                if key == ESC_KEY: break
                if key == BACKSPACE_KEY:
                    if len(pattern) > 0: pattern = pattern[:-1]
                else:
                    try:
                        char = chr(key)
                        if char in printable:
                            pattern += char
                        else: break
                    except: continue

            if not success:
                self.nodes = original_nodes
                self.selected = original_selected

            return False
        if key == ord('/'):
            pattern = ""
            success = False
            original_nodes = self.nodes
            original_selected = self.selected
            while True:
                key = self.screen.get_key()

                if key == ENTER_KEY:
                    if len(pattern) > 0: success = True
                    break
                if key == ESC_KEY: break
                if key == BACKSPACE_KEY:
                    if len(pattern) > 0: pattern = pattern[:-1]
                else:
                    try:
                        char = chr(key)
                        if char in printable:
                            pattern += char
                        else: break
                    except: continue
                filtered_nodes = [node for node in original_nodes if pattern in str(node)]
                if len(filtered_nodes) > 0:
                    self.nodes = filtered_nodes
                    if self.selected >= len(self.nodes):
                        self.selected = len(self.nodes) - 1
                    self.draw()
            if not success:
                self.nodes = original_nodes
                self.selected = original_selected

            return False
        try:
            if chr(key).isnumeric():
                target_level = int(chr(key))
                nodes = []
                def nodes_at_level(node, level, nth_child):
                    nonlocal nodes
                    nonlocal target_level
                    if level == target_level:
                        nodes.append(TSNode(node, level))
                    return
                traverse_tree(self.treesitter.tree, nodes_at_level)
                if len(nodes) > 0:
                    self.nodes = nodes
                    if self.selected >= len(self.nodes):
                        self.selected = len(self.nodes) - 1
                    self.draw()

                return False
        except Exception as e: elog(f"Exception: {e}")

        # exit popup if unkown key pressed
        return True

    def pop(self):
        try:
            while True:
                self.draw()

                key = self.screen.get_key()
                to_exit = self.on_key(key)
                if to_exit: break
        except Exception as e: elog(f"Exception: {e}")
        return self.ret_node

    def draw(self):
        try:
            style = {}
            style['background'] = g_settings['theme']['colors']['menu.background']
            style['foreground'] = g_settings['theme']['colors']['menu.foreground']
            selected_style = {}
            selected_style['background'] = g_settings['theme']['colors']['terminal.ansiMagenta']
            selected_style['foreground'] = g_settings['theme']['colors']['menu.foreground']

            for y in range(self.height):
                self.__draw(0, y, " "*self.width, style)

            if self.selected < self.height:
                for y, node in enumerate(self.nodes):
                    option = str(node)
                    if len(option) < self.width:
                        option = f"{option}{' '*(self.width - len(option))}"
                    option = option[:self.width]
                    if y == self.selected:
                        self.__draw(0, y, f"{option}", selected_style)
                    else:
                        self.__draw(0, y, f"{option}", style)
            else:
                index = self.selected
                for y in reversed(range(self.height)):
                    option = str(self.nodes[index])
                    if index == self.selected:
                        self.__draw(0, y, f"{option}", selected_style)
                    else:
                        self.__draw(0, y, f"{option}", style)
                    index -= 1
        except Exception as e: elog(f"Exception: {e}")
        self.screen.flush()

    def __draw(self, x, y, string, style):
        try:
            if x >= self.width: return
            if y >= self.height: return

            if x + len(string) - 1 >= self.width:
                space_for = self.width  - x
                string = string[:space_for]

            self.screen.write(  self.position[1] + y,
                                self.position[0] + x,
                                string,
                                style,
                                to_flush=False)
        except Exception as e: elog(f"Exception: {e}")

class LinesNode():
    def __init__(   self,
                    level,
                    line_num,
                    line_text,
                    parent=None,
                    children=None):
        self.level = level
        self.line_num = line_num
        self.line_text = line_text
        self.parent = parent
        if children: self.children = children
        else: self.children = []

def traverse_lines_tree(node, cb):
    reached_root = False
    cursor = node
    while not reached_root:
        cb(cursor)

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

class LinesPopup():
    def get_line_level(self, line):
        first_whitespaces = len(line) - len(line.lstrip())
        level = 0
        for ws in line[:first_whitespaces]:
            if ws == '\t': level += 4
            else: level += 1
        return int(level / 4)

    def init_tree(self):
        self.tree = LinesNode(-1, -1, "<root>")
        curr_node = self.tree
        for y, line in enumerate(self.original_lines):
            if len(line) == 1: continue
            line_level = self.get_line_level(line)
            new_node = LinesNode(line_level, y, line)
            if new_node.level > curr_node.level:
                curr_node.children.append(new_node)
                new_node.parent = curr_node
                curr_node = new_node
            elif new_node.level == curr_node.level:
                parent = curr_node.parent
                parent.children.append(new_node)
                new_node.parent = parent
                curr_node = new_node
            elif new_node.level < curr_node.level:
                while curr_node.level >= new_node.level:
                    curr_node = curr_node.parent
                curr_node.children.append(new_node)
                new_node.parent = curr_node
                curr_node = new_node

    def __init__(   self,
                    screen,
                    lines,
                    y_pos):
        if len(lines) == 0: raise Exception("no lines for LinesPopup().. WTF?")

        self.screen = screen
        self.original_lines = lines
        self.lines = lines
        self.y_pos = y_pos
        self.y_ret = y_pos
        self.ret_node = None
        self.selected = 0

        width_margin = 5
        height_margin = 3
        self.position = list([width_margin, height_margin])
        self.width = self.screen.width - (width_margin * 2)
        self.height = self.screen.height - (height_margin * 2)
        self.init_tree()

        found = self.tree
        def find_node(node):
            nonlocal found
            if node.line_num == self.y_pos:
                found = node
        traverse_lines_tree(self.tree, find_node)
        if not found.parent:
            self.nodes = [found]
            self.selected = 0
        else:
            self.nodes = found.parent.children
            self.selected = self.nodes.index(found)

    def on_key(self, key):
        if key == ENTER_KEY:
            self.y_ret = self.nodes[self.selected].line_num
            return True
        if key == ESC_KEY or key == ord('q'):
            return True
        if key == ord('h'):
            if not self.nodes[self.selected].parent:
                return False
            parent = self.nodes[self.selected].parent
            if parent.parent:
                siblings = parent.parent.children
                self.nodes = siblings
                self.selected = siblings.index(parent)
            else:
                self.nodes = [parent]
                self.selected = 0
            return False
        if key == ord('j'):
            if self.selected < len(self.nodes) - 1:
                self.selected += 1
            return False
        if key == ord('k'):
            if self.selected > 0:
                self.selected -= 1
            return False
        if key == ord('l'):
            if len(self.nodes[self.selected].children) > 0:
                self.nodes = self.nodes[self.selected].children
                self.selected = 0
            return False
        if key == CTRL_U_KEY:
            half = int(self.screen.height / 2)
            if self.selected < half: self.selected = 0
            else: self.selected -= half
            return False
        if key == CTRL_D_KEY:
            half = int(self.screen.height / 2)
            left = len(self.nodes) - self.selected - 1
            if left > half: self.selected += half
            else: self.selected += left
            return False
        if key == ord('g'):
            key = self.screen.get_key()
            if key == ord('g'):
                self.selected = 0
                return False
        if key == ord('G'):
            self.selected = len(self.nodes) - 1
            return False
        if key == ord('/'):
            pattern = ""
            success = False
            original_nodes = self.nodes
            original_selected = self.selected
            while True:
                key = self.screen.get_key()

                if key == ENTER_KEY:
                    if len(pattern) > 0: success = True
                    break
                if key == ESC_KEY: break
                if key == BACKSPACE_KEY:
                    if len(pattern) > 0: pattern = pattern[:-1]
                else:
                    try:
                        char = chr(key)
                        if char in printable:
                            pattern += char
                        else: break
                    except: continue
                filtered_nodes = [node for node in original_nodes if pattern in node.line_text]
                if len(filtered_nodes) > 0:
                    self.nodes = filtered_nodes
                    if self.selected >= len(self.nodes):
                        self.selected = len(self.nodes) - 1
                    self.draw()
            if not success:
                self.nodes = original_nodes
                self.selected = original_selected
            return False
        try:
            if chr(key).isnumeric():
                target_level = int(chr(key))
                nodes = []
                def nodes_at_level(node):
                    nonlocal nodes
                    nonlocal target_level
                    if node.level == target_level:
                        nodes.append(node)
                traverse_lines_tree(self.tree, nodes_at_level)
                if len(nodes) > 0:
                    self.nodes = nodes
                    if self.selected >= len(self.nodes):
                        self.selected = len(self.nodes) - 1
                    self.draw()

                return False
        except Exception as e: elog(f"Exception: {e}")
        return False

    def pop(self):
        try:
            while True:
                self.draw()

                key = self.screen.get_key()
                to_exit = self.on_key(key)
                if to_exit: break
        except Exception as e: elog(f"Exception: {e}")
        return self.y_ret

    def draw(self):
        try:
            style = {}
            style['background'] = g_settings['theme']['colors']['menu.background']
            style['foreground'] = g_settings['theme']['colors']['menu.foreground']
            selected_style = {}
            selected_style['background'] = g_settings['theme']['colors']['terminal.ansiMagenta']
            selected_style['foreground'] = g_settings['theme']['colors']['menu.foreground']

            for y in range(self.height):
                self.__draw(0, y, " "*self.width, style)

            if self.selected < self.height:
                for y, node in enumerate(self.nodes):
                    line = node.line_text
                    if len(line) < self.width:
                        option = f"{line}{' '*(self.width - len(line))}"
                    line = line[:self.width]
                    if y == self.selected:
                        self.__draw(0, y, f"{line}", selected_style)
                    else:
                        self.__draw(0, y, f"{line}", style)
            else:
                index = self.selected
                for y in reversed(range(self.height)):
                    line = self.nodes[index].line_text
                    if index == self.selected:
                        self.__draw(0, y, f"{line}", selected_style)
                    else:
                        self.__draw(0, y, f"{line}", style)
                    index -= 1
        except Exception as e: elog(f"Exception: {e}")
        self.screen.flush()

    def __draw(self, x, y, string, style):
        try:
            if x >= self.width: return
            if y >= self.height: return

            if x + len(string) - 1 >= self.width:
                space_for = self.width  - x
                string = string[:space_for]

            self.screen.write(  self.position[1] + y,
                                self.position[0] + x,
                                string,
                                style,
                                to_flush=False)
        except Exception as e: elog(f"Exception: {e}")
