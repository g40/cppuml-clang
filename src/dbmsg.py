#
#	BSD 3-Clause License
#
#   Copyright (c) 2022, Jerry Evans
#   All rights reserved.
#   See LICENCE.md for full details
#
#   Credit for originally showcasing Python inspect usage: 
#   https://stackoverflow.com/questions/6810999/how-to-determine-file-function-and-line-number
# 

import sys
import inspect

#--------------------------------------------------------------------------
# 
class dbmsg:
	def debug(message : str) -> None:
		""" print a debug message with file/function/line information """
		callerframerecord = inspect.stack()[1]
		frame = callerframerecord[0]
		info = inspect.getframeinfo(frame)
		# in a VS Code terminal, this will generate a clickable link
		# to enable jumping directly to the source location
		print(f"{info.filename}:{info.lineno} {message}")

