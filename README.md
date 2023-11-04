# Editor

## Syntax Highlighting

### The Parsers
The syntax highlighting system works with treesitter.

`pip3 install tree_sitter`

```python
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
```

The vendor folders you will clone from github - examples:

```
vendor> git clone https://github.com/tree-sitter/tree-sitter-go
vendor> git clone https://github.com/tree-sitter/tree-sitter-javascript
vendor> git clone https://github.com/tree-sitter/tree-sitter-python
```

### The Themes

The theme files should come as a json format. currently using vs code theme:
- See `themes/monokai-color-theme.json`.

### The Grammar

Treesitter enable us to parse th code file and get its Abstract Syntax Tree
(AST) in a fast, flexible, and efficiant way. But this is not enough, the
themes uses a seperate terminology to map a style to an element inside a file.
Something need to map between Treesitter's AST and the Theme's terminology.

That is the job of the grammar. It will convert the AST identifiers into a
`scope` terminology that the themes can understand.

The Atom
[Documentation](https://flight-manual.atom.io/hacking-atom/sections/creating-a-grammar/)
Explain it perfectly. Also Atoms mapings will be used as grammars:

- [C](https://raw.githubusercontent.com/atom/language-c/master/grammars/tree-sitter-c.cson)
- [Python](https://raw.githubusercontent.com/atom/language-python/master/grammars/tree-sitter-python.cson)

## TODOs
- visual block mode
- adding kill to tasks
- adding popup for managing tasks
- make asterisk work as <cword> in vim
- record jumps in all the right places
- when pasting from clipboard it is very slow because of the insert operation
    - make it faster by pasting it directly from the clipboard instead of inserting
    char by char
- make ALL delete operations to also yank the text...
    - never thought this is something I used so much, I actually useless without it.
- add support for diff output
- add support for bash scripts
- add support to <ctrl><x><f> in insert mode: auto complete filesystem paths

- in visual line mode, when highlights are one and we change the selected lines,
  the highlight do not drawing smoothly
- take influence from helix/kakoun
    - mutli lines selection
    - server/client architecture
- make gq take into account the indent level..
- horizontal scrolling
- add tabs status line like in vim
    - adding set_position() and resize() methods in Tab class
    - on ENTER, toggle
        - tabs status
        - line numbers for all windows
        - status line on all windows
- move windows (especially in the rg cases)
- add command auto complete at tab
- searching in large files is extremely slow

- `=` operator

- FIX: on search, the prompt isn't draw smoothly as we write more and more characters
- BUG: difflib is extremely slow or maybe even freezes
    - try to comment/indent all lines of a large file
- BUG: tab._adjust_sizes() corner case:
    - vsplit, split, move_left, split
    - close a window will cause colition of windows
- BUG: in visual mode, tabs do not uses the right style
- BUG: status line dont show if cursor is on last line

- ctags
- maybe add ast based text object?
    - `if`/`af` inner/arround if
    - `ir`/`ar` inner/arround for
    - `ie`/`ae` inner/arround while
    - `iy`/`ay` inner/arround try
    - `im`/`am` inner/arround method/function
- goto
    - start of function

