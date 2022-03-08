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

def get_settings(token_colors, scope):
    for token in token_colors:
        if "settings" not in token: continue
        if "scope" not in token: continue
        if token['scope'] != scope: continue

        # print(f"{token['settings']}")
        return token['settings']

def highlight_file(file_path):
    parser = Parser()
    parser.set_language(PY_LANGUAGE)

    theme_path = "themes/monokai-color-theme.json"

    with open(file_path, 'rb') as f: file_bytes = f.read()
    with open(theme_path, 'r') as f: theme = json.loads(f.read())

    # print(json.dumps(theme, indent=4))

    token_colors = theme['tokenColors']

    
    tree = parser.parse(file_bytes)

    def callback(node, level):
        # scope = node.type
        # settings = get_settings(token_colors, scope)
        # if not settings: return 

        # print(f"{scope}: {settings}")

        print("  "*level + f"{node.type}")

    walk_recursive(tree.root_node, callback)

highlight_file("editor")
