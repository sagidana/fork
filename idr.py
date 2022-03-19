BUFFER_ID = "buffer"
WINDOW_ID = "window"
TAB_ID = "tab"

def get_id(type):
    if type == BUFFER_ID:
        _id = get_id.buffer_last_id 
        get_id.buffer_last_id += 1
        return _id
    if type == WINDOW_ID:
        _id = get_id.window_last_id 
        get_id.window_last_id += 1
        return _id
    if type == TAB_ID:
        _id = get_id.tab_last_id 
        get_id.tab_last_id += 1
        return _id

get_id.buffer_last_id = 0
get_id.window_last_id = 0
get_id.tab_last_id = 0

