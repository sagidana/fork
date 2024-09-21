class Scope():
    class Point():
        def __init__(self, x, y):
            self.x = x
            self.y = y

    def __init__(self, src_x, src_y, dst_x, dst_y):
        self.src = self.Point(src_x, src_y)
        self.dst = self.Point(dst_x, dst_y)

    @property
    def start(self):
        if self.src.y > self.dst.y:
            return self.dst
        if self.src.y == self.dst.y and self.src.x > self.dst.x:
            return self.dst
        return self.src

    @property
    def end(self):
        if self.src.y > self.dst.y:
            return self.src
        if self.src.y == self.dst.y and self.src.x > self.dst.x:
            return self.src
        return self.dst

    def copy(self):
        return Scope(self.src.x, self.src.y, self.dst.x, self.dst.y)

