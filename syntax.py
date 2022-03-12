from intervaltree import Interval, IntervalTree
from tree_sitter import Language, Parser
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
    if 'bg' in style:
        sys.stdout.write(BACKGROUND_TRUE_COLOR.format(convert(style['bg'])))
    if 'fg' in style:
        sys.stdout.write(FOREGROUND_TRUE_COLOR.format(convert(style['fg'])))

def walk(node, cb, level=0, nth_child=0):
    cb(node, level, nth_child)
    curr_nth_child = 0
    for child in node.children:
        walk(child, cb, level + 1, curr_nth_child)
        curr_nth_child += 1
    
def get_scope_style(token_colors, scope):
    for token in token_colors:
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

def map_node_to_scope(node, grammar, nth_child=0):
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

                ret = map_node_to_scope(parent, curr)
                if ret: return ret # we need to fallback 
        elif isinstance(grammar[nth_type], dict):
            parent = node.parent
            if 'match' in grammar[nth_type]: parent = node

            ret = map_node_to_scope(parent, grammar[nth_type])
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

            return map_node_to_scope(parent, curr)
    elif isinstance(grammar[_type], dict):
        parent = node.parent
        if 'match' in grammar[_type]: parent = node

        return map_node_to_scope(parent, grammar[_type])
    return None

def get_grammar(file_path):
    with open(file_path) as f:
        return json.loads(f.read())

def highlight_file(file_path):
    parser = Parser()
    parser.set_language(PY_LANGUAGE)

    theme_path = "themes/monokai-color-theme.json"

    with open(file_path, 'rb') as f: file_bytes = f.read()
    with open(file_path, 'r') as f: file_lines = f.readlines()

    with open(theme_path, 'r') as f: theme = json.loads(f.read())
    token_colors = theme['tokenColors']

    grammar = get_grammar("grammars/python.json")
    tree = parser.parse(file_bytes)
    
    # set default colors
    default_bg_color = theme['colors']['editor.background']
    default_fg_color = theme['colors']['editor.foreground']

    style_map = IntervalTree()

    def get_file_pos(x, y):
        for line in file_lines[:y]: x += len(line)
        return x

    def set_default_style():
        sys.stdout.write(FOREGROUND_TRUE_COLOR.format(convert(default_fg_color)))
        sys.stdout.write(BACKGROUND_TRUE_COLOR.format(convert(default_bg_color)))

    def get_style(x, y): 
        style = {}
        pos = get_file_pos(x, y)
        styles = sorted(style_map[pos])
        if len(styles) == 0: return None

        # settings = styles[::-1][0]
        settings = styles[0]
        settings = settings[2]

        if 'background' in settings:
            style['bg'] = settings['background']
        if 'foreground' in settings:
            style['fg'] = settings['foreground']
        if 'fontStyle' in settings:
            style['font_style'] = settings['fontStyle']
        return style
    
    def update_styles(x, y): return None

    def map_styles(node, level, nth_child):
        scope = map_node_to_scope(node, grammar, nth_child)
        if not scope: return

        style = get_scope_style(token_colors, scope)
        if not style: 
            # print(f"'{node.text.decode('utf-8')}' ({scope}) - not found!")
            return

        start_point = node.start_point
        start_pos = get_file_pos(   start_point[1], 
                                    start_point[0])

        end_point = node.end_point
        end_pos = get_file_pos( end_point[1], 
                                end_point[0])

        # print(f"{start_pos}:{end_pos}")
        style_map[start_pos:end_pos] = style

    walk(tree.root_node, map_styles)

    # draw
    y = 0
    for line in file_lines:
        x = 0
        for c in line:
            style = get_style(x, y)
            if style: set_style(style)
            else: set_default_style()

            sys.stdout.write(c)
            x += 1
        y += 1

def colors():
    # # 24bit color
    # sys.stdout.write(BACKGROUND_TRUE_COLOR.format(convert("#1B1A25")))
    # sys.stdout.write(FOREGROUND_TRUE_COLOR.format(convert("#625996")))
    # sys.stdout.write("test")

    # # 8bit color
    # for i in range(0, 16):
        # for j in range(0, 16):
            # code = str(i * 16 + j)
            # revert = str(j * 16 + i)

            # sys.stdout.write(FOREGROUND_256_COLOR.format(code))
            # sys.stdout.write(BACKGROUND_256_COLOR.format(revert))
            # sys.stdout.write("test")

    print("")

highlight_file("editor")

# colors()

