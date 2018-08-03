# -*- coding: utf-8 -*
"""
线程池工作
1.创建Queue.Queue()队列实例，然后使用填充任务
2.生成守护线程池，将线程设置成了daemon守护线程
3.每个线程无限循环阻塞读取queue队列的项目并处理
4.每次完成一次工作后，使用queue.task_done()函数向任务已经完成的队列发送一个信号
5.主线程设置queue.join()阻塞，直到任务队列清空，解除阻塞，向下执行。
"""
import threading 
from time import sleep, ctime
from Queue import Queue 

lock = threading.Lock()

# 线程类
class ThreadManager(threading.Thread):
	"""定义线程类"""

	def __init__(self, work_queue, func = 'function_error', args = ''):
		# 初始化线程队列、以及设置成守护线程
		threading.Thread.__init__(self)
		self.work_queue = work_queue
		self.daemon = True # 线程池的线程设置成daemon守护进程，主线程退出，则守护线程自动退出
		self.func = func # 函数名
		self.args = args # 函数参数

	def run(self):
		# 线程来执行函数任务 
		while True:
			self.func, self.args = self.work_queue.get()
			self.func(*self.args)
			# 每次线程queue.get()后处理任务后，发送queue.task_done()信号，
			# queue的长度就会减一，queue的数据为空，queue.join()解除阻塞，向下执行
			self.work_queue.task_done()

# 线程池管理类
class ThreadPoolManager(object):
	"""线程池管理器"""

	def __init__(self, thread_num):
		# 初始化参数
		self.work_queue = Queue()
		self.thread_num = thread_num
		self.__init_threading_pool(self.thread_num)

	def __init_threading_pool(self, thread_num):
		# 初始化线程池，创建指定线程数量的线程池
		for i in range(thread_num):
			thread = ThreadManager(self.work_queue)
			thread.start()

	def add_job(self, func, args):
		# 将任务放入队列，等待线程池阻塞读取，参数是一个元组，元组中元素分别为函数名，函数参数元组
		self.work_queue.put((func, args))

def loop(nloop, nsec):
	"""
	不希望多线程同时执行这部分代码和函数，则可以通过加锁的方式
	lock.acquire()
	lock.release()
	"""
	print '当前线程名: ', threading.current_thread().name
	print 'start loop', nloop, 'at:', ctime()
	sleep(nsec)
	print 'loop', nloop, 'done at:', ctime()

# 任务列表，其中分别是函数名和对应函数元组参数所组成的元组序列
all_functions_TupleParam = [(loop, (1,4)), (loop, (2,10)), (loop, (3,5)), (loop, (4,4)), (loop, (5,10)), (loop, (6,7)), (loop, (7,6))]

def main():
	print 'starting at: ', ctime()
	thread_pool = ThreadPoolManager(2)
	for each in all_functions_TupleParam:
		func, args = each
		thread_pool.add_job(func, args)
	thread_pool.work_queue.join()
	print 'all done at: ', ctime()

if __name__ == '__main__':
	main()

