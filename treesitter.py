#!/usr/bin/python3
from tree_sitter import Language, Parser
from settings import EDITOR_HOME_PATH
from log import elog

from os import path


# Language.build_library(
    # # Store the library in the `build` directory
    # 'grammars/tree-sitter-lib/my-languages.so',

    # # Include one or more languages
    # [
        # 'vendor/tree-sitter-python',
        # 'vendor/tree-sitter-bash',
        # 'vendor/tree-sitter-c',
        # 'vendor/tree-sitter-cpp',
        # 'vendor/tree-sitter-css',
        # 'vendor/tree-sitter-go',
        # 'vendor/tree-sitter-html',
        # 'vendor/tree-sitter-java',
        # 'vendor/tree-sitter-javascript',
        # 'vendor/tree-sitter-markdown',
        # 'vendor/tree-sitter-php',
        # 'vendor/tree-sitter-ruby',
        # 'vendor/tree-sitter-rust',
        # 'vendor/tree-sitter-make',
        # 'vendor/tree-sitter-c-sharp',
        # 'vendor/tree-sitter-elisp',
        # 'vendor/tree-sitter-lua',
        # 'vendor/tree-sitter-yaml',
        # 'vendor/tree-sitter-r',
        # 'vendor/tree-sitter-json',
    # ]
# )

PYTHON_LANGUAGE = Language(     path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'python')
C_LANGUAGE = Language(          path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'c')
BASH_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'bash')
CPP_LANGUAGE = Language(        path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'cpp')
CSS_LANGUAGE = Language(        path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'css')
GO_LANGUAGE = Language(         path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'go')
HTML_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'html')
JAVA_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'java')
JAVASCRIPT_LANGUAGE = Language( path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'javascript')
MARKDOWN_LANGUAGE = Language(   path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'markdown')
PHP_LANGUAGE = Language(        path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'php')
RUBY_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'ruby')
RUST_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'rust')
MAKE_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'make')
CSHARP_LANGUAGE = Language(     path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'c_sharp')
ELISP_LANGUAGE = Language(      path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'elisp')
LUA_LANGUAGE = Language(        path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'lua')
YAML_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'yaml')
R_LANGUAGE = Language(          path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'r')
JSON_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'json')

def walk(node, cb, level=0, nth_child=0):
    if cb(node, level, nth_child): return True
    curr_nth_child = 0
    for child in node.children:
        if walk(child, cb, level + 1, curr_nth_child): 
            return True
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

class TreeSitter():
    def __init__(self, file_bytes, language):
        self._initialize_language(language)

        self.tree = self.parser.parse(file_bytes)
        self.captures = None

    def _initialize_language(self, language):
        self.parser = Parser()
        query_path = path.join(EDITOR_HOME_PATH, "grammars/{}/highlights.scm")

        try:
            if language == 'python':
                with open(query_path.format("python"),"r") as f: query = f.read()
                self.query = PYTHON_LANGUAGE.query(query)
                self.parser.set_language(PYTHON_LANGUAGE)
            elif language == 'c':
                with open(query_path.format("c"),"r") as f: query = f.read()
                self.query = C_LANGUAGE.query(query)
                self.parser.set_language(C_LANGUAGE)
            elif language == 'java':
                with open(query_path.format("java"),"r") as f: query = f.read()
                self.query = JAVA_LANGUAGE.query(query)
                self.parser.set_language(JAVA_LANGUAGE)
            elif language == 'javascript':
                with open(query_path.format("javascript"),"r") as f: query = f.read()
                self.query = JAVASCRIPT_LANGUAGE.query(query)
                self.parser.set_language(JAVASCRIPT_LANGUAGE)
                elog("here..")
            else:
                raise Exception("treesitter not support that language.. :(")
        except Exception as e: elog(f"Exception: {e}")

    def resync(self, file_bytes):
        self.tree = self.parser.parse(file_bytes)
        self.captures = None

    def edit(self, edit, new_file_bytes):
        self.tree.edit(
                start_byte=edit['start_byte'],
                old_end_byte=edit['old_end_byte'],
                new_end_byte=edit['new_end_byte'],
                start_point=edit['start_point'],
                old_end_point=edit['old_end_point'],
                new_end_point=edit['new_end_point']
                )
        new_tree = self.parser.parse(new_file_bytes, self.tree)

        # for changed_range in self.tree.get_changed_ranges(new_tree):
            # print('Changed range:')
            # print(f'  Start point {changed_range.start_point}')
            # print(f'  Start byte {changed_range.start_byte}')
            # print(f'  End point {changed_range.end_point}')
            # print(f'  End byte {changed_range.end_byte}')

        self.captures = None # reset cache.
        self.tree = new_tree

    def get_captures(self, node=None, start_point=None, end_point=None):
        if not node: target_node = self.tree.root_node
        else: target_node = node

        return list(self.query.captures(target_node,
                                        start_point=start_point,
                                        end_point=end_point))

if __name__ == '__main__':
    # with open("editor", "rb") as f: file_bytes = f.read()

    # ts = TreeSitter(file_bytes)
    # captures = ts.get_captures()
    # for c in captures:
        # print(c)

    print(PYTHON_LANGUAGE)
    print(BASH_LANGUAGE)
    print(C_LANGUAGE)
    print(CPP_LANGUAGE)
    print(CSS_LANGUAGE)
    print(GO_LANGUAGE)
    print(HTML_LANGUAGE)
    print(JAVA_LANGUAGE)
    print(JAVASCRIPT_LANGUAGE)
    print(MARKDOWN_LANGUAGE)
    print(PHP_LANGUAGE)
    print(RUBY_LANGUAGE)
    print(RUST_LANGUAGE)
    print(MAKE_LANGUAGE)
    print(CSHARP_LANGUAGE)
    print(ELISP_LANGUAGE)
    print(LUA_LANGUAGE)
    print(YAML_LANGUAGE)
    print(R_LANGUAGE)
    print(JSON_LANGUAGE)