# if style.b:
    # color_s += '\x1b[1m'
    # undo_s += '\x1b[22m'
# if style.i:
    # color_s += '\x1b[3m'
    # undo_s += '\x1b[23m'
# if style.u:
    # color_s += '\x1b[4m'
    # undo_s += '\x1b[24m'


class Syntax():
    def __init__(self, file_path, file_lines):
        # TODO: take settings from config.
        theme_path = "themes/monokai-color-theme.json"
        grammar_path = "grammars/python.json"

        with open(grammar_path, 'r') as f: self.grammar = json.loads(f.read())

        self.load_theme(theme_path)

        language = "python" # TODO auto detection

        self.initialize_tree_sitter(language)

        self.file_lines = file_lines

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

    def map_node_to_scope(self, node, nth_child=0):
        _type = node.type

        # match:
        if 'match' in self.grammar:
            pattern = self.grammar['match']

            if re.match(pattern, node.text.decode('utf-8')): 
                return self.grammar['scope']
            return None
        
        # choose most specific type
        nth_type = f"{_type}:nth-child({nth_child})"
        if nth_type in self.grammar: 
            if isinstance(self.grammar[nth_type], str): 
                return self.grammar[nth_type]
            elif isinstance(self.grammar[nth_type], list): 
                for curr in self.grammar[nth_type]:
                    # in the list case, its either dict or str.
                    if not isinstance(curr, dict): return curr

                    parent = node.parent
                    if 'match' in curr: parent = node

                    ret = self.map_node_to_scope(parent, curr)
                    if ret: return ret # we need to fallback 
            elif isinstance(self.grammar[nth_type], dict):
                parent = node.parent
                if 'match' in self.grammar[nth_type]: parent = node

                ret = self.map_node_to_scope(parent, self.grammar[nth_type])
                if ret: return ret

        if _type not in self.grammar: return None
        
        # str
        if isinstance(self.grammar[_type], str): 
            return self.grammar[_type]
        elif isinstance(self.grammar[_type], list): 
            for curr in self.grammar[_type]:
                if not isinstance(curr, dict): return curr

                parent = node.parent
                if 'match' in curr: parent = node

                return self.map_node_to_scope(parent, curr)
        elif isinstance(self.grammar[_type], dict):
            parent = node.parent
            if 'match' in self.grammar[_type]: parent = node

            return self.map_node_to_scope(parent, self.grammar[_type])
        return None

    def map_styles(self, node, level, nth_child):
        scope = self.map_node_to_scope(node, nth_child)
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

    def initialize_tree_sitter(self, language):
        # TODO: detect language.
        self.parser = Parser()

        if language == "python":
            self.parser.set_language(PY_LANGUAGE)
        elif language == "c": pass
        elif language == "markdown": pass
        elif language == "cpp": pass
        elif language == "rust": pass
        elif language == "asm": pass
        elif language == "vimscript": pass
        elif language == "java": pass
        elif language == "javascript": pass
        else: pass

        with open(file_path, 'rb') as f: file_bytes = f.read()
        self.tree = self.parser.parse(file_bytes)

    def get_file_pos(self, x, y):
        for line in self.file_lines[:y]: x += len(line)
        return x

    def initialize_style_map(self):
        self.style_map = IntervalTree()

        walk(self.tree.root_node, self.map_styles)

    def load_theme(self, theme_path):
        with open(theme_path, 'r') as f: self.theme = json.loads(f.read())

        # setting default style
        self.default_bg_color = self.theme['colors']['editor.background']
        self.default_fg_color = self.theme['colors']['editor.foreground']

        self.default_style = {}
        self.default_style['bg'] = self.default_bg_color
        self.default_style['fg'] = self.default_fg_color

        self.token_colors = self.theme['tokenColors']
    
    def get_style(self, position):
        style = {}
        pos = self.get_file_pos(x, y)
        styles = sorted(self.style_map[pos])
        if len(styles) == 0: 
            return self.default_style

        settings = styles[0]
        settings = settings[2]

        if 'background' in settings:
            style['bg'] = settings['background']
        if 'foreground' in settings:
            style['fg'] = settings['foreground']
        if 'fontStyle' in settings:
            style['font_style'] = settings['fontStyle']
        return style

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

# if __name__ == '__main__':
    # # sys.setrecursionlimit(10**6)

    # file_path = "editor"

    # with open(file_path, 'r') as f: file_lines = f.readlines()

    # syntax = Syntax(file_path, file_lines)

    # # syntax.draw()
