from os import path
import json

from log import elog

g_settings = {}
EDITOR_HOME_PATH = path.expanduser('~/.config/editor/')

with open(  path.join(EDITOR_HOME_PATH, 'config.json'),
            'r') as f:
    g_settings = json.loads(f.read())

with open(  path.join(EDITOR_HOME_PATH, g_settings['theme_path']),
            'r') as f:
    g_settings['theme'] = json.loads(f.read())

g_settings['theme_opt'] = {}

def add_to_theme(scope, style):
    if scope not in g_settings['theme_opt']:
        g_settings['theme_opt'][scope] = style
    else: 
        elog(f"scope: {scope}")

def optimize_theme():
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

optimize_theme()
