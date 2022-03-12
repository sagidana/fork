from intervaltree import Interval, IntervalTree
from tree_sitter import Language, Parser
from colors import rgb2short, short2rgb
from log import elog
import time
import json
import sys
import re

# Language.build_library(
        # # Store the library in the `build` directory
        # 'grammars/tree-sitter-lib/my-languages.so',

        # # Include one or more languages
        # [
            # 'vendor/tree-sitter-python'
        # ]
    # )

PY_LANGUAGE = Language('grammars/tree-sitter-lib/my-languages.so', 'python')

BACKGROUND_TRUE_COLOR = "\x1b[48;2;{}m"
FOREGROUND_TRUE_COLOR = "\x1b[38;2;{}m"
BACKGROUND_256_COLOR = "\x1b[48;5;{}m"
FOREGROUND_256_COLOR = "\x1b[38;5;{}m"

def convert(a):
    r, g, b = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    return f"{r};{g};{b}"

def set_style(style): 
    # if 'bg' in style:
        # sys.stdout.write(BACKGROUND_TRUE_COLOR.format(convert(style['bg'])))
    # if 'fg' in style:
        # sys.stdout.write(FOREGROUND_TRUE_COLOR.format(convert(style['fg'])))

    if 'bg' in style:
        # color = rgb2short(style['bg'])[0]
        color = style['bg']
        # print(f"bg: {rgb2short(style['bg'])}")
        sys.stdout.write(BACKGROUND_256_COLOR.format(color))
    if 'fg' in style:
        # color = rgb2short(style['fg'])[0]
        color = style['fg']
        # print(f"fg: {rgb2short(style['fg'])}")
        sys.stdout.write(FOREGROUND_256_COLOR.format(color))

def walk(node, cb, level=0, nth_child=0):
    if cb(node, level, nth_child): return False
    curr_nth_child = 0
    for child in node.children:
        if walk(child, cb, level + 1, curr_nth_child): 
            return False
        curr_nth_child += 1
    return False
    
def traverse_tree(tree, cb):
    cursor = tree.walk()
    reached_root = False

    level = 0
    nth_child = {}

    while reached_root == False:
        if level not in nth_child: nth_child[level] = 0

        # yield cursor
        cb(cursor.node, level, nth_child[level])

        if cursor.goto_first_child(): 
            level += 1
            continue

        if cursor.goto_next_sibling(): 
            nth_child[level] += 1
            continue

        retracing = True

        while retracing:
            if not cursor.goto_parent(): 
                retracing = False
                reached_root = True
            level -= 1

            if cursor.goto_next_sibling():
                nth_child[level] += 1
                retracing = False

# # if style.b:
    # # color_s += '\x1b[1m'
    # # undo_s += '\x1b[22m'
# # if style.i:
    # # color_s += '\x1b[3m'
    # # undo_s += '\x1b[23m'
# # if style.u:
    # # color_s += '\x1b[4m'
    # # undo_s += '\x1b[24m'

