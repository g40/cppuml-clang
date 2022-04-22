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
 

import os
import re
import html
import clang.cindex
from .dbmsg import dbmsg

#------------------------------------------------------------------------------
class UmlClass:

	def __init__(self,cursor : clang.cindex.Cursor, absDirectory: str ,generate_href : bool = True):
		""" Create a UmlClass instance with clang cursor and source directory"""
		self.generate_href = generate_href
		self.ropen = "\n<tr><td>\n"
		self.rclose = "\n</td></tr>\n"
		# where are we at?
		self.filename = os.path.abspath(cursor.location.file.name).strip()
		# store a relative path for hrefs as well
		# dbmsg.debug(f"{self.filename},{absDirectory}")
		# JME fixme. fubar on Windows with different drive names :\\\\
		# self.relname = os.path.relpath(self.filename,absDirectory).strip()
		self.relname = ""
		self.line = cursor.location.line
		# the fully qualified name as in a::b::c
		self.fqn = None
		if cursor.kind == clang.cindex.CursorKind.CLASS_TEMPLATE:
			# process declarations like:
			# template <typename T> class MyClass
			self.fqn = cursor.spelling
		else:
			# process declarations like:
			# class MyClass or struct MyStruct
			self.fqn = cursor.type.spelling
		# 
		self.parents = []
		self.privateFields = []
		self.privateMethods = []
		self.publicFields = []
		self.publicMethods = []
		self.protectedFields = []
		self.protectedMethods = []

	#--------------------------------------------------------------------------
	def _genFields(self, accessPrefix, fields) -> str:
		""" generate UML HTML string for all class member variables"""
		# sort by fieldName
		#fields = sorted(fields, key=lambda x: x[0])
		ret = ""
		if len(fields) > 0:
			ret = self.ropen
			for fieldName, fieldTypes in fields:
				ret += f"{accessPrefix} {html.escape(fieldName)} : {html.escape(fieldTypes[0])} <br />"
			ret += self.rclose
		return ret

	#--------------------------------------------------------------------------
	def _genMethods(self, accessPrefix, methods) -> str:
		""" generate UML HTML string for all class member functions"""
		# sort by methodName
		offset = 1
		# methods = sorted(methods, key=lambda x: x[offset])
		ret = ""
		if len(methods) > 0:
			ret = self.ropen
			for (static, virtual, returnType, methodName, methodArgs) in methods:
				ret += f"{accessPrefix} {static} {virtual} {html.escape(methodName)}{html.escape(methodArgs)} : {html.escape(returnType)} <br />"
			ret += self.rclose
		return ret

	#--------------------------------------------------------------------------
	def addParentByFQN(self, fullyQualifiedClassName):
		""" add fully qualified with namespaces etc """
		self.parents.append(fullyQualifiedClassName)

	#--------------------------------------------------------------------------
	def getId(self) -> str:
		""" generate a unique label for graphviz """
		# sad but required to avoid problems with graphviz IDs
		return self.getFQN().replace("::","__")

	#--------------------------------------------------------------------------
	def getFQN(self) -> str:
		""" get the fully qualified classname"""
		return self.fqn

	#--------------------------------------------------------------------------
	def getUQN(self) -> str:
		""" get the unqualified classname"""
		parts = str.split(self.getId(),"__")
		return parts[-1]

	#--------------------------------------------------------------------------
	def getNamespace(self) -> str:
		""" get the fully namespace as a string"""
		ns = ""
		parts:list[str] = str.split(self.getId(),"__")
		if len(parts) > 0:
			ns = "__".join(parts[:-1])
		return ns

	#--------------------------------------------------------------------------
	def getInnerNamespace(self) -> str:
		""" get the innermost namespace as a string"""
		ns = ""
		parts = str.split(self.getId(),"__")
		if len(parts) > 1:
			ns = parts[-2]
			# dbmsg.debug(f"{self.getId()} -> {ns}")
		return ns

	#--------------------------------------------------------------------------
	def getNamespaceDepth(self) -> int:
		""" how deep is the namespace nesting. global == 0 """
		depth = 0
		parts = str.split(self.getId(),"__")
		if len(parts) > 0:
			depth = len(parts) - 1
		return depth

	#--------------------------------------------------------------------------
	def getLocation(self) -> str:
		""" where are we defined in a source file? """
		return str(f"{self.filename}:{self.line}\n")

	#--------------------------------------------------------------------------
	def isUnamed(self) -> bool:
		""" dump unamed structs  """
		ret = "(unnamed struct" in self.fqn
		return ret

	#--------------------------------------------------------------------------
	def isAnonymous(self) -> bool:
		""" dump anonymous structs  """
		ret = "(anonymous struct" in self.fqn
		# if ret:
		#    dbmsg.debug(f"anon: -> {self.fqn}")
		return ret

	#--------------------------------------------------------------------------
	def _genAssociations(self,fields,classes) -> dict:
		""" generate DOT association strings """
		# ach!
		astr:str = "[constraint=false, arrowtail=odiamond]\n"
		mstr:str = "[constraint=false, arrowtail=diamond]\n"
		edges = dict()
		for fieldName, fieldTypes in fields:
			for fieldType in fieldTypes:
				if fieldType in classes:
					c = classes[fieldType]
					# check for multiple association(s)
					key = c.getId() 
					if key in edges:
						edges[key] = f"{key} -> {self.getId()} {mstr}"
					else:
						edges[key] = f"{key} -> {self.getId()} {astr}"
		return edges

	#--------------------------------------------------------------------------
	def genAssociations(self, classes) -> str:
		associations:str = ""
		edges = self._genAssociations(self.privateFields,classes)
		for k,v in edges.items():
			associations += v
		edges = self._genAssociations(self.publicFields,classes)
		for k,v in edges.items():
			associations += v
		return associations

	#--------------------------------------------------------------------------
	def genInheritances(self, classes, iStyle : str = "") -> str:
		""" generate edge labels from aClass to 1+ superclass(es) """
		edges = ""
		for parent in self.parents:
			if parent in classes:
				c = classes[parent]
				edges += f"{c.getId()} -> {self.getId()}\n"
		return edges

	#--------------------------------------------------------------------------
	def GenerateDot(self) -> str:
		""" generate a DOT HTML label for this instance """
		ret = f"{self.getId()}[ label = <<table border=\"0\" rows=\"*\">"
		# ret = f"{self.getId()}[ label = <<table border=\"0\">"
		ret += f"{self.ropen}{html.escape(self.getUQN())}{self.rclose}"
		# host-dependent. improve.
		if self.generate_href:
			# ugly but provides navigation to the target file
			ret += f"\n<tr><td href=\"file:///{self.filename}\">\n{self.filename}:{self.line}{self.rclose}"
			# 
		else:
			# make these file local
			# ret += f"{self.ropen}{self.filename}:{self.line}{self.rclose}"
			pass
		ret += f"{self._genFields('+',self.publicFields)}"
		ret += f"{self._genMethods('+',self.publicMethods)}"
		ret += f"{self._genFields('#',self.protectedFields)}"
		ret += f"{self._genMethods('#',self.protectedMethods)}"
		ret += f"{self._genFields('-',self.privateFields)}"
		ret += f"{self._genMethods('-',self.privateMethods)}"
		ret += "</table>> ]\n"
		return ret

	#--------------------------------------------------------------------------
	def _processClassField(self,cursor):
		""" Returns the name and the type of the given class field.
		The cursor must be of kind CursorKind.FIELD_DECL"""
		# the first element of types is for display purpose. Form 2nd to Nth element, 
		# they are template type argurment in the chain list
		types = list()
		fieldChilds = list(cursor.get_children())
		if len(fieldChilds) == 0:  # if there are not cursorchildren, the type is some primitive datatype
			types.append(cursor.type.spelling)
		else:  # if there are cursorchildren, the type is some non-primitive datatype (a class or class template)
			types.append(cursor.type.spelling)
			for cc in fieldChilds:
				if cc.kind == clang.cindex.CursorKind.TEMPLATE_REF:
					types.append(cc.spelling)
				elif cc.kind == clang.cindex.CursorKind.TYPE_REF:
					types.append(cc.type.spelling)
		name = cursor.spelling
		return name, types


	#------------------------------------------------------------------------------
	def _processClassMemberDeclaration(self, cursor):
		""" Processes a cursor corresponding to a class member declaration and
		appends the extracted information to the given umlClass """
		s = "static" if cursor.is_static_method() else ""
		v = "virtual" if cursor.is_virtual_method() else ""
		if cursor.kind == clang.cindex.CursorKind.CXX_BASE_SPECIFIER:
			for baseClass in cursor.get_children():
				if baseClass.kind == clang.cindex.CursorKind.TEMPLATE_REF:
					self.parents.append(baseClass.spelling)
				elif baseClass.kind == clang.cindex.CursorKind.TYPE_REF:
					self.parents.append(baseClass.type.spelling)
		# non static data member
		elif cursor.kind == clang.cindex.CursorKind.FIELD_DECL:
			name, types = self._processClassField(cursor)
			if name is not None and types is not None:
				if cursor.access_specifier == clang.cindex.AccessSpecifier.PUBLIC:
					self.publicFields.append((name, types))
				elif cursor.access_specifier == clang.cindex.AccessSpecifier.PRIVATE:
					self.privateFields.append((name, types))
				elif cursor.access_specifier == clang.cindex.AccessSpecifier.PROTECTED:
					self.protectedFields.append((name, types))
		elif cursor.kind == clang.cindex.CursorKind.CXX_METHOD or\
				cursor.kind == clang.cindex.CursorKind.CONSTRUCTOR or\
				cursor.kind == clang.cindex.CursorKind.DESTRUCTOR:
			try:
				returnType, argumentTypes = cursor.type.spelling.split(' ', 1)
				# s = "static" if cursor.is_static_method() else ""
				# v = "virtual" if cursor.is_virtual_method() else ""
				if cursor.access_specifier == clang.cindex.AccessSpecifier.PUBLIC:
					self.publicMethods.append((s,v,returnType, cursor.spelling, argumentTypes))
				elif cursor.access_specifier == clang.cindex.AccessSpecifier.PRIVATE:
					self.privateMethods.append((s,v,returnType, cursor.spelling, argumentTypes))
				elif cursor.access_specifier == clang.cindex.AccessSpecifier.PROTECTED:
					self.protectedMethods.append((s,v,returnType, cursor.spelling, argumentTypes))
			except:
				dbmsg.debug("Error Invalid declaration: {cursor.type.spelling}")
		elif cursor.kind == clang.cindex.CursorKind.FUNCTION_TEMPLATE:
			# s = "static" if cursor.is_static_method() else ""
			# v = "virtual" if cursor.is_virtual_method() else ""
			returnType, argumentTypes = cursor.type.spelling.split(' ', 1)
			if cursor.access_specifier == clang.cindex.AccessSpecifier.PUBLIC:
				self.publicMethods.append((s,v,returnType, cursor.spelling, argumentTypes))
			elif cursor.access_specifier == clang.cindex.AccessSpecifier.PRIVATE:
				self.privateMethods.append((s,v,returnType, cursor.spelling, argumentTypes))
			elif cursor.access_specifier == clang.cindex.AccessSpecifier.PROTECTED:
				self.protectedMethods.append((s,v,returnType, cursor.spelling, argumentTypes))

	#--------------------------------------------------------------------------
	def Process(self,cursor):
		""" process this class """
		# print(cursor.kind)
		for c in cursor.get_children():
			# print(c.kind)
			# process member variables and methods declarations
			self._processClassMemberDeclaration(c)

