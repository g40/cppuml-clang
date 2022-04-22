#
#
#
# is Windows_NT on XP, 2000, 7, Vista, 10...
ifeq ($(OS),Windows_NT)     
    detected_OS := Windows
else
	# same as "uname -s"
    detected_OS := $(shell uname)  
endif

APPNAME=cppuml
PACKAGENAME=bdist_rpm

ifeq ($(detected_OS),Windows)
	APPNAME=cppuml.exe
    PACKAGENAME=bdist_msi
else
	ifeq ($(detected_OS),Darwin)
    	PACKAGENAME=bdist_dmg
	endif
endif

all: help 
# 	@echo "$(detected_OS) -> $(PACKAGENAME)"
	
help:
	@echo "make run: run the example script"
	@echo "make binary: build an executable for your OS"
	@echo "make installer: build a distribution package for your OS"
	@echo "make clean: clean any junk. achtung baby."

run:
	python main.py

clean:
	rm -rf ./build ./dist ./__pycache__
# 	caution here as there is a wildcard.
	rm *.spec *.ini

# make
binary:
	pyinstaller --onefile -n$(APPNAME) main.py 

#---------unused for2 reference only ----------------------
# exe:
#	python setup.py build

# installer:
#	python setup.py $(PACKAGENAME)

# think this is not quite as good?
# pyinst:
#	pyinstaller --onefile -n$(APPNAME) main.py 
#	example to show how to add text resources. not so useful.
#	pyinstaller --onefile -n$(APPNAME) --add-data "./cppuml.ini;." main.py 
