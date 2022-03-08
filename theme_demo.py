#!/usr/bin/python3

from tree_sitter import Language, Parser
import json

# Language.build_library(
        # # Store the library in the `build` directory
        # 'build/my-languages.so',

        # # Include one or more languages
        # [
            # 'vendor/tree-sitter-python'
        # ]
    # )

PY_LANGUAGE = Language('build/my-languages.so', 'python')


def walk_recursive(node, cb, level=0):
    cb(node, level)
    for child in node.children:
        walk_recursive(child, cb, level + 1)

def get_scope_style(token_colors, scope):
    for token in token_colors:
        if "settings" not in token: continue
        if "scope" not in token: continue
        if token['scope'] != scope: continue

        # print(f"{token['settings']}")
        return token['settings']

def map_node_to_scope(node, grammar):
    # print(f"{node.type}")
    scopes = grammar['scopes']
    if node.type in scopes: return scopes[node.type]
    if f"\"{node.type}\"" in scopes: return scopes[f"\"{node.type}\""]

    return None

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

    def callback(node, level):
        # print("  "*level + f"{node.type}")
        scope = map_node_to_scope(node, grammar)
        if not scope: return

        style = get_scope_style(token_colors, scope)
        if not style: return 

        print(f"{scope}: {style}")

    walk_recursive(tree.root_node, callback)

highlight_file("editor")
