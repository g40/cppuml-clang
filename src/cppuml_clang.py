#!/usr/bin/python
#
#	BSD 3-Clause License
#
#   Copyright (c) 2022, Jerry Evans
#   All rights reserved.
#   See LICENCE.md for full details
#
#
# Credit for originally showcasing Python/libclang usage: 
#   https://github.com/gklingler/CodeDependencyVisualizer
# 
 

from distutils.log import debug
import sys
import os
from posixpath import dirname
import fnmatch
import re
import ccsyspath
import shutil
#import clang.cindex
from clang.cindex import Index, Config
from configparser import ConfigParser
from .constants import constants
from .umlgen import *
from .dbmsg import dbmsg

#------------------------------------------------------------------------------
class Application:
	""" The application shell """

	#--------------------------------------------------------------------------
	def __init__(self, argv):
		# bit o'hack :\\\
		self.args = self.parse_args(argv)
		if self.args == {}:
			return
		# where is clang?
		self.clang_path = self.args[constants.clangpath]
		self.clang_path = shutil.which(self.clang_path)
		# dbmsg.debug(f"clang: {self.clang_path}")
		if self.clang_path is None or os.path.exists(self.clang_path) == False:
			raise Exception(f"Cannot find clang {self.clang_path}")
		# and where is libclang
		self.libclangpath = self.args[constants.libclangpath]
		if not os.path.exists(self.libclangpath):
			raise Exception(f"Cannot find config file {self.libclangpath}")
		# set the path to libclang. this is important if we are using pyinst or similar
		Config.set_library_file(self.libclangpath)
		#
		self.exclusions = self.args[constants.exclusions].split(",")
		self.exclusions = [ s.strip() for s in self.exclusions ]
		# clear filter specs if we are ignoring them
		if self.args[constants.ignorefilters] == "true":
			self.args[constants.excludefilepath] = ""
			self.args[constants.excludefamespace] = ""
		# needs to be OS independent
		if os.sys.platform == "linux" or os.sys.platform == "linux2":
			self.clang_system_include_paths = [path.decode('utf-8') for path in ccsyspath.system_include_paths(self.clang_path)]
		elif os.sys.platform == "darwin":
			self.clang_system_include_paths = [path.decode('utf-8') for path in ccsyspath.system_include_paths(self.clang_path)]
		elif os.sys.platform == "win32":
			self.clang_system_include_paths = []
		#
		self.index = clang.cindex.Index.create()
		self.dotGenerator = DotGenerator()

	#--------------------------------------------------------------------------
	def _getFiles(self, rootDir, patterns, recursive = False) -> list:
		""" Searches for files in rootDir which file names mathes the given pattern. Returns
		a list of file paths of found files"""
		recursive = (self.args[constants.recursive] == "true")
		fqns = []
		if not recursive:  
			files = []
			for filename in os.listdir( rootDir ):
				files.append(filename)
			for p in patterns:
				for filename in fnmatch.filter(files, p):
					if filename not in self.exclusions:
						fqns.append(os.path.join(rootDir, filename))
	
		else:
			for rootDir, dirs, files in os.walk(rootDir):
				for p in patterns:
					for filename in fnmatch.filter(files, p):
						if filename not in self.exclusions:
							fqns.append(os.path.join(rootDir, filename))
		return fqns


	#--------------------------------------------------------------------------
	def _processClass(self, cursor, excludeNamespaces : list, excludeFilepaths : list):
		""" Processes an ast node that is a class. """
		# 
		generateHref = self.args[constants.generatehref] == "true"
		absDirectory = self.args[constants.directory]
		verbosity = int(self.args[constants.verbosity])
		umlClass = UmlClass(cursor, absDirectory, generateHref)  

		# JME should be an option.
		if umlClass.isUnamed() or umlClass.isAnonymous():
			return

		# exclude on the basis of a name(space)
		for ns in excludeNamespaces:
			if re.search(ns, umlClass.fqn) != None and verbosity > 2:
				dbmsg.debug(f"Skipping namespace: {ns} {umlClass.fqn}")
				return

		# exclude on the basis of a filepath
		abspath = os.path.abspath(umlClass.filename)
		# dbmsg.debug(f"{abspath} -> {excludeFilepaths}")
		for xp in excludeFilepaths:
			# if re.find(xp, abspath,constants.reOpts):
			if abspath.find(xp) != -1 and verbosity > 2:
				dbmsg.debug(f"Skipping include path: {abspath}")
				return

		# seen and parsed before? 
		if self.dotGenerator.hasClass(umlClass.fqn):
			return

		# process this class
		umlClass.Process(cursor)

		# map it.
		self.dotGenerator.addClass(umlClass)

	#--------------------------------------------------------------------------
	#
	def _traverseAst(self, cursor, excludeNamespaces, excludeFilepaths):
		""" recursively walk the clang AST """
		# dbmsg.debug(f"{cursor.kind} -> {cursor.displayname} {cursor.spelling}")
		# if cursor.kind == clang.cindex.CursorKind.NAMESPACE:
			# self.debug(f"{cursor.kind} -> {cursor.displayname} {cursor.spelling}")
			# dbmsg.debug(f"{os.path.abspath(cursor.location.file.name).strip()}:{cursor.location.line} {cursor.kind} -> {cursor.displayname} {cursor.spelling}")
		""" process if the current cursor is a class, class template or struct declaration """
		#if cursor.kind == clang.cindex.CursorKind(280):
		#    pass

		# work-around for https://github.com/sighingnow/libclang/issues/25
		try:
			if (cursor.kind == clang.cindex.CursorKind.CLASS_DECL
					or cursor.kind == clang.cindex.CursorKind.STRUCT_DECL
					or cursor.kind == clang.cindex.CursorKind.CLASS_TEMPLATE):
				self._processClass(cursor, excludeNamespaces, excludeFilepaths)
			for child_node in cursor.get_children():
				self._traverseAst(child_node, excludeNamespaces, excludeFilepaths)
		except Exception:
			pass

	#--------------------------------------------------------------------------
	#
	def _parseTranslationUnit(self, filePath : str, clangArgs : list, includeDirs : list, excludeNamespaces : list, excludeFilepaths : list):
		""" parse a single source file """
		includeDirs = includeDirs + self.clang_system_include_paths
		clangArgs += ['-I' + includeDir for includeDir in includeDirs]
		dbmsg.debug(f"{self.clang_path} {clangArgs} {filePath}")
		tu = self.index.parse(filePath, args=clangArgs, options=clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)
		for diagnostic in tu.diagnostics:
			dbmsg.debug(f"{diagnostic}")
		self._traverseAst(tu.cursor, excludeNamespaces, excludeFilepaths)


	#--------------------------------------------------------------------------
	#
	def run(self):
		""" run the application with command line args """

		# i.e help was requested ...
		if self.args == {}:
			return

		fileTypes = self.args[constants.filetypes].split(",")
		fileTypes = [ s.strip() for s in fileTypes ]
		filesToParse = self._getFiles(self.args[constants.directory], fileTypes)
		#
		if False:
			dbmsg.debug(f"Parsing {len(filesToParse)} file(s).")
		#
		if len(filesToParse) == 0:
			dbmsg.debug(f"No files matching {fileTypes} in {self.args[constants.directory]}")
			return
	
		sp = ""
		for csip in self.clang_system_include_paths:
			sp += f"{ os.path.abspath(csip)} "
		if len(sp) > 0:
			dbmsg.debug(f"Using clang system path: {sp}")

		# CSV string to lists ...
		includeDirs = self.args[constants.include].split(",")
		includeDirs = [ s.strip() for s in includeDirs ]
		excludeNamespace = self.args[constants.excludenamespace].split(",")
		excludeNamespace = [ s.strip() for s in excludeNamespace ]
		excludeFilepath = self.args[constants.excludefilepath].split(",")
		excludeFilepath = [ s.strip() for s in excludeFilepath ]
		if False:
			dbmsg.debug(f"-i: {includeDirs}")
			dbmsg.debug(f"-xn: {excludeNamespace}")
			dbmsg.debug(f"-xf: {excludeFilepath}")

		# gak. 
		clangArgs=['-x','c++']
		clangArgs += [ f"-std={self.args[constants.clangstandard].strip()}" ]
		clangDefines = [ f"-D{s.strip()}" for s in self.args[constants.clangdefines].split(',') ]
		clangArgs += clangDefines
		#
		dbmsg.debug(f"Queuing {filesToParse}")
		#
		for sourceFile in filesToParse:
			dbmsg.debug(f"Parsing {sourceFile}")
			self._parseTranslationUnit(sourceFile, clangArgs, includeDirs, excludeNamespace, excludeFilepath)
			#
			dotfileName = self.args[constants.outfile]
			sdirname = os.path.dirname(sourceFile)
			dotfileName=dotfileName.replace("$SRCDIR",sdirname)
			sbasename= os.path.basename(sourceFile)
			dotfileName=dotfileName.replace("$SRCNAME",sbasename)
			# i.e test.cpp.svg
			dbmsg.debug(f"Generating dotfile {dotfileName} : {self.dotGenerator.count()} class(es)")
			# create the folder if required 
			folder = dirname(dotfileName)
			if not os.path.exists(folder):
				os.makedirs(folder)
			# generate the DOT
			with open(dotfileName, 'w') as dotfile:
				dotfile.write(self.dotGenerator.generate(self.args[constants.generatenamespaces]))
			# generate the SVG
			ret = os.system(f"dot -Tsvg -O {dotfileName}")
			#
			dbmsg.debug(f"Generated {dotfileName}.svg")

	#--------------------------------------------------------------------------
	#
	def usage(self,iniName):
		usage = f"""	
	C++ -> UML generator

		optional arguments:
		-h  get help!
		-i specify which `path/to/project.ini` if required. overrides search in current directory
		-s overrides the `directory` setting in the `.ini` file

		default is {iniName}
		"""
		print(f"{usage}")

	#--------------------------------------------------------------------------
	# write out a skeleton .ini.
	def do_init(self,iniName:str) -> dict:
		# just going to do a copy
		import shutil
		# name gets created from folder
		# opName = f"{os.getcwd()}/{os.path.basename(os.getcwd())}.ini"
		# 'make' style
		opName = f"{os.getcwd()}/{constants.ininame}"
		# ensure consistent line endings
		content = constants.ini_content
		content = content.replace("\r\n","\n")
		content += "\n"
		#
		if True:
			with open(opName, "w") as a_file:
				a_file.write(content)
		else:
			shutil.copy(iniName, opName)
		dbmsg.debug(f"Initialized {iniName}")
		return {}
		
	#--------------------------------------------------------------------------
	#
	def parse_args(self,argv: list) -> dict:
		""" orignally an ultra simple argv parser """
		count = len(argv) - 1
		#
		iniName = f"{os.getcwd()}/{constants.ininame}"
		#
		help = ["-h", "--help", "-?"]
		if count == 1 and argv[1] in help:
			self.usage(iniName)
			# yakk
			return {}
		#
		source_directory = None
		init_root = None
		#
		index = 1
		while index <= count:
			switch = argv[index]
			# directory
			if switch == "-s":
				source_directory = argv[index+1]
			# path/to/ini
			if switch == "-i":
				iniName = argv[index+1]
			# initialize a top-level directory
			if switch == "--init":
				init_root = os.path.basename(os.getcwd())
			index+=1

		#
		if init_root:
			return self.do_init(iniName)

		# find the .ini file: start in working folder
		if not os.path.exists(iniName):
			# next look in .exe folder
			iniName = f"{os.getcwd()}/{constants.ininame}"
			if not os.path.exists(iniName):
				raise Exception(f"Cannot find config file {iniName}")
		#
		config = ConfigParser(allow_no_value=True)
		config.read(iniName)
		args = dict(config["common"])
		args.update(dict(config[sys.platform]))
		#
		if source_directory:
			args[constants.directory]=source_directory
		#
		if int(args[constants.verbosity]) >= 4:
			for k,v in args.items():
				print (f"{iniName} {k} -> {v}")
		#
		args[constants.directory] = os.path.abspath(args[constants.directory])
		if not os.path.exists(args[constants.directory]):
			raise Exception(f"{iniName} No directory {args[constants.directory]}")
		if not os.path.exists(args[constants.libclangpath]):
			raise Exception(f"{iniName} No libclang in {args[constants.libclangpath]}")			
		#
		self.iniName = iniName
		#
		return args
	
