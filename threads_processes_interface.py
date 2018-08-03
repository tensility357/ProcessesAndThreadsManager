# -*- coding: utf-8 -*

"""
计算框架，包括进程管理和线程管理，以及该系统对资源的消耗情况的统计
getProcessStat 获取计算框架中的进程信息，可以统计其资源消耗 
参数: 无
返回值： 字典列表 字典包含pid、进程处理任务函数路径、进程的标识、cpu占用、进程内存占用

createThread 创建一个线程池，用于计算或业务处理
参数: 任务函数路径、args任务函数参数 
返回值: 状态码、返回结果
"""

import os
import sys
import psutil
import subprocess
import threading
from time import ctime, sleep
from inspect import isfunction
from processes_pool import MultiProcessPool
from threads_pool import ThreadPoolManager
from error_exception import InputAddressException

from testfunc import long_time_task

class ThreAndProPoolManager(object):
	""" 对外提供三个接口来进线程管理和任务的分配 """

	def __init__(self, ncpu = None, threadsNum = 4):
		# 属性为内部进程池和内部线程池，外部进程列表
		self.inner_process_pool = MultiProcessPool(ncpu)
		self.inner_thread_pool = None
		self.extern_process_list = [] # 元素是每个进程的字典信息
		self.processess_pool_info = [] #当前所有存活进程

		self.__escape_dict = {'\a':r'\a',
         '\b':r'\b',
         '\c':r'\c',
         '\f':r'\f',
         '\n':r'\n',
         '\r':r'\r',
         '\t':r'\t',
         '\v':r'\v',
         '\'':r'\'',
         '\"':r'\"',
         '\0':r'\0',
         '\1':r'\1',
         '\2':r'\2',
         '\3':r'\3',
         '\4':r'\4',
         '\5':r'\5',
         '\6':r'\6',
         '\7':r'\7',
         '\8':r'\8',
         '\9':r'\9'}

	def createProcess(self, proAddr,  proType):
		"""
		createProcess(proAddr, func, args, proType) 创建内部或外部进程  
		extern : 参数: ”python /opt/nsfocus/bin/test.py”执行脚本字符串， proType为extern
		inner: 参数: ((函数名，(参数，))))元组信息 proType为inner
		"""

		if 'extern' == proType:
			proAddr = self.__turn_to_rawstring(proAddr)
			# 判断外部输入路径是否存在，文件是否存在
			if not self.__is_address_correct(proAddr):
				# 输入错误路径或文件名，返回错误码1
				return 1
			file_direct, file_name = self.__is_address_correct(proAddr)
			current_popen = subprocess.Popen(proAddr)
			p = psutil.Process(current_popen.pid)
			extern_pro_dict = {}
			extern_pro_dict['pid'] = current_popen.pid
			extern_pro_dict['proAddr'] = proAddr 
			extern_pro_dict['proType'] = proType
			extern_pro_dict['cpu'] = p.cpu_percent()
			reality_memory = p.memory_full_info().rss / 1024 / 1024
			virtual_memory = p.memory_full_info().vms / 1204 / 1204
			extern_pro_dict['real mem'] = 'reality memory is {0}M'.format(reality_memory)
			extern_pro_dict['virtual mem'] = 'virtual memory is {0}M'.format(virtual_memory)
			self.extern_process_list.append(extern_pro_dict)

		elif 'intern' == proType:
			for each in proAddr:
				func, args = each
				if self.__isfunc(func):
					# 是函数添加，不是则忽略并提示不是函数名
					self.inner_process_pool.assign_task(func, args)
			self.inner_process_pool.apply_async()
			self.inner_process_pool.join()
		else: 
			return 1
		# 创建成功，返回正确码0
		return 0

	def getProcessStat(self):
		# 返回所有进程的信息
		print 'The basic information of all external processes in the process list is as follows'
		for each in self.extern_process_list:
			print each
		print 'The basic information of all internal processes in the process pool is as follows'
		for each in self.inner_process_pool.process_info:
			print each

	def createThread(self, func, args = None, threadnum = 4):
		"""
		用户可以使用单线程运行函数
		也可以通过指定线程数量来创建线程池运行批量函数任务，默认线程数为4
		"""
		if threadnum == 1:
			t = threading.Thread(target = func, args = args)
			t.start()
		else:
			self.inner_thread_pool = ThreadPoolManager(threadnum)
			for each in func:
				func, args = each
				self.inner_thread_pool.add_job(func, args)
			self.inner_thread_pool.work_queue.join()
		return 0

	def __turn_to_rawstring(self, text):
		# 将输入路径字符串转成raw string
		new_string = ''
		for char in text:
			try:
				new_string += self.__escape_dict[char]
			except KeyError:
				new_string += char
		return new_string

	def __is_address_correct(self, proAddr):
		# 判断用户输入的文件路径是否正确

		file_direction = proAddr.replace(' ', '')[6:]

		file_direct, file_name = os.path.split(file_direction)
		try:
			if not os.path.isdir(file_direct) or  not os.path.isfile(file_name):
				raise InputAddressException("输入的文件路径参数有误")
		except Exception as e:
			print '请重新传入文件路径参数'
			return None
		else:
			return file_direct, file_name

	def __isfunc(self, func):
		try:
			if not isfunction(func):
				raise InputAddressException("输入的函数有误")
		except Exception as e:
			print 'not func',func
			return False
		return True

