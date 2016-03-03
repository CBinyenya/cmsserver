import sys
from cx_Freeze import setup, Executable
# Dependencies are automatically detected, but it might need fine tuning.
base = None
if sys.platform == "win32":
    base = "Win32GUI"
includefiles = []
options = {
   'build_exe': {
        'includes': ['whichdb','wx'],
        "include_files":includefiles
    }
}

setup( name = "SMSLite Server",
    version = "1.3",
    description = "SMSLite Server Application 2.0",
    options = options,
    executables = [Executable("runserver.py", base=base)])
    
