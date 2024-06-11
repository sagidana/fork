#!/usr/bin/python3
from settings import EDITOR_HOME_PATH
from log import elog

from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_c
import tree_sitter_bash
import tree_sitter_cpp
import tree_sitter_css
import tree_sitter_go
import tree_sitter_html
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_php
import tree_sitter_ruby
import tree_sitter_rust
import tree_sitter_c_sharp
import tree_sitter_json
from os import path



PYTHON_LANGUAGE =       Language(tree_sitter_python.language())
C_LANGUAGE =            Language(tree_sitter_c.language())
BASH_LANGUAGE =         Language(tree_sitter_bash.language())
CPP_LANGUAGE =          Language(tree_sitter_cpp.language())
CSS_LANGUAGE =          Language(tree_sitter_css.language())
GO_LANGUAGE =           Language(tree_sitter_go.language())
HTML_LANGUAGE =         Language(tree_sitter_html.language())
JAVA_LANGUAGE =         Language(tree_sitter_java.language())
JAVASCRIPT_LANGUAGE =   Language(tree_sitter_javascript.language())
PHP_LANGUAGE =          Language(tree_sitter_php.language_php())
RUBY_LANGUAGE =         Language(tree_sitter_ruby.language())
RUST_LANGUAGE =         Language(tree_sitter_rust.language())
CSHARP_LANGUAGE =       Language(tree_sitter_c_sharp.language())
JSON_LANGUAGE =         Language(tree_sitter_json.language())
# SMALI_LANGUAGE = get_language('smali')
# MARKDOWN_LANGUAGE = get_language('markdown')

# PYTHON_LANGUAGE = Language(     path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'python')
# C_LANGUAGE = Language(          path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'c')
# BASH_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'bash')
# CPP_LANGUAGE = Language(        path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'cpp')
# CSS_LANGUAGE = Language(        path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'css')
# GO_LANGUAGE = Language(         path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'go')
# HTML_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'html')
# JAVA_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'java')
# JAVASCRIPT_LANGUAGE = Language( path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'javascript')
# PHP_LANGUAGE = Language(        path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'php')
# RUBY_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'ruby')
# RUST_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'rust')
# CSHARP_LANGUAGE = Language(     path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'c_sharp')
# JSON_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'json')
# SMALI_LANGUAGE = Language(      path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'smali')
# MARKDOWN_LANGUAGE = Language(   path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'markdown')

