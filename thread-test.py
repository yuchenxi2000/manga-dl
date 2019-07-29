import threading
from queue import Queue
import math
import time
import random

q = Queue()
li = list()
cond = threading.Condition()
finished = False


def task(*arg):
    while True:
        if cond.acquire():
            if len(li) == 0:
                if not finished:
                    cond.wait()
                    cond.release()
                else:
                    cond.release()
                    return
            else:
                t = li.pop()
                cond.release()
                print('thread {} : {}'.format(arg[0], math.exp(t)))
                time.sleep(random.random())


th = threading.Thread(target=task, args=[1])
th2 = threading.Thread(target=task, args=[2])


def produce():
    global finished
    for i in range(10):
        if cond.acquire():
            li.append(i)
            cond.notifyAll()
            cond.release()
    if cond.acquire():
        finished = True
        cond.notifyAll()
        cond.release()


producer = threading.Thread(target=produce)

if __name__ == '__main__':
    th.start()
    th2.start()
    producer.start()
