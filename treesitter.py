#!/usr/bin/python3
from tree_sitter import Language, Parser

from log import elog

# Language.build_library(
        # # Store the library in the `build` directory
        # 'grammars/tree-sitter-lib/my-languages.so',

        # # Include one or more languages
        # [
            # 'vendor/tree-sitter-python'
        # ]
    # )

PY_LANGUAGE = Language('grammars/tree-sitter-lib/my-languages.so', 'python')

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
    def __init__(self, file_bytes):
        with open("grammars/python/highlights.scm" ,"r") as f: query = f.read()

        self.query = PY_LANGUAGE.query(query)
        self.parser = Parser()
        self.parser.set_language(PY_LANGUAGE)

        self.tree = self.parser.parse(file_bytes)
        self.captures = None

    def tree_edit(self, edit, new_file_bytes):
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

    def get_captures(self):
        if not self.captures:
            self.captures = list(self.query.captures(self.tree.root_node))
            elog(f"{len(self.captures)}")
        return self.captures

if __name__ == '__main__':
    with open("editor", "rb") as f: file_bytes = f.read()

    ts = TreeSitter(file_bytes)
    captures = ts.get_captures()
    for c in captures:
        print(c)
