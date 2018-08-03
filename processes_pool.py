# -*- coding: utf-8 -*
import multiprocessing
from multiprocessing import Pool, Process
import os, time,sys
import psutil

class MultiProcessPool(object):
	""" 
	进程池管理类 
	assign_task(): 创建任务，将任务的函数名和参数传入到任务列表中
	apply_async(): 执行所有任务，批量创建子进程
	join() 阻塞等待所有子进程运行结果，可以指定回调函数来处理子进程返回的结果
	"""
	def __init__(self, ncpu = None):
		# 创建与CPU核数大小相同的进程池，如果不传入cpu的核数，则默认是cpu的逻辑个数 我的电脑默认是4个进程 
		self._pool = Pool(processes = ncpu)
		self._tasks = {} # 当前子进程的结果对象 以键(对象id) : 值(任务返回的结果对象multiprocessing.pool.AsyncResult)保存
		self._cmds = [] # 保存所有task的入口函数和参数
		self.__process_info = [] # 列表中元素为进程池中的进程字典信息,私有属性

	def __init_func(self, text):
		# 每执行一个函数成功的回调函数
		print '执行%s函数成功!' %(text)
		

	def __len__(self):
		# 线程池中执行的任务数量
		return len(self._tasks)

	@property
	def processes(self):
		# 返回能够同时运行的任务数量  只读属性
		return self._pool._processes

	@property
	def process_info(self):

		for each in self._pool._pool:
			process_info_dict = {}
			p = psutil.Process(each.pid)
			process_info_dict['pid'] = each.pid
			process_info_dict['proType'] = 'intern'
			p.cpu_percent()
			process_info_dict['cpu'] = p.cpu_percent()
			virtual_memory = p.memory_full_info().vms / 1204 / 1204
			reality_memory = p.memory_full_info().rss / 1024 / 1024
			process_info_dict['real mem'] = 'reality memory is {0}M'.format(reality_memory)
			process_info_dict['virtual mem'] = 'virtual memory is {0}M'.format(virtual_memory)
			self.__process_info.append(process_info_dict)
		return self.__process_info

	def assign_task(self, task_func, args = None):
		# 分配一个任务，不立即执行，之后被apply_async()运行
		item = task_func, args
		self._cmds.append(item) # 将任务的函数名和参数组成的元组传入到列表中

	def apply_async(self):
		# 执行任务列表中的所有的任务 Pool.apply_async是异步非阻塞的
		while self._cmds:
			cmd = self._cmds.pop()
			func, args = cmd
			if args and not isinstance(args, tuple):
				# 如果args不为None，并且不是元组类型，则报类型异常
				raise TypeError('args should be a tuple, not %s' % type(args))
			# 创建子进程，将结果以键值对的形式保存到结果字典中
			self._tasks[id(cmd)] = self._pool.apply_async(func, args = args, callback = self.__init_func)
		return len(self._tasks)

	def join(self, task_handle = None, args = None, pre_handle = None, post_handle = None,
		wait_handle = None, wait_internal = 0.5, timeout = None):
		"""
		函数功能: 每隔wait_internal(默认0.5秒)从传入的任务队列中检查所有执行完成的任务并处理
		task_handle: 用户可传入回调函数处理任务返回的结果 
		args: 函数参数
		pre_handle： 预处理函数
		post_handle: 返回处理函数
		wait_handle: 等待函数
		wait_internal： 等待时间间隔
		timeout: 超时退出时间
		"""
		start_time = time.time()
		if pre_handle:
			pre_handle(args)
		while self._tasks:
			# 遍历所有子进程，找到已经运行完成的子进程
			done = [tid for tid, task in self._tasks.items() if task.ready()]
			for tid in done:
				# 获取每一个完成的子进程运行结果
				ret = self._tasks[tid].get()
				del self._tasks[tid] # 从子进程dict里删除 
				# 调用用户的回调函数来处理返回的结果
				if task_handle:
					task_handle(args, ret)
			time.sleep(wait_internal) # 一段时间又检查任务列表中执行完成的任务
			if wait_handle:
				wait_handle(args)
			if timeout and time.time() - start_time > timeout:
				break # 超时退出
		if post_handle:
			post_handle(args)

		return len(self._tasks)
 
# # 简单测试进程池
# def long_time_task(name):
#     print 'Run task {0} ({1})'.format(name,os.getpid())
#     start = time.time()
#     time.sleep(3)
#     end = time.time()
#     print 'Task {0} runs {1:.2f} seconds.'.format(name,end - start)
#     return {'task' : name, 'pid' : os.getpid(), 'runtime' : end - start}

# 用户的回调函数，记录任务运行的结果
results = []
def handle_result(args, result):
	results.append(result)

if __name__=='__main__':

    print 'Parent process ({0})'.format(os.getpid())

    # 创建进程池
    pool = MultiProcessPool()
    # 创建任务
    for i in range(12):
    	pool.assign_task(long_time_task, args = (i,))
    pool.apply_async()
    pool.join(handle_result)
    print sys.argv[0]

    # 等待所有任务结束，并处理结果
    print 'Waiting for all subprocesses done...'
    print 'All subprocesses done.'

    # 将所有任务的结果打印出来
    for each in results:
    	print each

"""
测试结果:
Parent process (6780)
Waiting for all subprocesses done...
All subprocesses done.
{'task': 10, 'pid': 12516, 'runtime': 3.0}
{'task': 11, 'pid': 9836, 'runtime': 3.0}
{'task': 8, 'pid': 936, 'runtime': 3.0}
{'task': 9, 'pid': 6124, 'runtime': 3.0}
{'task': 7, 'pid': 9836, 'runtime': 3.0}
{'task': 6, 'pid': 12516, 'runtime': 3.000999927520752}
{'task': 5, 'pid': 6124, 'runtime': 3.000999927520752}
{'task': 4, 'pid': 936, 'runtime': 3.000999927520752}
{'task': 3, 'pid': 9836, 'runtime': 3.0}
{'task': 2, 'pid': 12516, 'runtime': 3.0}
{'task': 0, 'pid': 936, 'runtime': 3.0}
{'task': 1, 'pid': 6124, 'runtime': 3.0}
Run task 11 (9836)
Task 11 runs 3.00 seconds.
Run task 7 (9836)
Task 7 runs 3.00 seconds.
Run task 3 (9836)
Task 3 runs 3.00 seconds.
Run task 10 (12516)
Task 10 runs 3.00 seconds.
Run task 6 (12516)
Task 6 runs 3.00 seconds.
Run task 2 (12516)
Task 2 runs 3.00 seconds.
Run task 9 (6124)
Task 9 runs 3.00 seconds.
Run task 5 (6124)
Task 5 runs 3.00 seconds.
Run task 1 (6124)
Task 1 runs 3.00 seconds.
Run task 8 (936)
Task 8 runs 3.00 seconds.
Run task 4 (936)
Task 4 runs 3.00 seconds.
Run task 0 (936)
Task 0 runs 3.00 seconds.
[Finished in 10.6s]
"""