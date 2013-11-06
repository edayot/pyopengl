import logging, os, urllib, traceback, textwrap
import xmlreg
log = logging.getLogger( __name__ )
AUTOGENERATION_SENTINEL = """### DO NOT EDIT above the line "END AUTOGENERATED SECTION" below!"""
AUTOGENERATION_SENTINEL_END = """### END AUTOGENERATED SECTION"""

def nameToPathMinusGL( name ):
    return "/".join( name.split( '_',2 )[1:] )
def indent( text, indent='\t' ):
    return "\n".join([
        '%s%s'%(indent,line) 
        for line in text.splitlines()
    ])

class Generator( object ):
    targetDirectory = os.path.join( '.','OpenGL')
    rawTargetDirectory = os.path.join( '.','OpenGL','raw')
    prefix = 'GL'
    dll = '_p.GL'
    includeOverviews = True
    
    def __init__( self, type_translator ):
        self.type_translator = type_translator
    def module( self, module ):
        gen = ModuleGenerator(module,self)
        gen.generate()
        return gen
    def enum( self, enum ):
        comment = ''
        try:
            value = int( enum.value, 0 )
        except ValueError as err:
            comment = '# '
        return '%s%s=_C(%r,%s)'%(comment, enum.name,enum.name,enum.value)
    def function( self, function ):
        """Produce a declaration for this function in ctypes format"""
        returnType = self.type_translator( function.returnType )
        if function.argTypes:
            argTypes = ','.join([self.type_translator(x) for x in function.argTypes])
        else:
            argTypes = ''
        if function.argNames:
            argNames = ','.join(function.argNames)
        else:
            argNames = ''
        arguments = ', '.join([
            '%s %s'%(t,n)
            for (t,n) in zip( function.argTypes,function.argNames )
        ])
        name = function.name 
        if returnType.strip() in ('_cs.GLvoid', '_cs.void','void'):
            returnType = pyReturn = 'None'
        else:
            pyReturn = function.returnType
        doc = '%(name)s(%(arguments)s) -> %(pyReturn)s'%locals()
#        log.info( '%s', doc )
        formatted=  self.FUNCTION_TEMPLATE%locals()
#        log.debug( '%s', formatted)
        return formatted
    FUNCTION_TEMPLATE = """@_f
@_p.types(%(returnType)s,%(argTypes)s)
def %(name)s(%(argNames)s):pass"""

