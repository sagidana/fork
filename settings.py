import json



g_settings = {}

with open('config.json', 'r') as f: g_settings = json.loads(f.read())
with open(g_settings['theme_path'], 'r') as f: g_settings['theme'] = json.loads(f.read())