class Syntax():
    def __init__(self, file_path, file_lines):
        self.file_path = file_path
        self.file_lines = file_lines

        # self.colors_system = "256_colors"
        self.colors_system = "true_colors"

        # TODO: take settings from config.
        # theme_path = "themes/monokai-color-theme.json"
        theme_path = "themes/darcula.json"
        grammar_path = "grammars/python.json"

        with open(grammar_path, 'r') as f: self.grammar = json.loads(f.read())

        self.load_theme(theme_path)

        self.language = "python" # TODO auto detection

        self.initialize_tree_sitter()

        self.initialize_style_map()

    def get_scope_style(self, scope):
        for token in self.token_colors:
            if "settings" not in token: continue
            if "scope" not in token: continue

            if isinstance(token['scope'], list):
                for curr in token['scope']:
                    if curr == scope:
                        # print(f"{scope}: {token['settings']}")
                        return token['settings']
                continue
            else:
                scopes = [x.strip() for x in token['scope'].split(',')]

                for s in scopes:
                    target_scopes = scope.split('.')
                    if s == scope: return token["settings"]

                    for i in range(len(target_scopes) - 1, 0, -1):
                        curr = '.'.join(target_scopes[:i])
                        if curr == s: return token['settings']

    def map_node_to_scope(self, node, grammar, nth_child=0):
        _type = node.type

        # match:
        if 'match' in grammar:
            pattern = grammar['match']

            if re.match(pattern, node.text.decode('utf-8')): 
                return grammar['scope']
            return None
        
        # choose most specific type
        nth_type = f"{_type}:nth-child({nth_child})"
        if nth_type in grammar: 
            if isinstance(grammar[nth_type], str): 
                return grammar[nth_type]
            elif isinstance(grammar[nth_type], list): 
                for curr in grammar[nth_type]:
                    # in the list case, its either dict or str.
                    if not isinstance(curr, dict): return curr

                    parent = node.parent
                    if 'match' in curr: parent = node

                    ret = self.map_node_to_scope(parent, curr)
                    if ret: return ret # we need to fallback 
            elif isinstance(grammar[nth_type], dict):
                parent = node.parent
                if 'match' in grammar[nth_type]: parent = node

                ret = self.map_node_to_scope(parent, grammar[nth_type])
                if ret: return ret

        if _type not in grammar: return None
        
        # str
        if isinstance(grammar[_type], str): 
            return grammar[_type]
        elif isinstance(grammar[_type], list): 
            for curr in grammar[_type]:
                if not isinstance(curr, dict): return curr

                parent = node.parent
                if 'match' in curr: parent = node

                return self.map_node_to_scope(parent, curr)
        elif isinstance(grammar[_type], dict):
            parent = node.parent
            if 'match' in grammar[_type]: parent = node

            return self.map_node_to_scope(parent, grammar[_type])
        return None

    def map_styles(self, node, level, nth_child):
        scope = self.map_node_to_scope(node, self.grammar, nth_child)
        # scope = map_node_to_scope(node, self.grammar, nth_child)
        if not scope: return

        style = self.get_scope_style(scope)
        if not style: return

        start_point = node.start_point
        start_pos = self.get_file_pos(  start_point[1], 
                                        start_point[0])

        end_point = node.end_point
        end_pos = self.get_file_pos(    end_point[1], 
                                        end_point[0])

        self.style_map[start_pos:end_pos] = style

    def initialize_tree_sitter(self):
        self.parser = Parser()

        if self.language == "python":
            self.parser.set_language(PY_LANGUAGE)
        elif self.language == "c": pass
        elif self.language == "markdown": pass
        elif self.language == "cpp": pass
        elif self.language == "rust": pass
        elif self.language == "asm": pass
        elif self.language == "vimscript": pass
        elif self.language == "java": pass
        elif self.language == "javascript": pass
        else: pass

        file_bytes = ''.join(self.file_lines).encode()
        self.tree = self.parser.parse(file_bytes)

    def get_file_pos(self, x, y):
        for line in self.file_lines[:y]: x += len(line)
        return x

    def initialize_style_map(self):
        elog("initialize_style_map()")
        self.style_map = IntervalTree()

        walk(self.tree.root_node, self.map_styles)
        # traverse_tree(self.tree, self.map_styles) # have some kind of bug..

    def refresh(self):
        # start = time.time()
        self.initialize_tree_sitter()
        # elog(f"initialize_tree_sitter() time: {time.time() - start}")
        # start = time.time()
        self.initialize_style_map()
        # elog(f"initialize_style_map() time: {time.time() - start}")

    def get_color(self, color):
        if self.colors_system == "true_colors":
            return color
        elif self.colors_system == "256_colors":
            return rgb2short(color)[0]
        else: raise Exception("Not implemented.")
        return None

    def load_theme(self, theme_path):
        with open(theme_path, 'r') as f: self.theme = json.loads(f.read())

        # setting default style
        self.default_bg_color = self.get_color(self.theme['colors']['editor.background'])
        self.default_fg_color = self.get_color(self.theme['colors']['editor.foreground'])

        self.default_style = {}
        self.default_style['bg'] = self.default_bg_color
        self.default_style['fg'] = self.default_fg_color

        self.token_colors = self.theme['tokenColors']

    def get_default_style(self):
        return self.default_style
    
    def _get_style(self, x, y):
        pos = self.get_file_pos(x, y)

        style = None
        def cb(node, level, nth_child):
            start_point = node.start_point
            start_pos = self.get_file_pos(  start_point[1], 
                                            start_point[0])

            end_point = node.end_point
            end_pos = self.get_file_pos(    end_point[1], 
                                            end_point[0])

            if pos > end_pos:
                return False # continue to search
            if pos <= start_pos:
                return False # continue to search

            scope = self.map_node_to_scope(node, self.grammar, nth_child)
            # scope = map_node_to_scope(node, self.grammar, nth_child)
            if not scope: return False

            style = self.get_scope_style(scope)
            if not style: return False

            return True # found - exit!

        elog("before walk()")
        walk(self.tree.root_node, cb)
        elog("after walk()")

        return style

    def get_style(self, x, y):
        style = {}

        pos = self.get_file_pos(x, y)
        styles = sorted(self.style_map[pos])
        if len(styles) == 0: 
            return self.default_style
        settings = styles[0]

        # res = self._get_style(x, y)
        # if not res: return self.default_style
        # settings = res

        settings = settings[2]

        if 'background' in settings:
            style['bg'] = self.get_color(settings['background'])
        else: 
            style['bg'] = self.default_bg_color

        if 'foreground' in settings:
            style['fg'] = self.get_color(settings['foreground'])
        else:
            style['fg'] = self.default_fg_color

        if 'fontStyle' in settings:
            style['font_style'] = settings['fontStyle']
        return style

    def on_change(self, change):
        # TODO incremental changes.
        self.initialize_tree_sitter()
        self.initialize_style_map()

    def draw(self):
        # draw
        y = 0
        for line in self.file_lines:
            x = 0
            for c in line:
                style = self.get_style(x, y)
                if style: set_style(style)

                sys.stdout.write(c)
                x += 1
            y += 1

if __name__ == '__main__':
    # sys.setrecursionlimit(10**6)

    file_path = "editor"

    with open(file_path, 'r') as f: file_lines = f.readlines()

    syntax = Syntax(file_path, file_lines)

    syntax.draw()
