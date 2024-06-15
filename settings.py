from os import path
import json

from log import elog


EDITOR_HOME_PATH = path.expanduser('~/.config/editor/')
INSTALLATION_PATH = path.dirname(path.abspath(__file__))
g_settings = {}

def add_to_theme(scope, style):
    global g_settings
    if scope not in g_settings['theme_opt']:
        g_settings['theme_opt'][scope] = style

def optimize_theme():
    global g_settings

    g_settings['theme_opt'] = {}

    theme = g_settings['theme']

    token_colors = theme['tokenColors']
    for token in token_colors:
        if "settings" not in token: continue
        if "scope" not in token: continue
        if isinstance(token['scope'], list):
            for s in token['scope']:
                add_to_theme(s, token["settings"])
        else:
            scopes = [x.strip() for x in token['scope'].split(',')]
            for s in scopes:
                add_to_theme(s, token["settings"])

def load_settings():
    global g_settings

    with open(  path.join(EDITOR_HOME_PATH, 'config.json'),
                'r') as f:
        g_settings = json.loads(f.read())

    with open(  path.join(EDITOR_HOME_PATH, g_settings['theme_path']),
                'r') as f:
        g_settings['theme'] = json.loads(f.read())

    optimize_theme()

def get_settings():
    global g_settings
    return g_settings

def get_setting(key, default=None):
    if key == "line_numbers":
        _ = False if not default else default
        return get_settings().get(key, _)
    if key == "status_line":
        _ = False if not default else default
        return get_settings().get(key, _)
    if key == "windows_separator_color":
        _ = "#4C4C47" if not default else default
        return get_settings().get(key, _)
    if key == "status_line_background":
        _ = "#4C4C47" if not default else default
        return get_settings().get(key, _)
    if key == "status_line_foreground":
        _ = "#000000" if not default else default
        return get_settings().get(key, _)

    if key == "line_numbers_background":
        _ = "#2D2D2A" if not default else default
        return get_settings().get(key, _)
    if key == "line_numbers_foreground":
        _ = "#4C4C47" if not default else default
        return get_settings().get(key, _)

    if key == "search_highlights_background":
        _ = "#FFC09F" if not default else default
        return get_settings().get(key, _)
    if key == "search_highlights_foreground":
        _ = "#000000" if not default else default
        return get_settings().get(key, _)

    if key == "multi_cursors_background":
        _ = "#FFC000" if not default else default
        return get_settings().get(key, _)
    if key == "multi_cursors_foreground":
        _ = "#000000" if not default else default
        return get_settings().get(key, _)

    if key == "menu_background":
        _ = "#3C474B" if not default else default
        return get_settings().get(key, _)
    if key == "menu_foreground":
        _ = "#C0E0DE" if not default else default
        return get_settings().get(key, _)

    if key == "tab_representation":
        _ = ">\u00b7\u00b7\u00b7" if not default else default
        return get_settings().get(key, _)
    if key == "tab_insert":
        _ = "    " if not default else default
        return get_settings().get(key, _)
    if key == "syntax":
        _ = "sync" if not default else default
        return get_settings().get(key, _)

    return get_settings().get(key, default)

load_settings()