# MAKE_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'make')
# ELISP_LANGUAGE = Language(      path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'elisp')
# LUA_LANGUAGE = Language(        path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'lua')
# YAML_LANGUAGE = Language(       path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'yaml')
# R_LANGUAGE = Language(          path.join(EDITOR_HOME_PATH, 'grammars/tree-sitter-lib/my-languages.so'), 'r')

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
        self.language = language

        self.tree = self.parser.parse(file_bytes)
        self.captures = None

    def _initialize_language(self, language):
        self.parser = Parser()
        query_path = path.join(EDITOR_HOME_PATH, "grammars/{}/highlights.scm")

        try:
            if language == 'python':
                self._language = PYTHON_LANGUAGE
                with open(query_path.format("python"),"r") as f: query = f.read()
                self.query = PYTHON_LANGUAGE.query(query)
                self.parser.set_language(PYTHON_LANGUAGE)
            elif language == 'c':
                self._language = C_LANGUAGE
                with open(query_path.format("c"),"r") as f: query = f.read()
                self.query = C_LANGUAGE.query(query)
                self.parser.set_language(C_LANGUAGE)
            elif language == 'json':
                self._language = JSON_LANGUAGE
                with open(query_path.format("json"),"r") as f: query = f.read()
                self.query = JSON_LANGUAGE.query(query)
                self.parser.set_language(JSON_LANGUAGE)
            elif language == 'java':
                self._language = JAVA_LANGUAGE
                with open(query_path.format("java"),"r") as f: query = f.read()
                self.query = JAVA_LANGUAGE.query(query)
                self.parser.set_language(JAVA_LANGUAGE)
            elif language == 'javascript':
                self._language = JAVASCRIPT_LANGUAGE
                with open(query_path.format("javascript"),"r") as f: query = f.read()
                self.query = JAVASCRIPT_LANGUAGE.query(query)
                self.parser.set_language(JAVASCRIPT_LANGUAGE)
            elif language == 'smali':
                self._language = SMALI_LANGUAGE
                with open(query_path.format("smali"),"r") as f: query = f.read()
                self.query = SMALI_LANGUAGE.query(query)
                self.parser.set_language(SMALI_LANGUAGE)
            elif language == 'markdown':
                self._language = MARKDOWN_LANGUAGE
                with open(query_path.format("markdown"),"r") as f: query = f.read()
                self.query = MARKDOWN_LANGUAGE.query(query)
                self.parser.set_language(MARKDOWN_LANGUAGE)
            elif language == 'cpp':
                self._language = CPP_LANGUAGE
                with open(query_path.format("cpp"),"r") as f: query = f.read()
                self.query = CPP_LANGUAGE.query(query)
                self.parser.set_language(CPP_LANGUAGE)
            elif language == 'rust':
                self._language = RUST_LANGUAGE
                with open(query_path.format("rust"),"r") as f: query = f.read()
                self.query = RUST_LANGUAGE.query(query)
                self.parser.set_language(RUST_LANGUAGE)
            elif language == 'go':
                self._language = GO_LANGUAGE
                with open(query_path.format("go"),"r") as f: query = f.read()
                self.query = GO_LANGUAGE.query(query)
                self.parser.set_language(GO_LANGUAGE)
            elif language == 'bash':
                self._language = BASH_LANGUAGE
                with open(query_path.format("bash"),"r") as f: query = f.read()
                self.query = BASH_LANGUAGE.query(query)
                self.parser.set_language(BASH_LANGUAGE)
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

    def _get_relevant_nodes(self, node, query, x=None, y=None, most_relevant=False):
        if x is None or y is None:
            captures = query.captures(node)
        else:
            captures = query.captures(  node,
                                        start_point=[y-1 if y > 0 else y, 0],
                                        end_point=[y+1, 0])

        elog(f"captures: {captures}")
        if most_relevant: captures = reversed(captures)

        for node, name in captures:
            if x is None or y is None:
                return node

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            elog(f"{y, x}")
            elog(f"{(start_y, start_x, end_y, end_x)}")
            if start_y > y: continue
            if end_y < y: continue
            if start_y == y and start_x > x: continue
            if end_y == y and end_x < x: continue
            return node
        return None

    def get_inner_if(self, x, y):
        if self.language == 'python':
            query = self._language.query("(if_statement (block) @name)")
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the new line char
            return start_x, start_y, end_x, end_y

        if self.language == 'c':
            query = self._language.query("(if_statement (compound_statement) @name)")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            start_x += 1 # exclude the curly braces
            end_x -= 1 # exclude the curly braces

            return start_x, start_y, end_x-1, end_y
        return None

    def get_arround_if(self, x, y):
        if self.language == 'python':
            query = self._language.query("(if_statement) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the new line char
            return start_x, start_y, end_x, end_y

        if self.language == 'c':
            query = self._language.query("(if_statement) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            return start_x, start_y, end_x-1, end_y
        return None

    def get_inner_IF(self, x, y):
        if self.language == 'python':
            query = self._language.query("(if_statement) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            node_start_y = node.start_point[0]
            node_start_x = node.start_point[1]
            node_end_y = node.end_point[0]
            node_end_x = node.end_point[1]

            start_y = node_start_y
            start_x = node_start_x + len('if ')
            end_y = start_y
            end_x = start_x

            for ch in node.text.decode()[len('if '):]:
                if ch == ':': break
                if ch == '\n':
                    end_x = 0
                    end_y += 1
                else:
                    end_x += 1
            end_x -= 1 # remove the ':' from the range

            return start_x, start_y, end_x, end_y

        if self.language == 'c':
            query = self._language.query("(if_statement) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None
            query = self._language.query("(if_statement (parenthesized_expression) @name)")
            node = self._get_relevant_nodes(node, query)
            if not node: return None

            start_y = node.start_point[0]
            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the parenthesize
            start_x += 1 # exclude the parenthesize

            return start_x, start_y, end_x-1, end_y
        return None

    def get_inner_method(self, x, y):
        if self.language == 'python':
            query = self._language.query("(function_definition (block) @name)")
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the new line char
            return start_x, start_y, end_x, end_y

        if self.language == 'c':
            query = self._language.query("(function_definition (compound_statement) @name)")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            end_x -= 1 # why c parser returns the end exclusive?
            end_x -= 1 # exclude the parenthesize
            start_x += 1 # exclude the parenthesize

            return start_x, start_y, end_x, end_y
        return None

    def get_arround_method(self, x, y):
        if self.language == 'python':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the new line char
            return start_x, start_y, end_x, end_y

        if self.language == 'c':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            return start_x, start_y, end_x, end_y
        return None

    def get_inner_METHOD(self, x, y):
        if self.language == 'python':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None
            query = self._language.query("(function_definition (parameters) @name)")
            node = self._get_relevant_nodes(node, query)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # why python parser returns the end exclusive?
            start_x += 1 # exclude the parenthesize
            end_x -= 1 # exclude the parenthesize
            return start_x, start_y, end_x, end_y

        if self.language == 'c':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None
            query = self._language.query("(function_definition (function_declarator (parameter_list) @name))")
            node = self._get_relevant_nodes(node, query)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            end_x -= 1 # why c parser returns the end exclusive?
            end_x -= 1 # exclude the parenthesize
            start_x += 1 # exclude the parenthesize

            return start_x, start_y, end_x, end_y
        return None

    def get_arround_METHOD(self, x, y):
        if self.language == 'python':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None
            query = self._language.query("(function_definition (identifier) @name)")
            node = self._get_relevant_nodes(node, query)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # why python parser returns the end exclusive?
            return start_x, start_y, end_x, end_y

        if self.language == 'c':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None
            query = self._language.query("(function_definition (function_declarator (identifier) @name))")
            node = self._get_relevant_nodes(node, query)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            end_x -= 1 # why c parser returns the end exclusive?
            return start_x, start_y, end_x, end_y
        return None

if __name__ == '__main__':
    Language.build_library(
        # Store the library in the `build` directory
        'grammars/tree-sitter-lib/my-languages.so',

        # do into vendor/:
        # git clone https://github.com/tree-sitter/tree-sitter-python
        # git clone https://github.com/tree-sitter/tree-sitter-bash
        # git clone https://github.com/tree-sitter/tree-sitter-c
        # git clone https://github.com/tree-sitter/tree-sitter-cpp
        # git clone https://github.com/tree-sitter/tree-sitter-css
        # git clone https://github.com/tree-sitter/tree-sitter-go
        # git clone https://github.com/tree-sitter/tree-sitter-html
        # git clone https://github.com/tree-sitter/tree-sitter-java
        # git clone https://github.com/tree-sitter/tree-sitter-javascript
        # git clone https://github.com/tree-sitter/tree-sitter-php
        # git clone https://github.com/tree-sitter/tree-sitter-ruby
        # git clone https://github.com/tree-sitter/tree-sitter-rust
        # git clone https://github.com/tree-sitter/tree-sitter-c-sharp
        # git clone https://github.com/tree-sitter/tree-sitter-json
        # git clone https://github.com/amaanq/tree-sitter-smali.git
        # git clone https://github.com/MDeiml/tree-sitter-markdown.git

        # git clone https://github.com/tree-sitter/tree-sitter-markdown
        # git clone https://github.com/tree-sitter/tree-sitter-make
        # git clone https://github.com/tree-sitter/tree-sitter-elisp
        # git clone https://github.com/tree-sitter/tree-sitter-lua
        # git clone https://github.com/tree-sitter/tree-sitter-yaml
        # git clone https://github.com/tree-sitter/tree-sitter-r

        # Include one or more languages

        [
            'vendor/tree-sitter-python',
            'vendor/tree-sitter-bash',
            'vendor/tree-sitter-c',
            'vendor/tree-sitter-cpp',
            'vendor/tree-sitter-css',
            'vendor/tree-sitter-go',
            'vendor/tree-sitter-html',
            'vendor/tree-sitter-java',
            'vendor/tree-sitter-javascript',
            'vendor/tree-sitter-php',
            'vendor/tree-sitter-ruby',
            'vendor/tree-sitter-rust',
            'vendor/tree-sitter-c-sharp',
            'vendor/tree-sitter-json',
            'vendor/tree-sitter-smali',
            'vendor/tree-sitter-markdown',
            # 'vendor/tree-sitter-markdown',
            # 'vendor/tree-sitter-make',
            # 'vendor/tree-sitter-elisp',
            # 'vendor/tree-sitter-lua',
            # 'vendor/tree-sitter-yaml',
            # 'vendor/tree-sitter-r',
        ]
    )

    # with open("editor", "rb") as f: file_bytes = f.read()

    # ts = TreeSitter(file_bytes)
    # captures = ts.get_captures()
    # for c in captures:
        # print(c)

    # print(PYTHON_LANGUAGE)
    # print(BASH_LANGUAGE)
    # print(C_LANGUAGE)
    # print(CPP_LANGUAGE)
    # print(CSS_LANGUAGE)
    # print(GO_LANGUAGE)
    # print(HTML_LANGUAGE)
    # print(JAVA_LANGUAGE)
    # print(JAVASCRIPT_LANGUAGE)
    # print(MARKDOWN_LANGUAGE)
    # print(PHP_LANGUAGE)
    # print(RUBY_LANGUAGE)
    # print(RUST_LANGUAGE)
    # print(MAKE_LANGUAGE)
    # print(CSHARP_LANGUAGE)
    # print(ELISP_LANGUAGE)
    # print(LUA_LANGUAGE)
    # print(YAML_LANGUAGE)
    # print(R_LANGUAGE)
    # print(JSON_LANGUAGE)
