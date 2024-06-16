#!/usr/bin/python
from threading import Thread

from log import elog
from idr import *


class Task():
    def __init__(self, callback, arg):
        self.id = get_id(TASK_ID)
        self.on_done_callback = None
        self.ret = None
        def wrapper(arg):
            self.ret = callback(arg)
            if self.on_done_callback:
                self.on_done_callback(self.ret)

        self.thread = Thread(target=wrapper, args=(arg, ))

    def on_done(self, callback):
        self.on_done_callback = callback

    def start(self): self.thread.start()

    def wait(self):
        self.thread.join()
        return self.ret

    def kill(self): pass # TODO: to implement

    def done(self): return not self.thread.is_alive()

import time
if __name__=='__main__':
    def work(secs):
        print("before sleep")
        time.sleep(secs)
        print("after sleep")
        return 100

    aaa = "this ia a context.."
    def on_done(ret):
        print(ret)
        print(aaa)

    task = Task(work, 3)
    task.on_done(on_done)
    task.start()

    while not task.done():
        time.sleep(1)
        print('waiting...')
    time.sleep(2)


