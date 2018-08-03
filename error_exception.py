# -*- coding: utf-8 -*

class InputAddressException(Exception):
	# 输入程序路径错误异常类

	def __init__(self, errorinfo):
		Exception.__init__(self)
		self.errorinfo = errorinfo

	def __str__(self):
		return self.errorinfo

