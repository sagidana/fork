#!/usr/bin/python3

from tree_sitter import Language, Parser

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

def highlight_file(file_path):
    parser = Parser()
    parser.set_language(PY_LANGUAGE)

    with open(file_path, 'rb') as f: file_bytes = f.read()
    
    tree = parser.parse(file_bytes)

    def callback(node, level):
        print("  "*level + f"{node.type}")

    walk_recursive(tree.root_node, callback)

highlight_file("editor")
