from os import path, listdir
import re

from log import elog


def is_binary_file(file):
    bytes = open(file, 'rb').read()
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    return bytes.translate(None, textchars)

def extract_destination(string):
    file_path = None
    file_line = None
    file_col = None

    try:
        m = re.match(f'^(?P<file_path>[\\w\\.\\/\\-]+)(:(?P<file_line>\\d+):(?P<file_col>\\d+))?.*$',
                    string)
        if not m: return None, None, None

        file_path = m.group('file_path')
        file_line = m.group('file_line')
        if file_line: file_line = int(file_line) - 1
        file_col = m.group('file_col')
        if file_col: file_col = int(file_col) - 1
        if not path.isfile(file_path): return None, None, None
    except Exception as e: elog(f"Exception: {e}")

    return file_path, file_line, file_col

def find_files_suggestions(start_x, start_of_path):
    # explicit relative path
    path_until_now = start_of_path.split('./', 1)
    if len(path_until_now) == 2:
        to_add = start_of_path.find('./')
        path_until_now = './'+path_until_now[1]

        dir_name = path.dirname(path_until_now)
        file_prefix = path.basename(path_until_now)

        files = listdir(dir_name)
        suggestions = []
        for file_name in files:
            if not file_name.startswith(file_prefix): continue
            suggestions.append((file_name, file_name[len(file_prefix):]))

        return (start_x + to_add + len(dir_name) + len('/'), suggestions)

    # explicit absolut path
    path_until_now = start_of_path.split('/', 1)
    if len(path_until_now) == 2:
        to_add = start_of_path.find('/')
        path_until_now = '/'+path_until_now[1]

        dir_name = path.dirname(path_until_now)
        add_slash = 0 if dir_name == '/' else 1
        file_prefix = path.basename(path_until_now)

        files = listdir(dir_name)
        suggestions = []
        for file_name in files:
            if not file_name.startswith(file_prefix): continue
            suggestions.append((file_name, file_name[len(file_prefix):]))

        return (start_x + to_add + len(dir_name) + add_slash, suggestions)

    # # implicit relative path
    # to_add = start_of_path.find('./')
    # path_until_now = './'+path_until_now[1]

    # elog(f"path_until_now: {path_until_now}")

    # dir_name = path.dirname(path_until_now)
    # file_prefix = path.basename(path_until_now)

    # files = listdir(dir_name)
    # suggestions = []
    # for file_name in files:
        # if not file_name.startswith(file_prefix): continue
        # suggestions.append((file_name, file_name[len(file_prefix):]))

    # return (start_x + to_add + len(dir_name) + len('/'), suggestions)

if __name__=='__main__':
    print('-'*80)
    elog('-'*80)
    print(find_files_suggestions(1, './ut'))
    print('-'*80)
    print(find_files_suggestions(1, './themes/da'))
    print('-'*80)
    print(find_files_suggestions(1, './'))
    print('-'*80)
    print(find_files_suggestions(1, './themes/'))
    print('-'*80)
    print(find_files_suggestions(1,'a=./ut'))
    print('-'*80)
    # print(find_files_suggestions('VI = ./ut'))
    # print('-'*80)
    # print(find_files_suggestions('ASDJKFL=./'))
    # print('-'*80)

    # print(find_files_suggestions('ut'))
    # print('-'*80)
    # print(find_files_suggestions('/bi'))
    # print('-'*80)
    # print(find_files_suggestions('/bin/'))
    # print('-'*80)
