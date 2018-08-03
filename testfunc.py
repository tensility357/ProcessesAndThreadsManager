import os
import time

def long_time_task(name):
    print 'Run task {0} ({1})'.format(name,os.getpid())
    start = time.time()
    time.sleep(10)
    end = time.time()
    print {'task' : name, 'pid' : os.getpid(), 'runtime' : end - start}
    print 'Task {0} runs {1:.2f} seconds.'.format(name,end - start)
    return long_time_task.__name__

#long_time_task('hello')