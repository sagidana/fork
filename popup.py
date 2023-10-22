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
        window = self.editor.get_curr_window()

        x = window.buffer_cursor[0]
        y = window.buffer_cursor[1]
        status = f"{buffer.describe()} {y}:{x}"
        pending_tasks = self.editor.tasks
        self.details = []
        self.details.append(status)
        if len(pending_tasks) > 0:
            self.details.append("tasks")
            for task in pending_tasks:
                self.details.append(f"{g_settings['tab_representation']}- {task.id}")
        buffers = self.editor.buffers
        if len(buffers) > 0:
            self.details.append("buffers")
            for b in buffers:
                self.details.append(f"{g_settings['tab_representation']}- {b.describe()}")

        margin = 5
        self.position = list([  window.position[0] + margin,
                                window.position[1] + margin])
        self.width = window.width - (margin * 2)
        self.height = window.height - (margin * 2)
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

class TreeSitterPopup():
    def __init__(   self,
                    screen,
                    treesitter,
                    position):
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
            self.nodes = self.filter_nodes([closest_node])
            self.selected = 0
            self.level = closest_level
        else:
            while True:
                prev = closest_node
                closest_node = closest_node.parent
                if not closest_node: break
                closest_level -= 1
                self.nodes = self.filter_nodes(closest_node.children)
                if len(self.nodes) > 0:
                    self.selected = self.nodes.index(prev)
                    self.level = closest_level + 1
                    break

        if len(self.nodes) == 0: raise Exception('not should happend')

        # full screen TODO:
        margin = 5
        self.position = list([margin, margin])
        self.width = self.screen.width - (margin * 2)
        self.height = self.screen.height - (margin * 2)

    def filter_nodes(self, nodes):
        filtered_nodes = []
        for node in nodes:
            # if node.type not in [
                    # "translation_unit",
                    # "function_definition",
                    # "class_definition",
                    # "method_definition",
                    # "field_definition",
                    # ]:
                # continue
            filtered_nodes.append(node)
        return filtered_nodes

    def on_key(self, key):
        if key == ENTER_KEY:
            self.ret_node = self.nodes[self.selected]
            return True
        if key == ord('h'):
            if not self.nodes[self.selected].parent:
                return False
            parent = self.nodes[self.selected].parent
            if parent.parent:
                siblings = parent.parent.children
                self.nodes = self.filter_nodes(siblings)
                self.selected = self.nodes.index(parent)
            else:
                self.nodes = [parent]
                self.selected = 0
            self.level -= 1
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
            if self.nodes[self.selected].children:
                new_nodes = self.filter_nodes(self.nodes[self.selected].children)
                if len(new_nodes) == 0: return False
                self.nodes = new_nodes
                self.selected = 0
                self.level += 1
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
        if key == ord('/') or key == ord('?'):
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
                filtered_nodes = [node for node in original_nodes if pattern in self.node_to_string(node)]
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
                    if level == target_level: nodes.append(node)
                    return
                traverse_tree(self.treesitter.tree, nodes_at_level)
                if len(nodes) > 0:
                    self.level = target_level
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

    def node_to_string(self, node):
        lines = node.text.decode('utf8').splitlines()
        if len(lines) > 0:
            text = node.text.decode('utf8').splitlines()[0]
        else:
            text = ""
        ret = f"[{self.level}]{node.type}: {text}"

        return ret

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
                    option = self.node_to_string(node)
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
                    option = self.node_to_string(self.nodes[index])
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
