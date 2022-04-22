#
#	BSD 3-Clause License
#
#   Copyright (c) 2022, Jerry Evans
#   All rights reserved.
#   See LICENCE.md for full details
#
#------------------------------------------------------------------------------
class constants:

	#--------------------------------------------------------------------------
	# keep all strings etc in one place
	directory = "directory"
	filetypes = 'filetypes'
	include = 'include'
	outfile = 'outfile'
	recursive = 'recursive'
	verbosity = 'verbosity'
	ignorefilters = 'ignorefilters'
	clangpath = 'clangpath'
	clangstandard = 'clangstandard'
	clangdefines = 'clangdefines'
	generatehref = 'generatehref'
	generatenamespaces = 'generatenamespaces'
	excludefilepath = 'excludefilepath'
	excludenamespace = 'excludenamespace'
	exclusions = 'exclusions'
	libclangpath = "libclangpath"
	# name of the ini file
	ininame='cppuml.ini'

	#--------------------------------------------------------------------------
	# yakk. horrible.
	ini_content = """
	;
	; boilerplate configuration file for c++ => UML generation
	;

	[common]
	; default directory to scan, aka root!
	directory=.
	; recursively search directories
	recursive=false
	; types of files to search
	filetypes=*.cpp,
	; exclude specific files ...
	exclusions=
	; how much tracking info?
	verbosity=1
	; macroised output file location. 
	; cppuml will create the directory if required
	outfile=$SRCDIR/uml/$SRCNAME.dot
	; add named boxed in UML
	generatenamespaces=true
	; filter out any classes in thse C++ namespaces (CSV list)
	excludenamespace=std
	; this is a quick override for all filters. 
	ignorefilters=false
	; add links into UML records
	generatehref=true

	; all windows specific stuff hee
	[win32]
	; can be absolute or relative to root directory
	include=r:/src/include,.,./test/inc,r:/src/audio/libaiff
	excludefilepath=vs2022,vs2019,vs2017,vs2012,Windows Kits
	clangstandard=c++17
	clangdefines=_IS_WINDOWS,_MBCS
	clangpath = clang-cl.exe
	libclangpath = r:/apps/python3/Lib/site-packages/clang/native/libclang.dll

	; all linux specific stuff
	[linux]
	include=../include,./test/inc
	excludenamespace=std
	excludefilepath=/usr/include,/usr/lib
	clangstandard=c++17
	clangdefines=_IS_LINUX
	clangpath = /usr/bin/clang++
	# is this indeed the correct .so?
	libclangpath = /usr/lib/x86_64-linux-gnu/libclang-10.so

	[darwin]
	; N.B. untested as my Mac is in storage!
	include=../include,./test/inc
	excludenamespace=std
	excludefilepath=/usr/include,/usr/lib
	clangstandard=c++17
	clangdefines=_IS_OSX
	clangpath = /usr/bin/clang++
	libclangpath =
	"""