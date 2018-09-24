## Shader and render code adapted from 3ds_viewer.py provided by PyAssimp
## Texture shader and reader written by Jared Rodriguez
# I think I know what all of this does now.

import sys

import logging
logger = logging.getLogger("pyassimp")
gllogger = logging.getLogger("OpenGL")
gllogger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

import OpenGL
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False
#OpenGL.ERROR_ON_COPY = True
#OpenGL.FULL_LOGGING = True
from OpenGL.GL import *
from OpenGL.error import GLError
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
import shaderLoader

import math, random, numpy, pygame

import pyassimp
from pyassimp.postprocess import *
from pyassimp.helper import *
    
class GLModel(object):
    shaders = {}
    def __init__(self, main,**kwargs):
        self.fileMain = main
        self.fileReplace = kwargs.get("replace", None)
        self.image = kwargs.get("image", None)
        self.rawSurface = kwargs.get("rawSurface", None)
        self.postprocess = kwargs.get("postprocess", aiProcessPreset_TargetRealtime_MaxQuality)
        if not GLModel.shaders:
            self.setNormalShaders()
        self.phongWeight = kwargs.get("phong", 0)
        self.model = None
        if kwargs.get("load", True):
            self.loadModel()
            
    def loadModel(self):
        # Separates model data from loaded file and processed into a usable format
        if self.model:
            logger.info(self.fileMain + " is already loaded.")
            return
            
        logger.info("Loading model:" + self.fileMain + "...")
        model = None
        
        if self.postprocess:
            model = pyassimp.load(self.fileMain, self.postprocess)
        else:
            model = pyassimp.load(self.fileMain)
            
        if self.fileReplace:
            aux = pyassimp.load(self.fileReplace)
            for i in range(len(model.meshes)):
                replaced = model.meshes[i].bones
                model.meshes[i].bones = aux.meshes[i].bones.copy() # replaces the bones with those from the secondary file
                del replaced
            pyassimp.release(aux)
        logger.info("Done.")
    
        scene = model
            
        for index, mesh in enumerate(scene.meshes):
            self.prepare_gl_buffers(mesh)
    
        # Finally release the model
        pyassimp.release(scene)
        
        self.model = model
    
    def prepare_gl_buffers(self, mesh):

        mesh.gl = {}
        
        texFound = False
        for k, v in mesh.material.properties.items():
            if k == 'file':
                texFound = v
                break
                
        if texFound:
            surface = None
            try:
                if self.rawSurface:
                    surface = self.rawSurface
                elif self.image == None:                
                    surface = pygame.image.load("Textures/"+texFound).convert_alpha()
                else:
                    surface = pygame.image.load("Textures/"+self.image).convert_alpha()
            except:
                logger.warning("texture "+texFound+" produced error on load")
                surface = pygame.image.load("Textures/missing.png").convert_alpha()
                
            x, y = surface.get_rect().size
            image = pygame.image.tostring(surface, 'RGBA', 1)            
            texBuffer = mesh.gl["texture"] = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texBuffer)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                GL_NEAREST)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, x, y, 0, GL_RGBA,
                GL_UNSIGNED_BYTE, image)
            glBindTexture(GL_TEXTURE_2D, 0)

            v = numpy.array(mesh.vertices, 'f')
            n = numpy.array(mesh.normals, 'f')
            
            if 1 not in mesh.texturecoords.shape or mesh.texturecoords[0][0][2] != 0:
                logger.warning("Critical error: texcoords format has entered apocalypse mode!")
            t = numpy.squeeze(numpy.array(mesh.texturecoords, 'f'))

            mesh.gl["vbo"] = vbo.VBO(numpy.hstack((v,n,t)))
        else:
            mesh.gl["texture"] = None
            v = numpy.array(mesh.vertices, 'f')
            n = numpy.array(mesh.normals, 'f')
    
            mesh.gl["vbo"] = vbo.VBO(numpy.hstack((v,n)))
            
        mesh.gl["faces"] = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.gl["faces"])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 
                    mesh.faces,
                    GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,0)
        
    def render(self, **kwargs):
        wireframe = kwargs.get('wireframe', False)
        twosided = kwargs.get('twosided', False)
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)
        glDisable(GL_CULL_FACE) if twosided else glEnable(GL_CULL_FACE)
        
        # I don't know why this doesn't work as intended
        colorShader = GLModel.shaders["color"]
        texShader = GLModel.shaders["tex"]
        glUseProgram(colorShader)
        glUniform4f( colorShader.Global_ambient, .1,.1,.1,.1 )
        glUniform4f( colorShader.Light_ambient, .5,.5,.5, 1.0 )
        glUniform4f( colorShader.Light_diffuse, 1,1,1,1 )
        glUniform3f( colorShader.Light_location, 10, 10, 10)
        glUseProgram(texShader)
        glUniform1f( texShader.saturation, kwargs.get("saturation", 1) )

        self.recursive_render(self.model.rootnode, kwargs)
        glUseProgram( 0 )

    def recursive_render(self, node, kwargs):
        # Main recursive rendering method.

        # save model matrix and apply node transformation
        glPushMatrix()
        m = node.transformation.transpose() # OpenGL row major
        glMultMatrixf(m)

        for mesh in node.meshes:
            
            if mesh.gl["texture"]:
                stride = 36 # 9 * 4 bytes
                shader = GLModel.shaders["tex"]
                glUseProgram(shader)
                
                glBindTexture(GL_TEXTURE_2D, mesh.gl["texture"])
                
                glEnableVertexAttribArray( shader.Vertex_position )
                glEnableVertexAttribArray( shader.Vertex_texcoords )

                vbo = mesh.gl["vbo"]
                vbo.bind()

                glVertexAttribPointer(
                    shader.Vertex_position,
                    3, GL_FLOAT,False, stride, vbo
                )       
                glVertexAttribPointer(
                    shader.Vertex_texcoords,
                    3, GL_FLOAT,False, stride, vbo+24
                )

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.gl["faces"])
                
                glDrawElements(GL_TRIANGLES, len(mesh.faces) * 3, GL_UNSIGNED_INT, None)
    
                vbo.unbind()
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
                glDisableVertexAttribArray( shader.Vertex_position )
                glDisableVertexAttribArray( shader.Vertex_texcoords )
                glBindTexture(GL_TEXTURE_2D, 0)
            else:
                stride = 24 # 6 * 4 bytes
                shader = GLModel.shaders["color"]
                glUseProgram(shader)

                diffuse = mesh.material.properties["diffuse"]
                if len(diffuse) == 3: diffuse.append(1.0)
                glUniform4f( shader.Material_diffuse, *diffuse )                 
                ambient = mesh.material.properties["ambient"]
                if len(ambient) == 3: ambient.append(1.0)
                glUniform4f( shader.Material_ambient, *ambient ) 
                
                glEnableVertexAttribArray( shader.Vertex_position )
                glEnableVertexAttribArray( shader.Vertex_normal )

                vbo = mesh.gl["vbo"]
                vbo.bind()

                glVertexAttribPointer(
                    shader.Vertex_position,
                    3, GL_FLOAT,False, stride, vbo
                )
                glVertexAttribPointer(
                    shader.Vertex_normal,
                    3, GL_FLOAT,False, stride, vbo+12
                )

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.gl["faces"])
                
                glDrawElements(GL_TRIANGLES, len(mesh.faces) * 3, GL_UNSIGNED_INT, None)
    
                vbo.unbind()
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
                glDisableVertexAttribArray( shader.Vertex_position )
                glDisableVertexAttribArray( shader.Vertex_normal )
                glBindTexture(GL_TEXTURE_2D, 0)

        for child in node.children:
            self.recursive_render(child, kwargs)

        glPopMatrix()
        
    def unload(self):
        self.recursiveUnload(self.model.rootnode)
        
    def recursiveUnload(self, node):
        for child in node.children:
            self.recursiveUnload(child)
            
        for mesh in node.meshes:
            try:
                if mesh.gl.get("texture", None):
                    glDeleteTextures(mesh.gl["texture"])
                    mesh.gl.discard("texture")
                glDeleteBuffers(1, mesh.gl["faces"])
            except: # This is REALLY bad but it's only called so the ineffective error doesn't show up
                pass
        
    @staticmethod
    def setNormalShaders():

        phong = "Shaders/phong_weightCalc.txt"
        folderTex = "Shaders/Tex/"
        folderColor = "Shaders/Color/"
        shaderTex, errorsTex = shaderLoader.load(folderTex, [phong])
        shaderColor, errorsColor = shaderLoader.load(folderColor, [phong])
        
        for error in errorsTex:
            logger.warning(error)
        for error in errorsColor:
            logger.warning(error)
        
        GLModel.shaders["tex"] = shaderTex
        GLModel.shaders["color"] = shaderColor
