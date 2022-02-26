class Buffer():
    def __init__(self, file_path=None):
        self.lines = []
        self.file_path = None

        if not file_path: return
        
        try:
            with open(file_path, 'r') as f:
                self.lines = f.readlines()
        except:pass

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
