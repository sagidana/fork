#!/usr/bin/python3
from settings import INSTALLATION_PATH
from common import Scope
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
import traceback


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


def static_init(cls):
    if getattr(cls, "static_init", None):
        cls.static_init()
        return cls

@static_init
class TreeSitter():
    @classmethod
    def static_init(cls):
        def load_language(path, name):
            from ctypes import c_void_p, cdll
            from typing import Callable, List, Optional, Union
            try:
                lib = cdll.LoadLibrary(path)
                language_function: Callable[[],int] = getattr(lib, f"tree_sitter_{name}")
                language_function.restype = c_void_p
                return Language(language_function())
            except Exception as e:
                elog(f"Exception: {e}")
            return None

        cls.PYTHON_LANGUAGE =       Language(tree_sitter_python.language())
        cls.C_LANGUAGE =            Language(tree_sitter_c.language())
        cls.BASH_LANGUAGE =         Language(tree_sitter_bash.language())
        cls.CPP_LANGUAGE =          Language(tree_sitter_cpp.language())
        cls.CSS_LANGUAGE =          Language(tree_sitter_css.language())
        cls.GO_LANGUAGE =           Language(tree_sitter_go.language())
        cls.HTML_LANGUAGE =         Language(tree_sitter_html.language())
        cls.JAVA_LANGUAGE =         Language(tree_sitter_java.language())
        cls.JAVASCRIPT_LANGUAGE =   Language(tree_sitter_javascript.language())
        cls.PHP_LANGUAGE =          Language(tree_sitter_php.language_php())
        cls.RUBY_LANGUAGE =         Language(tree_sitter_ruby.language())
        cls.RUST_LANGUAGE =         Language(tree_sitter_rust.language())
        cls.CSHARP_LANGUAGE =       Language(tree_sitter_c_sharp.language())
        cls.JSON_LANGUAGE =         Language(tree_sitter_json.language())
        lib_path = path.join(INSTALLATION_PATH,
                            "ts_parsers/tree-sitter-markdown/tree-sitter-markdown/libtree-sitter-markdown.so")
        cls.MARKDOWN_LANGUAGE =     load_language(lib_path, 'markdown')
        lib_path = path.join(INSTALLATION_PATH,
                            "./ts_parsers/tree-sitter-zig/libtree-sitter-zig.so")
        cls.ZIG_LANGUAGE =     load_language(lib_path, 'zig')

    def __init__(self, file_bytes, language):
        self._initialize_language(language)
        self.language = language

        self.tree = self.parser.parse(file_bytes)
        self.captures = None

    def _initialize_language(self, language):
        self.parser = Parser()
        query_path = path.join(INSTALLATION_PATH, "grammars/{}/highlights.scm")

        try:
            if language == 'python':
                self._language = TreeSitter.PYTHON_LANGUAGE
                with open(query_path.format("python"),"r") as f: query = f.read()
                self.query = TreeSitter.PYTHON_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.PYTHON_LANGUAGE)
            elif language == 'c':
                self._language = TreeSitter.C_LANGUAGE
                with open(query_path.format("c"),"r") as f: query = f.read()
                self.query = TreeSitter.C_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.C_LANGUAGE)
            elif language == 'json':
                self._language = TreeSitter.JSON_LANGUAGE
                with open(query_path.format("json"),"r") as f: query = f.read()
                self.query = TreeSitter.JSON_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.JSON_LANGUAGE)
            elif language == 'java':
                self._language = TreeSitter.JAVA_LANGUAGE
                with open(query_path.format("java"),"r") as f: query = f.read()
                self.query = TreeSitter.JAVA_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.JAVA_LANGUAGE)
            elif language == 'javascript':
                self._language = TreeSitter.JAVASCRIPT_LANGUAGE
                with open(query_path.format("javascript"),"r") as f: query = f.read()
                self.query = TreeSitter.JAVASCRIPT_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.JAVASCRIPT_LANGUAGE)
            elif language == 'smali':
                self._language = TreeSitter.SMALI_LANGUAGE
                with open(query_path.format("smali"),"r") as f: query = f.read()
                self.query = TreeSitter.SMALI_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.SMALI_LANGUAGE)
            elif language == 'markdown':
                self._language = TreeSitter.MARKDOWN_LANGUAGE
                with open(query_path.format("markdown"),"r") as f: query = f.read()
                self.query = TreeSitter.MARKDOWN_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.MARKDOWN_LANGUAGE)
            elif language == 'cpp':
                self._language = TreeSitter.CPP_LANGUAGE
                with open(query_path.format("cpp"),"r") as f: query = f.read()
                self.query = TreeSitter.CPP_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.CPP_LANGUAGE)
            elif language == 'rust':
                self._language = TreeSitter.RUST_LANGUAGE
                with open(query_path.format("rust"),"r") as f: query = f.read()
                self.query = TreeSitter.RUST_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.RUST_LANGUAGE)
            elif language == 'go':
                self._language = TreeSitter.GO_LANGUAGE
                with open(query_path.format("go"),"r") as f: query = f.read()
                self.query = TreeSitter.GO_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.GO_LANGUAGE)
            elif language == 'zig':
                self._language = TreeSitter.ZIG_LANGUAGE
                with open(query_path.format("zig"),"r") as f: query = f.read()
                self.query = TreeSitter.ZIG_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.ZIG_LANGUAGE)
            elif language == 'bash':
                self._language = TreeSitter.BASH_LANGUAGE
                with open(query_path.format("bash"),"r") as f: query = f.read()
                self.query = TreeSitter.BASH_LANGUAGE.query(query)
                self.parser.set_language(TreeSitter.BASH_LANGUAGE)
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
        self.captures = None # reset cache.
        self.tree = self.parser.parse(new_file_bytes, self.tree)

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

        if most_relevant: captures = reversed(captures)

        for node, name in captures:
            if x is None or y is None:
                return node

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            if start_y > y: continue
            if end_y < y: continue
            if start_y == y and start_x > x: continue
            if end_y == y and end_x < x: continue
            return node
        return None

    def get_inner_if(self, x, y):
        x += 1
        if self.language == 'python':
            query = self._language.query("""
            (if_statement) @name
            (elif_clause) @name
            """)
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None
            query = self._language.query("""
            (if_statement (block) @name)
            (elif_clause (block) @name)
            """)
            node = self._get_relevant_nodes(node, query)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the new line char
            return Scope(start_x, start_y, end_x, end_y)

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

            return Scope(start_x, start_y, end_x-1, end_y)
        return None

    def get_arround_if(self, x, y):
        x += 1
        if self.language == 'python':
            query = self._language.query("""
            (if_statement) @name
            (elif_clause) @name
            """)
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the new line char
            return Scope(start_x, start_y, end_x, end_y)

        if self.language == 'c':
            query = self._language.query("(if_statement) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            return Scope(start_x, start_y, end_x-1, end_y)
        return None

    def get_inner_IF(self, x, y):
        x += 1
        if self.language == 'python':
            query = self._language.query("""
            (if_statement) @name
            (elif_clause) @name
            """)
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            node_start_y = node.start_point[0]
            node_start_x = node.start_point[1]
            node_end_y = node.end_point[0]
            node_end_x = node.end_point[1]
            node_text = node.text.decode()

            start_y = node_start_y
            to_skip = 0
            if node_text.startswith('if'):
                to_skip = len('if ')
            elif node_text.startswith('elif'):
                to_skip = len('elif ')
            else:
                return None
            start_x = node_start_x + to_skip
            end_y = start_y
            end_x = start_x

            for ch in node.text.decode()[to_skip:]:
                if ch == ':': break
                if ch == '\n':
                    end_x = 0
                    end_y += 1
                else:
                    end_x += 1
            end_x -= 1 # remove the ':' from the range

            return Scope(start_x, start_y, end_x, end_y)

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

            return Scope(start_x, start_y, end_x-1, end_y)
        return None

    def get_inner_method(self, x, y):
        x += 1
        if self.language == 'python':
            query = self._language.query("(function_definition (block) @name)")
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the new line char
            return Scope(start_x, start_y, end_x, end_y)

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

            return Scope(start_x, start_y, end_x, end_y)
        return None

    def get_arround_method(self, x, y):
        x += 1 # index is out of sync?
        if self.language == 'python':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]
            end_x -= 1 # exclude the new line char
            return Scope(start_x, start_y, end_x, end_y)

        if self.language == 'c':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None

            start_y = node.start_point[0]
            start_x = node.start_point[1]
            end_y = node.end_point[0]
            end_x = node.end_point[1]

            return Scope(start_x, start_y, end_x, end_y)
        return None

    def get_inner_METHOD(self, x, y):
        x += 1
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
            return Scope(start_x, start_y, end_x, end_y)

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

            return Scope(start_x, start_y, end_x, end_y)
        return None

    def get_arround_METHOD(self, x, y):
        x += 1 # index is out of sync?
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
            return Scope(start_x, start_y, end_x, end_y)

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
            return Scope(start_x, start_y, end_x, end_y)
        return None

    def get_arround_argument(self, x, y):
        x += 1 # index is out of sync?
        if self.language == 'python':
            query = self._language.query("""
            (argument_list) @name
            """)
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            for parameter in node.children:
                start_y = parameter.start_point[0]
                start_x = parameter.start_point[1]
                end_y = parameter.end_point[0]
                end_x = parameter.end_point[1]

                if start_y > y: continue
                if end_y < y: continue
                if start_y == y and start_x > x: continue
                if end_y == y and end_x < x: continue

                end_x -= 1 # why python parser returns the end exclusive?
                return Scope(start_x, start_y, end_x, end_y)

        if self.language == 'c':
            query = self._language.query("""
            (argument_list) @name
            """)
            node = self._get_relevant_nodes(self.tree.root_node, query, x,y, most_relevant=True)
            if not node: return None

            for parameter in node.children:
                start_y = parameter.start_point[0]
                start_x = parameter.start_point[1]
                end_y = parameter.end_point[0]
                end_x = parameter.end_point[1]

                if start_y > y: continue
                if end_y < y: continue
                if start_y == y and start_x > x: continue
                if end_y == y and end_x < x: continue

                end_x -= 1 # why c parser returns the end exclusive?
                return Scope(start_x, start_y, end_x, end_y)
        return None

    def get_next_method(self, x, y):
        x += 1
        if self.language == 'python':
            query = self._language.query("(function_definition) @name")
            methods = query.captures(self.tree.root_node)
            for method, name in methods:
                method_x = method.start_point[1]
                method_y = method.start_point[0]
                if method_y > y: return method_x, method_y
            return None
        if self.language == 'c':
            query = self._language.query("(function_definition) @name")
            methods = query.captures(self.tree.root_node)
            for method, name in methods:
                method_x = method.start_point[1]
                method_y = method.start_point[0]
                if method_y > y: return method_x, method_y
            return None
        return None

    def get_prev_method(self, x, y):
        x += 1
        if self.language == 'python':
            query = self._language.query("(function_definition) @name")
            methods = query.captures(self.tree.root_node)
            for method, name in reversed(methods):
                method_x = method.start_point[1]
                method_y = method.start_point[0]
                if method_y < y: return method_x, method_y
            return None
        if self.language == 'c':
            query = self._language.query("(function_definition) @name")
            methods = query.captures(self.tree.root_node)
            for method, name in reversed(methods):
                method_x = method.start_point[1]
                method_y = method.start_point[0]
                if method_y < y: return method_x, method_y
            return None
        return None

    def get_method_end(self, x, y):
        if self.language == 'python':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None
            method_x = node.end_point[1]
            method_y = node.end_point[0]
            return method_x, method_y
        if self.language == 'c':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None
            method_x = node.end_point[1]
            method_y = node.end_point[0]
            return method_x, method_y
        return None

    def get_method_begin(self, x, y):
        if self.language == 'python':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None
            method_x = node.start_point[1]
            method_y = node.start_point[0]
            return method_x, method_y
        if self.language == 'c':
            query = self._language.query("(function_definition) @name")
            node = self._get_relevant_nodes(self.tree.root_node, query, x, y, most_relevant=True)
            if not node: return None
            method_x = node.start_point[1]
            method_y = node.start_point[0]
            return method_x, method_y
        return None

if __name__ == '__main__':
    Language.build_library(
        # Store the library in the `build` directory
        'grammars/tree-sitter-lib/my-languages.so',

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
        ]
    )
