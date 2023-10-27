#!/usr/bin/python3
import json

from treesitter import TreeSitter
from settings import get_settings
from log import elog

from functools import lru_cache


def _get_scope_style(theme, scope):
    token_colors = theme['tokenColors']
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
                target_scopes = scope.split('.')
                if s == scope: return token["settings"]

                for i in range(len(target_scopes) - 1, 0, -1):
                    curr = '.'.join(target_scopes[:i])
                    if curr == s: return token['settings']

@lru_cache(None)
def get_scope_style(scope):
    theme = get_settings()['theme_opt']
    if scope in theme: return theme[scope]
    target_scopes = scope.split('.')
    for i in range(len(target_scopes) - 1, 0, -1):
        curr = '.'.join(target_scopes[:i])
        if curr in theme: return theme[curr]

    return None

def get_syntax_highlights(  treesitter,
                            target_node=None,
                            start_point=None,
                            end_point=None):
    for c in treesitter.get_captures(   target_node,
                                        start_point,
                                        end_point):
        node, scope = c[0], c[1]

        style = get_scope_style(scope)
        if not style: continue
        yield (node, style)


if __name__ == '__main__':
    with open('themes/monokai-color-theme.json', 'r') as f: theme = json.loads(f.read())
    with open('editor', 'rb') as f: treesitter = TreeSitter(f.read(), 'c')

    print(treesitter.query.captures(treesitter.tree.root_node,
                                    start_point=(0,0),
                                    end_point=(10,10)))
    # for hl in get_syntax_highlights(treesitter, theme):
        # print(hl)
