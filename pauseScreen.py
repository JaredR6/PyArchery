import math, numpy, random, pygame, copy, miscClasses

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo

import render as renderGL

class PauseScreen(miscClasses.Screen):
    
    def __init__(self, width, height, verbose=False, visible=True):
        super().__init__(width, height, verbose, visible)
        
    def update(self, inputManager, time):
        mouseCoords = (inputManager.mouseX, inputManager.mouseY)
        if inputManager.keyPressed(pygame.K_ESCAPE):
            self.visible = not self.visible # Toggle visibility of pause "screen"
        
        if self.visible:
            inputManager.locked = False
        else:
            inputManager.locked = True
        
    def redraw(self, inter):
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -2, 2)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glColor3f(1,0,0)
        glBegin(GL_QUADS)
        glVertex3f(0,          self.height*17/18, 0)
        glVertex3f(0,          self.height,       0)
        glVertex3f(self.width, self.height,       0)
        glVertex3f(self.width, self.height*17/18, 0)
        glEnd()
    
    def loadAssets(self, assets):
        super().loadAssets(assets)
        
    def unloadAssets(self):
        pass
        
def main():
    from game import Game
    game = Game(60, 30)
    game.run()
    del game
    
if __name__ == "__main__":
    main()