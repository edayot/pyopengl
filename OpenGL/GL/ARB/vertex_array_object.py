'''OpenGL extension ARB.vertex_array_object

This module customises the behaviour of the 
OpenGL.raw.GL.ARB.vertex_array_object to provide a more 
Python-friendly API
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions, wrapper
from OpenGL.GL import glget
import ctypes
from OpenGL.raw.GL.ARB.vertex_array_object import *
### END AUTOGENERATED SECTION