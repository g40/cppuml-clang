#!/usr/bin/env python
#
#	BSD 3-Clause License
#
#   Copyright (c) 2022, Jerry Evans
#   All rights reserved.
#   See LICENCE.md for full details
#

#------------------------------------------------------------------------------
from typing import Any

#------------------------------------------------------------------------------
class Stack:
	
	#--------------------------------------------------------------------------
	def __init__(self):
		""" constructor """
		self._data = []
	
	#--------------------------------------------------------------------------
	def depth(self) -> int:
		""" how deep is the stack? """
		return len(self._data)
	
	#--------------------------------------------------------------------------
	def is_empty(self) -> bool:
		""" True if empty """
		return len(self._data) == 0
	
	#--------------------------------------------------------------------------
	def push(self, item) -> None:
		""" push an item onto the stack """
		self._data.append(item)
		
	#--------------------------------------------------------------------------
	def top(self) -> Any:
		""" get the topmost item else None """
		if self.is_empty():
			return None
		return self._data[-1]
	
	#--------------------------------------------------------------------------
	def pop(self) -> Any:
		""" pop an item else None if empty"""
		if self.is_empty():
			return None
		return self._data.pop()
