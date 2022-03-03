from events import *
from hooks import *

class Buffer():
    def __init__(self, file_path=None):
        Hooks.execute(ON_BUFFER_CREATE_BEFORE, self)

        self.lines = []
        self.file_path = None


        if not file_path: 
            Hooks.execute(ON_BUFFER_CREATE_AFTER, self)
            return
        
        try:
            with open(file_path, 'r') as f:
                self.lines = f.readlines()
                # self.lines = [l.strip() for l in f.readlines()]
        except:pass
        Hooks.execute(ON_BUFFER_CREATE_AFTER, self)

    def destroy(self):
        Hooks.execute(ON_BUFFER_DESTROY_BEFORE, self)
        Hooks.execute(ON_BUFFER_DESTROY_AFTER, self)

    def write_to_file(self, file_path):
        if not self.file_path: 
            self.file_path = file_path

        with open(file_path, 'w+') as f:
            f.writelines(self.lines)

    def write(self):
        if not self.file_path: 
            raise Exception("No file attached to buffer.")

        with open(self.file_path, 'w+') as f:
            f.writelines(self.lines)
