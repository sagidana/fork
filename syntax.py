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

def walk(node, cb, level=0, nth_child=0):
    cb(node, level, nth_child)
    curr_nth_child = 0
    for child in node.children:
        walk(child, cb, level + 1, curr_nth_child)
        curr_nth_child += 1
    
def traverse_tree(tree):
    cursor = tree.walk()
    reached_root = False

    while reached_root == False:
        yield cursor

        if cursor.goto_first_child(): continue

        if cursor.goto_next_sibling(): continue

        retracing = True

        while retracing:
            if not cursor.goto_parent(): 
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                retracing = False

def make_move(cursor, move, fn):
    if (move == "down"):
        fn(cursor)
        if (cursor.goto_first_child()):
            make_move(cursor, "down", fn)
        elif (cursor.goto_next_sibling()):
            make_move(cursor, "right", fn)
        elif (cursor.goto_parent()):
            make_move(cursor, "up", fn)
    elif (move == "right"):
        fn(cursor)
        if (cursor.goto_first_child()):
            make_move(cursor, "down", fn)
        elif (cursor.goto_next_sibling()):
            make_move(cursor, "right", fn)
        elif (cursor.goto_parent()):
            make_move(cursor, "up", fn)
    elif move == "up":
        if (cursor.goto_next_sibling()):
            make_move(cursor, "right", fn)
        elif (cursor.goto_parent()):
            make_move(cursor, "up", fn)

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
                    if curr == s:
                        return token['settings']

            # if scope in scopes: return token['settings']

            # continue

            # if scope != token['scope']: continue
            # return token['settings']

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

    def set_style(style): 
        if 'bg' in style:
            sys.stdout.write(BACKGROUND_TRUE_COLOR.format(convert(style['bg'])))
        if 'fg' in style:
            sys.stdout.write(FOREGROUND_TRUE_COLOR.format(convert(style['fg'])))
            
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