#------------------------------------------------------------------------------
class DotGenerator:
	""" Generate a DOT script """

	#--------------------------------------------------------------------------
	def __init__(self):
		""" constructor """
		self.classes = {}

	#--------------------------------------------------------------------------
	def hasClass(self, aClass) -> bool:
		""" check to see if a fully qualified classname has been mapped"""
		return self.classes.get(aClass) is not None

	#--------------------------------------------------------------------------
	#
	def addClass(self, aClass) -> None:
		""" map fully qualified classname to class descriptor instance """
		self.classes[aClass.fqn] = aClass

	#--------------------------------------------------------------------------
	# 
	def count(self) -> int:
		""" how many classes? """
		return len(self.classes)

	#--------------------------------------------------------------------------
	def genNamespaces(self) -> str:
		""" generate 0+ DOT subgraph definitions labelled by namespace. """
		# clang does not provide a clean namespace entry/exit token
		# it has to be inferred from the fully qualifed name, which is :: delimited
		# we want to generate final set of DOT strings that do something like this:
		# subgraph cluster_1 { label="A" test__A, test__B, test__C, test__D
		# subgraph cluster_2 { label="E" test__E } }
		# which clusters all of the classes parsed in the TU.
		# so what we want is a dictionary where the key is the namespace and the value
		# is a list of class names within it
		# 'global' -> [ 'g1', 'g2', ...]
		#  no, forget global. always implicit thus:
		# 'ns' -> [ 'g3', 'g4', ...]
		# 'ns::ns2' -> [ 'g4', 'g5', ...]
		#
		nameSpaces = ""
		curdepth = 0
		cluster = 0
		depth = 0
		ns = ""
		for key, umlClass in self.classes.items():
			# track the current values
			curns = umlClass.getNamespace()
			if curns == "":
				continue
			curdepth = umlClass.getNamespaceDepth()
			# dbmsg.debug(f"{ns} {curns} {ns == curns} : {depth} {curdepth}")
			# potentially depth changes might be > 1 so we need to 
			# account for these eventualities. 
			if  curdepth > depth:
				nsdepth = curdepth
				braces = ""
				while nsdepth > depth:
					braces += "{"
					nsdepth -= 1
				nameSpaces += f"\nsubgraph cluster_{cluster} {braces} label=\"{umlClass.getInnerNamespace()}\" {umlClass.getId()} "
				cluster += 1
			elif curdepth < depth:
				nsdepth = curdepth
				braces = ""
				while nsdepth < depth:
					braces += "}"
					nsdepth += 1
				nameSpaces += f" {braces}\n"
			elif curns != ns and curdepth == depth:
				nameSpaces += f"}}\nsubgraph cluster_{cluster} {{ label=\"{umlClass.getInnerNamespace()}\" {umlClass.getId()} "
				cluster += 1
			elif curdepth > 0:
				nameSpaces += f"{umlClass.getId()} "
			# stash ...
			ns = curns
			depth = curdepth
		while curdepth > 0:
			curdepth -= 1
			nameSpaces += "}\n"
		return nameSpaces

	#--------------------------------------------------------------------------
	# 
	def generate(self,generateNamespaces) -> str:
		""" generate the DOT file content """
		# fully qualified classname (std::string) -> UmlClass instance
		classes = ""
		for key, value in self.classes.items():
			classes += value.GenerateDot()
		# associations
		associations = ""
		for key, aClass in self.classes.items():
			associations += aClass.genAssociations(self.classes)
		# inheritances
		inheritances = ""
		for key, aClass in self.classes.items():
			inheritances += aClass.genInheritances(self.classes)
		# These get modelled as DOT (nested) subgraphs
		# GOK how to style them so we do not! Any examples welcomed.
		# subgraph cluster_A { label="A" test__A, test__B, test__C, test__D
		# subgraph cluster_E { label="E" test__E } }
		namespaces = ""
		if generateNamespaces:
			namespaces = self.genNamespaces()

		# JME needs to be an option somehow
		dotContent = f"""
					// Paste into https://graphviz.christine.website/ to experiment. great stuff.
					digraph UML {{
						node [fontname = \"Helvetica,Arial,sans-serif\" margin=0 fontcolor=black fontsize=8 width=0.5 shape=box style=filled]
						edge [fontname = \"Helvetica,Arial,sans-serif\" fontsize = 8 dir=back, arrowtail=empty]
						// classes
						{classes}
						// has-a (uses/ownership/association)
						{associations}
						// is-a (inheritance)
						{inheritances}
						// subgraphs for namespaces
						{ namespaces }
						//
						}} // EOF\n
						"""
		# clear out rubbish from triple quote strings
		dotContent = re.sub(r'(^[ \t]+|[ \t]+(?=:))', '', dotContent, flags=re.M)
		return dotContent