# 用户的回调函数，记录任务运行的结果
results = []
def handle_result(args, result):
	results.append(result)

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

if __name__=='__main__':

    print 'Parent process ({0})'.format(os.getpid())
    proAddr = 'python Q:\project\ThreadAndProcessInterface\\testfunc.py'
    # 创建进程管理对象
    all_pool = ThreAndProPoolManager()
    # 创建任务,任务是由函数名和对应参数元组组成的键值对组成
    test_list = []
    for each in range(6):
    	item = long_time_task, (each,)
    	test_list.append(item)
    test_tuple = tuple(test_list)
    
    # all_pool.createProcess(proAddr,  proType = 'extern')


    # all_pool.getProcessStat()

    # all_pool.createThread(long_time_task, ("task",) , 1)
    all_functions_TupleParam = [(loop, (1,4)), (loop, (2,10)), (loop, (3,5)), (loop, (4,4)), (loop, (5,10)), (loop, (6,7)), (loop, (7,6))]
    all_pool.createThread(all_functions_TupleParam)

    # 等待所有任务结束，并处理结果
    print 'Waiting for all subprocesses done...'
    print 'All subprocesses done.'

    # 将所有任务的结果打印出来
    

"""
createProcess(self, proAddr,  proType)接口测试
extern形式:
proAddr = 'python Q:\project\ThreadAndProcessInterface\\testfunc.py'
all_pool = ThreAndProPoolManager()
all_pool.createProcess(proAddr,  proType = 'extern')

result:
Parent process (8096)
Waiting for all subprocesses done...
All subprocesses done.
Run task hello (13040)
{'task': 'hello', 'pid': 13040, 'runtime': 3.0149998664855957}
Task hello runs 3.01 seconds.
[Finished in 3.6s]

intern形式: 
all_pool = ThreAndProPoolManager()
# 创建任务,任务是由函数名和对应参数元组组成的键值对组成
test_list = []
for each in range(12):
	item = long_time_task, (each,)
	test_list.append(item)
test_tuple = tuple(test_list)

all_pool.createProcess(test_tuple,  proType = 'intern')

result:
Run task hello (9920)
{'task': 'hello', 'pid': 9920, 'runtime': 3.0119998455047607}
Task hello runs 3.01 seconds.
Parent process (9920)
Waiting for all subprocesses done...
All subprocesses done.
Run task hello (13668)
{'task': 'hello', 'pid': 13668, 'runtime': 3.002000093460083}
Task hello runs 3.00 seconds.
Run task 3 (13668)
{'task': 3, 'pid': 13668, 'runtime': 3.0139999389648438}
Task 3 runs 3.01 seconds.
Run task hello (6784)
{'task': 'hello', 'pid': 6784, 'runtime': 3.001999855041504}
Task hello runs 3.00 seconds.
Run task 2 (6784)
{'task': 2, 'pid': 6784, 'runtime': 3.0139999389648438}
Task 2 runs 3.01 seconds.
Run task hello (9076)
{'task': 'hello', 'pid': 9076, 'runtime': 3.002000093460083}
Task hello runs 3.00 seconds.
Run task 5 (9076)
{'task': 5, 'pid': 9076, 'runtime': 3.0139999389648438}
Task 5 runs 3.01 seconds.
Run task 1 (9076)
{'task': 1, 'pid': 9076, 'runtime': 3.001000165939331}
Task 1 runs 3.00 seconds.
Run task hello (11716)
{'task': 'hello', 'pid': 11716, 'runtime': 3.003000020980835}
Task hello runs 3.00 seconds.
Run task 4 (11716)
{'task': 4, 'pid': 11716, 'runtime': 3.014000177383423}
Task 4 runs 3.01 seconds.
Run task 0 (11716)
{'task': 0, 'pid': 11716, 'runtime': 3.000999927520752}
Task 0 runs 3.00 seconds.
[Finished in 13.2s]


getProcessStat(self)测试:
result:
执行long_time_task函数成功!
执行long_time_task函数成功!
执行long_time_task函数成功!
执行long_time_task函数成功!
执行long_time_task函数成功!
执行long_time_task函数成功!
The basic information of all external processes in the process list is as follows
{'proType': 'extern', 'pid': 10844, 'virtual mem': 'virtual memory is 0M', 
'proAddr': 'python Q:\\project\\ThreadAndProcessInterface\\testfunc.py', 'cpu': 0.0, 'real mem': 'reality memory is 0M'}
The basic information of all internal processes in the process pool is as follows
{'virtual mem': 'virtual memory is 4M', 'pid': 11488, 'cpu': 0.0, 'proType': 'intern', 'real mem': 'reality memory is 12M'}
{'virtual mem': 'virtual memory is 4M', 'pid': 7556, 'cpu': 0.0, 'proType': 'intern', 'real mem': 'reality memory is 12M'}
{'virtual mem': 'virtual memory is 4M', 'pid': 1172, 'cpu': 0.0, 'proType': 'intern', 'real mem': 'reality memory is 12M'}
{'virtual mem': 'virtual memory is 4M', 'pid': 11472, 'cpu': 0.0, 'proType': 'intern', 'real mem': 'reality memory is 12M'}


createThread(self, func, args = None, threadnum = 4)测试:
参数: 传入func,args元组参数
一个线程
all_pool = ThreAndProPoolManager()
all_pool.createThread(long_time_task, ("task",) , 1)
result:
Parent process (8704)
Waiting for all subprocesses done...
All subprocesses done.
Run task task (8704)
{'task': 'task', 'pid': 8704, 'runtime': 10.016000032424927}
Task task runs 10.02 seconds.
[Finished in 10.7s]

用户指定线程数量传入批量小函数
参数: 传入func, func为((函数,(参数,)), threadnum = 5
all_pool = ThreAndProPoolManager()
all_functions_TupleParam = [(loop, (1,4)), (loop, (2,10)), (loop, (3,5)), (loop, (4,4)), (loop, (5,10)), (loop, (6,7)), (loop, (7,6))]
all_pool.createThread(all_functions_TupleParam)

result:
Parent process (14608)
当前线程名:  Thread-4
start loop 1 at: Fri Aug 03 18:38:22 2018
当前线程名:  Thread-5
start loop 2 at: Fri Aug 03 18:38:22 2018
当前线程名:  Thread-6
start loop 3 at: Fri Aug 03 18:38:22 2018
当前线程名:  Thread-7
start loop 4 at: Fri Aug 03 18:38:22 2018
loop 1 done at: Fri Aug 03 18:38:26 2018
当前线程名:  Thread-4
start loop 5 at: Fri Aug 03 18:38:26 2018
loop 4 done at: Fri Aug 03 18:38:26 2018
当前线程名:  Thread-7
start loop 6 at: Fri Aug 03 18:38:26 2018
loop 3 done at: Fri Aug 03 18:38:27 2018
当前线程名:  Thread-6
start loop 7 at: Fri Aug 03 18:38:27 2018
loop 2 done at: Fri Aug 03 18:38:32 2018
loop 7 done at: Fri Aug 03 18:38:33 2018
loop 6 done at: Fri Aug 03 18:38:33 2018
loop 5 done at: Fri Aug 03 18:38:36 2018
Waiting for all subprocesses done...
All subprocesses done.
[Finished in 14.7s]
"""

