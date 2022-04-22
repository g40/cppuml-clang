#
# entry point for the application (main)
# 
#

import os
import sys
import traceback
from src.dbmsg import dbmsg
from src.cppuml_clang import Application

#------------------------------------------------------------------------------
if __name__ == "__main__":
	# return code
	ret = 0
	try:
		#
		# dbmsg.debug(f"{sys.executable} {os.getcwd()} => {sys.argv[0]} ")
		#
		app = Application(sys.argv)
		#
		app.run()

	except Exception:
		# just GTF out of Dodge
		traceback.print_exc(file=sys.stdout)
		#
		ret = -1
	# exit
	sys.exit(ret)        
