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

Treesitter enable us to parse th code file and get its Abstraxt Syntax Tree
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


## Tabs
## Windows
## Buffers

## Features
- Modal Editing
- Syntax Highlight
- Folding

## TODOs
- selection
- <num><action>
- inner action
- around action

- line numbers
- statusline
- syntax highlighting
- folds
- ctags
- cscope
- splits
- tabs
