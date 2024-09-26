from os import path
import json

from .colors import brighten_color
from .log import elog


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
    if path.isfile(path.join(EDITOR_HOME_PATH, 'config.json')):
        with open(  path.join(EDITOR_HOME_PATH, 'config.json'),
                    'r') as f:
            g_settings = json.loads(f.read())
    else:
        with open(  path.join(INSTALLATION_PATH, 'config.json'),
                    'r') as f:
            g_settings = json.loads(f.read())

    if "theme_path" not in g_settings:
        with open(  path.join(INSTALLATION_PATH, "themes/monokai-color-theme.json"),
                    'r') as f:
            g_settings['theme'] = json.loads(f.read())
    else:
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
        background = get_settings()['theme']['colors'].get("statusBar.background", "#4C4C47")
        _ = background if not default else default
        return get_settings().get(key, _)
    if key == "status_line_foreground":
        foreground = get_settings()['theme']['colors'].get("statusBar.foreground", "#000000")
        _ = foreground if not default else default
        return get_settings().get(key, _)
    if key == "line_numbers_background":
        background = get_settings()['theme']['colors']['editor.background']
        _ = background if not default else default
        return get_settings().get(key, _)
    if key == "line_numbers_foreground":
        foreground = get_settings()['theme']['colors'].get('editorLineNumber.foreground', "#4C4C47")
        _ = foreground if not default else default
        return get_settings().get(key, _)
    if key == "cursor_highlight_background":
        background = get_settings()['theme']['colors'].get('editor.background')
        background = brighten_color(background, 15)
        _ = background if not default else default
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
        background = get_settings()['theme']['colors'].get('menu.background', "#3C474B")
        _ = background if not default else default
        return get_settings().get(key, _)
    if key == "menu_foreground":
        foreground = get_settings()['theme']['colors'].get('menu.foreground', "#C0E0DE")
        _ = foreground if not default else default
        return get_settings().get(key, _)
    if key == "menu_selected_background":
        background = get_settings()['theme']['colors'].get('menu.selectionBackground', "#FFC000")
        _ = background if not default else default
        return get_settings().get(key, _)
    if key == "menu_selected_foreground":
        foreground = get_settings()['theme']['colors'].get('menu.selectionForeground', "#000000")
        _ = foreground if not default else default
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
