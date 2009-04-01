'''OpenGL extension EXT.blend_func_separate

Overview (from the spec)
	
	Blending capability is extended by defining a function that allows
	independent setting of the RGB and alpha blend factors for blend
	operations that require source and destination blend factors.  It
	is not always desired that the blending used for RGB is also applied
	to alpha.

The official definition of this extension is available here:
	http://oss.sgi.com/projects/ogl-sample/registry/EXT/blend_func_separate.txt

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_EXT_blend_func_separate'
GL_BLEND_DST_RGB_EXT = constant.Constant( 'GL_BLEND_DST_RGB_EXT', 0x80C8 )
glget.addGLGetConstant( GL_BLEND_DST_RGB_EXT, (1,) )
GL_BLEND_SRC_RGB_EXT = constant.Constant( 'GL_BLEND_SRC_RGB_EXT', 0x80C9 )
glget.addGLGetConstant( GL_BLEND_SRC_RGB_EXT, (1,) )
GL_BLEND_DST_ALPHA_EXT = constant.Constant( 'GL_BLEND_DST_ALPHA_EXT', 0x80CA )
glget.addGLGetConstant( GL_BLEND_DST_ALPHA_EXT, (1,) )
GL_BLEND_SRC_ALPHA_EXT = constant.Constant( 'GL_BLEND_SRC_ALPHA_EXT', 0x80CB )
glget.addGLGetConstant( GL_BLEND_SRC_ALPHA_EXT, (1,) )
glBlendFuncSeparateEXT = platform.createExtensionFunction( 
	'glBlendFuncSeparateEXT', dll=platform.GL,
	extension=EXTENSION_NAME,
	resultType=None, 
	argTypes=(constants.GLenum, constants.GLenum, constants.GLenum, constants.GLenum,),
	doc = 'glBlendFuncSeparateEXT( GLenum(sfactorRGB), GLenum(dfactorRGB), GLenum(sfactorAlpha), GLenum(dfactorAlpha) ) -> None',
	argNames = ('sfactorRGB', 'dfactorRGB', 'sfactorAlpha', 'dfactorAlpha',),
)


def glInitBlendFuncSeparateEXT():
	'''Return boolean indicating whether this extension is available'''
	return extensions.hasGLExtension( EXTENSION_NAME )