class ModuleGenerator( object ):
    ROOT_EXTENSION_SOURCE = 'http://www.opengl.org/registry/specs/'
    RAW_MODULE_TEMPLATE = """'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, constants as _cs, arrays
from OpenGL.constant import Constant as _C
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = %(constantModule)r
def _f( function ):
    return _p.createFunction( function,%(dll)s,%(constantModule)r)
%(constants)s
%(declarations)s
"""

    WRAPPER_TEMPLATE_NO_FUNCTIONS = """'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p
from OpenGL.GL import glget
EXTENSION_NAME = %(constantModule)r
%(constants)s
"""
    WRAPPER_TEMPLATE_NOTHING = """'''Autogenerated by xml_generate script, do not edit!'''
EXTENSION_NAME = %(constantModule)r
"""

    INIT_TEMPLATE = """
def glInit%(camelModule)s%(owner)s():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( EXTENSION_NAME )
"""
    FINAL_MODULE_TEMPLATE = """'''OpenGL extension %(owner)s.%(module)s

This module customises the behaviour of the 
OpenGL.raw.%(prefix)s.%(owner)s.%(module)s to provide a more 
Python-friendly API

%(overview)sThe official definition of this extension is available here:
%(ROOT_EXTENSION_SOURCE)s%(owner)s/%(module)s.txt
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions, wrapper
from OpenGL.GL import glget
import ctypes
from OpenGL.raw.%(prefix)s.%(owner)s.%(module)s import *
"""
    dll = '_p.GL'
    def __init__( self, registry, overall ):
        self.registry = registry 
        self.overall = overall
        name = registry.name
        if hasattr( self.registry, 'api' ):
            self.prefix = self.registry.api.upper()
        else:
            self.prefix = name.split('_')[0]
        name = name.split('_',1)[1]
        try:
            self.owner, self.module = name.split('_',1)
            self.sentinelConstant = '%s_%s'%(self.owner,self.module)
            
        except ValueError:
            if name.endswith( 'SGIX' ):
                self.prefix = "GL"
                self.owner = 'SGIX'
                self.module = name[3:-4]
                self.sentinelConstant = '%s%s'%(self.module,self.owner)
            else:
                log.error( """Unable to parse module name: %s""", name )
                raise
        if self.module[0].isdigit():
            self.module = '%s_%s'%(self.prefix,self.module,)
        self.camelModule = "".join([x.title() for x in self.module.split('_')])
        self.rawModule = self.module
        
        self.rawOwner = self.owner
        while self.owner and self.owner[0].isdigit():
            self.owner = self.owner[1:]
        self.rawPathName = os.path.join( self.overall.rawTargetDirectory, self.prefix, self.owner, self.module+'.py' )
        self.pathName = os.path.join( self.overall.targetDirectory, self.prefix, self.owner, self.module+'.py' )
        
        self.constantModule = '%(prefix)s_%(owner)s_%(rawModule)s'%self
        specification = self.getSpecification()
        self.overview = ''
        if self.overall.includeOverviews:
            for title,section in specification.blocks( specification.source ):
                if title.startswith( 'Overview' ):
                    self.overview = 'Overview (from the spec)\n%s\n\n'%(
                        indent( section.replace('\xd4','O').replace('\xd5','O').decode( 'ascii', 'ignore' ).encode( 'ascii', 'ignore' ) )
                    )
                    break
    def __getitem__( self, key ):
        try:
            return getattr( self, key )
        except AttributeError as err:
            raise KeyError( key )
    def __getattr__( self, key ):
        if key not in ('registry',):
            return getattr( self.registry, key )
            
    def shouldReplace( self ):
        """Should we replace the given filename?"""
        filename = self.pathName
        if not os.path.isfile(
            filename
        ):
            return True
        else:
            hasLines = 0
            for line in open( filename ):
                if line.strip() == AUTOGENERATION_SENTINEL_END.strip():
                    return True
                hasLines = 1
            if not hasLines:
                return True
        return False
    
    def get_constants( self ):
        functions = []
        for req in self.registry:
            if req.require:
                for item in req:
                    if isinstance( item, xmlreg.Enum ):
                        functions.append( item )
        return functions
    
    @property
    def constants( self ):
        try:
            result = []
            for function in self.get_constants():
                result.append( self.overall.enum( function ) )
            return '\n'.join( result )
        except Exception as err:
            traceback.print_exc()
            raise
    @property
    def declarations( self ):
        functions = []
        for req in self.registry:
            if req.require:
                for item in req:
                    if isinstance( item, xmlreg.Command):
                        functions.append( item )
        result = []
        for function in functions:
            result.append( self.overall.function( function ) )
        return "\n".join( result )
    SPEC_EXCEPTIONS = {
        # different URLs... grr...
        '3DFX/multisample': 'http://oss.sgi.com/projects/ogl-sample/registry/3DFX/3dfx_multisample.txt',
        #'EXT/color_matrix': 'http://oss.sgi.com/projects/ogl-sample/registry/SGI/color_matrix.txt',
        #'EXT/texture_cube_map': 'http://oss.sgi.com/projects/ogl-sample/registry/ARB/texture_cube_map.txt',
        'SGIS/fog_function': 'http://oss.sgi.com/projects/ogl-sample/registry/SGIS/fog_func.txt',
    }
    def getSpecification( self ):
        """Retrieve our specification document...
        
        Retrieves the .txt file which defines this specification,
        allowing us to review the document locally in order to provide
        a reasonable wrapping of it...
        """
        return Specification('')
        if self.registry.feature:
            return Specification('')
        specFile = os.path.splitext( self.pathName )[0] + '.txt'
        specURLFragment = nameToPathMinusGL(self.name)
        if specURLFragment in self.SPEC_EXCEPTIONS:
            specURL = self.SPEC_EXCEPTIONS[ specURLFragment ]
        else:
            specURL = '%s/%s.txt'%( 
                self.ROOT_EXTENSION_SOURCE, 
                specURLFragment,
            )
        if not os.path.isfile( specFile ):
            try:
                data = download(specURL)
            except Exception, err:
                log.warn( """Failure downloading specification %s: %s""", specURL, err )
                data = ""
            else:
                try:
                    open(specFile,'w').write( data )
                except IOError, err:
                    pass
        else:
            data = open( specFile ).read()
        if 'Error 404' in data:
            log.info( """Spec 404: %s""", specURL)
            data = ''
        return Specification( data )
    
    def generate( self ):
        for target in (self.rawPathName,self.pathName):
            directory = os.path.dirname( target )
            if not os.path.exists( directory ):
                log.warn( 'Creating target directory: %s', directory )
                os.makedirs( directory )
            if not os.path.isfile( os.path.join(directory, '__init__.py')):
                open( os.path.join(directory, '__init__.py'),'w').write( 
                    '''"""OpenGL Extensions"""'''
                )
            
        directory = os.path.dirname(self.rawPathName)
        current = ''
        toWrite = self.RAW_MODULE_TEMPLATE % self
        try:
            current = open( self.rawPathName, 'r').read()
        except Exception, err:
            pass 
        if current.strip() != toWrite.strip():
            fh = open( self.rawPathName, 'w')
            fh.write( toWrite )
            fh.close()
        if self.shouldReplace( ):
            # now the final module with any included custom code...
            toWrite = self.FINAL_MODULE_TEMPLATE % self
            current = ''
            try:
                current = open( self.pathName, 'r').read()
            except Exception, err:
                pass 
            else:
                found = current.rfind( '\n'+AUTOGENERATION_SENTINEL_END )
                if found >= -1:
                    if current[:found].strip() == toWrite.strip():
                        # we aren't going to change anything...
                        return False
                    found += len( '\n' + AUTOGENERATION_SENTINEL_END )
                    current = current[found:]
                else:
                    current = ''
            try:
                fh = open( self.pathName, 'w')
            except IOError, err:
                log.warn( "Unable to create module for %r %s", self.name, err )
                return False
            else:
                fh.write( toWrite )
                fh.write( AUTOGENERATION_SENTINEL_END )
                fh.write( current )
                fh.close()
                return True
        return False

