#!/usr/bin/python3

from tree_sitter import Language, Parser
import json
import re

# Language.build_library(
        # # Store the library in the `build` directory
        # 'build/my-languages.so',

        # # Include one or more languages
        # [
            # 'vendor/tree-sitter-python'
        # ]
    # )

PY_LANGUAGE = Language('build/my-languages.so', 'python')


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
                if s == scope:
                    return token['settings']
            # if scope in scopes: return token['settings']

            # continue

            # if scope != token['scope']: continue
            # return token['settings']
# 
def map_node_to_scope(node, grammar, nth_child=0):
    if 'match' in grammar:
        pattern = grammar['match']

        if re.match(pattern, node.text.decode('utf-8')): 
            return grammar['scope']
        return None
    
    _type = node.type
    if _type not in grammar: 
        _type = f"nth-child({nth_child})"
        if _type not in grammar: return None

    if isinstance(grammar[_type], str): return grammar[_type]

    if isinstance(grammar[_type], list): 
        for curr in grammar[_type]:
            if not isinstance(curr, dict): return curr

            parent = node.parent
            if 'match' in curr: parent = node

            return map_node_to_scope(parent, curr)

    if isinstance(grammar[_type], dict):
        parent = node.parent
        if 'match' in grammar[_type]: parent = node

        # print(f"{parent.type} > {node.type}")
        return map_node_to_scope(parent, grammar[_type])

def get_grammar(file_path):
    with open(file_path) as f:
        return json.loads(f.read())

def highlight_file(file_path):
    parser = Parser()
    parser.set_language(PY_LANGUAGE)

    theme_path = "themes/monokai-color-theme.json"

    with open(file_path, 'rb') as f: file_bytes = f.read()

    with open(theme_path, 'r') as f: theme = json.loads(f.read())
    token_colors = theme['tokenColors']

    grammar = get_grammar("grammars/python.json")
    # print(json.dumps(grammar, indent=4))

    tree = parser.parse(file_bytes)
    # cursor = tree.walk()
    # print(dir(tree.root_node))
    # return

    def callback(node, level, nth_child):
        # node = cursor.node
        scope = map_node_to_scope(node, grammar, nth_child)
        if not scope: return


        style = get_scope_style(token_colors, scope)
        if not style: 
            print(f"{scope}")
            return 

        # print(f"{scope}: {style}")

    walk(tree.root_node, callback)
    # make_move(cursor, "down", callback)
    # for cursor in traverse_tree(tree):
        # print(cursor.node.child_count)
        # break
        # callback(cursor)

highlight_file("editor")
