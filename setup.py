# Dependencies are automatically detected, but it might need
# fine tuning.
#build_options = {'packages': ['src'], 'excludes': []}

#if True:
if False:

	from distutils.core import setup
	import py2exe
	import src.umlgen.py
	import src.dbmsg.py
	import src.constants.py

	setup(
		console=['src/main.py'],
		data_files="cppuml.ini",
	)

else:
	from cx_Freeze import setup, Executable

	build_options = {
		"include_files" : ["cppuml.ini"],
		# "packages" : [ "src/umlgen.py","src/constants.py"],
		# "includes": ["src/umlgen.py","./src/constants.py","./src/dbmsg.py"] 
	}
	base = 'Console'

	executables = [
		Executable('main.py', base=base, target_name = 'cppuml',)
	]

	setup(name='cppuml-clang',
		version = '1.0',
		description = 'Industrial quality c++ UML generation using clang',
		options = {'build_exe': build_options},
		executables = executables)