class Specification( object ):
    """Parser for parsing OpenGL specifications for interesting information
    
    """
    def __init__( self, source ):
        """Store the source text for the specification"""
        self.source = source
    def blocks( self, data ):
        """Retrieve the set of all blocks"""
        data = data.splitlines()
        title = []
        block = []
        for line in data:
            if line and line.lstrip() == line:
                if block:
                    yield "\n".join(title), textwrap.dedent( "\n".join(block) )
                    title = [ ]
                    block = [ ]
                title.append( line )
            else:
                block.append( line )
        if block:
            yield "\n".join(title), textwrap.dedent( "\n".join(block) )
    def constantBlocks( self ):
        """Retrieve the set of constant blocks"""
        for title,block in self.blocks( self.source ):
            if title and title.startswith( 'New Tokens' ):
                yield block
    def glGetConstants( self ):
        """Retrieve the set of constants which pass to glGet* functions"""
        table = {}
        for block in self.constantBlocks():
            for title, section in self.blocks( block ):
                for possible in (
                    'GetBooleanv','GetIntegerv','<pname> of Get'
                ):
                    if possible in title:
                        for line in section.splitlines():
                            line = line.strip().split()
                            if len(line) == 2:
                                constant,value = line 
                                table['GL_%s'%(constant,)] = value 
                        break
        return table

def download( url ):
    """Download the given url, informing the user of what we're doing"""
    log.info( 'Download: %r',url,)
    file = urllib.urlopen( url )
    return file.read()
