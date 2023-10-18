#!/usr/bin/python

from concurrent.futures import ThreadPoolExecutor

from idr import *


class Task():
    def __init__(self, callback, arg):
        self.id = get_id(TASK_ID)
        self.callback = callback
        self.arg = arg
        self.future = None
        self.on_done_callback = None

    def __on_done(self, future): pass

    def on_done(self, callback):
        self.on_done_callback = callback

    def start(self):
        pool = ThreadPoolExecutor(max_workers=1)
        self.future = pool.submit(self.callback, self.arg)

        self.future.add_done_callback(self.__on_done)
        if self.on_done_callback:
            self.future.add_done_callback(self.on_done_callback)

    def abort(self):
        # TODO
        pass

    def done(self):
        if not self.future: return True
        return self.future.done()


import time
if __name__=='__main__':
    def work(secs):
        print("before sleep")
        time.sleep(secs)
        print("after sleep")
        return 100

    aaa = "this ia a context.."
    def on_done(future):
        print(future.result())
        print(aaa)

    task = Task(work, 2)
    task.on_done(on_done)
    task.start()

    while not task.done():
        time.sleep(1)
        print('waiting...')
    time.sleep(2)


