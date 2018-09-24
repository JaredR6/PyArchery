import pygame, random, time, math, numpy
from miscClasses import Screen

import mainmenu, pauseScreen

from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *
from render import GLModel

class InputManager(object): # Manage pygame input for multiple key calls
  def __init__(self, eventFn):
    self.getEvents = eventFn
    self.eventTypes = set()         
    self.keysDown = {}
    self.mouseDown = {}
    self.mouseX = 0
    self.mouseY = 0
    self.locked = True
    self.frame = 0
    
  def update(self):
    self.frame += 1
    self.events = self.getEvents()
    self.eventTypes = set()
    self.mouseX = 0
    self.mouseY = 0
    
    for key in self.keysDown:
      self.keysDown[key] += 1
    for key in self.mouseDown:
      self.mouseDown[key] += 1
      
    for event in self.events:
      self.eventTypes.add(event.type)
        
      if   event.type == MOUSEBUTTONDOWN:
        self.mouseDown[event.button] = 1
        
      elif event.type == MOUSEBUTTONUP:
        self.mouseDown.pop(event.button, None)
        
      elif event.type == KEYDOWN:
        self.keysDown[event.key] = 1
        
      elif event.type == KEYUP:
        self.keysDown.pop(event.key, None)
      
      elif event.type == MOUSEMOTION:
        self.mouseX += event.rel[0]
        self.mouseY += event.rel[1]
    
  def isKeyDown(self, key):
    return key in self.keysDown
    
  def keyDownLen(self, key):
    return self.keysDown.get(key, 0)
    
  def keyPressed(self, key):
    return self.keysDown.get(key, 0) == 1
    
  def isMouseDown(self, button):
    return button in self.mouseDown
    
  def mouseDownLen(self, button):
    return self.mouseDown.get(button, 0)
    
  def mousePressed(self, button):
    return self.mouseDown.get(button, 0) == 1
    
  def mouseMoved(self):
    return MOUSEMOTION in self.eventTypes
    
  def isQuit(self):
    return QUIT in self.eventTypes

class Game(object): # The game. I lost it.
  def __init__(self, redrawPerSec, updatePerSec, verbose=False):
    self.fps = redrawPerSec
    self.ups = updatePerSec
    self.width = 1440
    self.height = 810
    self.verbose = verbose
    self.screenNames = []
    self.screenStack = []
    self.inputManager = InputManager(pygame.event.get)
    self.quit = False
    self.assets = {}
    self.data = {}
    self.loadAssets()
    
  def __del__(self):
    self.uninitGame() # Get rid of the game.
  
  def initGame(self):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) # Enable transparency
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL) # Depth must be lower to be placed above other objects.
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glViewport(0, 0, self.width, self.height) # Basic window size.
    
    self.addScreen(mainmenu.MainMenu(self.width, self.height, visible=True), "main") # Add initial menu
    self.addScreen(pauseScreen.PauseScreen(self.width, self.height, visible=False), "pause") # Pause functionality via escape key
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True) # Lock the cursor to the pygame window
    
  def uninitGame(self):
    self.unloadAssets()
  
  def run(self):
    pygame.init()
    pygame.display.set_caption("PyArchery")
    screen = pygame.display.set_mode((self.width, self.height),
                                      HWSURFACE|OPENGL|DOUBLEBUF)
    pygame.display.set_icon(pygame.image.load("Textures/icon.png").convert_alpha())
    
    self.initGame()
    
    # Game loop adapted from "Fix Your Timestep!" by Gaffer Games
    # PyGame code adapted from "OpenGL sample code for PyGame" by WillMcGugan
    # Heavily inspired by XNA game development code
    # OpenGL renders game, PyGame handles context and inputs
    updateRate = 1/self.ups
    renderRate = 1/self.fps    
    currentTime = time.time()
    
    updateSkipMax = 5*updateRate
    
    unusedUpdateTime = 0.0
    unusedRenderTime = 0.0
    
    while not self.quit:
      newTime = time.time()
      renderTime = updateTime = newTime - currentTime
      if updateTime > updateSkipMax:
        updateTime = updateSkipMax # set maximum updateSkip
        
      currentTime = newTime
      
      unusedUpdateTime += updateTime
      unusedRenderTime += renderTime

      while unusedUpdateTime >= updateRate:
        self.updateGame(updateRate)
        unusedUpdateTime -= updateRate
        
      if unusedRenderTime >= renderRate:
        unusedRenderTime %= renderRate
        inter = unusedUpdateTime / updateRate # interpolation 
        self.redrawGame(inter)

    pygame.quit()
  
  def loadAssets(self):    
    pass
    
  def unloadAssets(self):
    for i in range(len(self.screenStack) -1, -1, -1):
      self.screenStack[i].unloadAssets()
    for key in self.assets:
      asset = self.assets[key]
      if isinstance(asset, GLModel):
        asset.unload()
  
  def updateGame(self, time):
    self.inputManager.update()
    if self.inputManager.isQuit():
      self.quit = True
      
    if self.inputManager.locked:
      pygame.mouse.set_visible(False)
      pygame.event.set_grab(True)
    else:
      pygame.mouse.set_visible(True)
      pygame.event.set_grab(False)
      
    commands = {} # Feedback from screen update procedures
    for i in range(len(self.screenStack) -1, -1, -1):
      output = self.screenStack[i].update(self.inputManager, time)
      if output:
        commands.update(output)
    
    if commands.get("quit", False):
      self.quit = True
    
    if commands.get("add", False):
      screen, name = commands["add"]
      self.addScreen(screen, name)
      
    if commands.get("remove", False):
      name = commands["remove"]
      self.removeScreen(name)
      
    if commands.get("update", False):
      oldName, newScreen, newName = commands["update"]
      self.replaceScreen(oldName, newScreen, newName)
    
  def redrawGame(self, inter):
    glClearColor(0,0,0,1)
    glClearDepth(3000.0) 
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT) # Empty screen for drawing
    glLoadIdentity()
    
    for i in range(len(self.screenStack) -1, -1, -1):
      if self.screenStack[i].visible:
        self.screenStack[i].redraw(inter)
    pygame.display.flip()
    
  def addScreen(self, screen, name):
    if not isinstance(screen, Screen):
      raise ValueError("Value added to Screen Stack was not of type Screen.")
    self.screenNames.append(name)
    self.screenStack.append(screen)
    screen.loadAssets(self.assets)
    
  def replaceScreen(self, oldScreenName, newScreen, newScreenName):
    if oldScreenName not in self.screenNames:
      raise ValueError("Unknown screen %s called for replacement." % oldScreenName)
    i = self.screenNames.index(oldScreenName)
    self.screenStack[i].unloadAssets()
    newScreen.loadAssets(self.assets)
    self.screenStack[i] = newScreen
    self.screenNames[i] = newScreenName
    
    
  def removeScreen(self, name):
    if name not in self.screenNames:
      raise ValueError("Unknown screen %s called for removal." % name)
    i = self.screenNames.index(name)
    self.screenStack[i].unloadAssets()
    self.screenStack.pop[i]
    self.screenNames.pop[i]
    
def main():
  fps = 60
  ups = 30
  game = Game(fps, ups)
  game.run()
  del game
  
if __name__ == "__main__":
  main()