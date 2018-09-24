import math, random, pygame, copy, miscClasses

from OpenGL.GL import *
from OpenGL.GLU import *

import render as renderGL
from Quaternion import Vector, Quaternion
from arrows import ArrowQuat, EntityArray, Target, PlayerTarget

class MainMenu(miscClasses.Screen):
    def __init__(self, width, height, verbose=False, visible=True):
        super().__init__(width, height, verbose, visible)
        self.vals = miscClasses.GameState(x=0, y=-40, z=0, cx=0, cy=0, speed=5,
                                          playerArrows=EntityArray({}))
        self.quit = Target(-120, 59, 0, 20, 8, 16)
        self.target = Target(68, 100, -30, 20, 12, 24)
        self.dodge = Target(68, 100, 30, 20, 12, 24)
        self.last = None
    
    def update(self, inputManager, time):
        self.vals.update()
        if inputManager.locked:
            
        ## Movement
            if inputManager.isKeyDown(pygame.K_w):
                self.vals["z"] += math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] -= math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_s):
                self.vals["z"] -= math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] += math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_a):
                self.vals["z"] += math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] += math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_d):
                self.vals["z"] -= math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] -= math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_p):
                for key in self.vals["playerArrows"]:
                    arrow = self.vals["playerArrows"][key]
                    print("Arrow:", arrow.coords.x, arrow.coords.y, arrow.coords.z)   
                print(self.vals["x"], self.vals["y"], self.vals["z"], self.vals["cx"], self.vals["cy"])
                
            self.vals["x"] = max(-69, min(69, self.vals["x"]))        
            self.vals["z"] = max(-69, min(69, self.vals["z"]))

            self.updateCamera(inputManager.mouseX, inputManager.mouseY)
            
        ## Weapon Control
            if inputManager.mouseDownLen(1) % 8 == 1:
                self.vals["playerArrows"].add(ArrowQuat.fromCamera(self.vals["x"], self.vals["y"], self.vals["z"], self.vals["cx"], self.vals["cy"]))
            self.vals["playerArrows"] = self.vals["playerArrows"].update(time)
            for arrow in self.vals["playerArrows"]:
                if self.vals["playerArrows"][arrow].inBox(*self.quit.getBox()):
                    return {"quit":True}
                if self.vals["playerArrows"][arrow].inBox(*self.target.getBox()):
                    return {"update":("main",TargetGame(self.width, self.height, visible=True),"target")}
                if self.vals["playerArrows"][arrow].inBox(*self.dodge.getBox()):
                    return {"update":("main",DodgeGame(self.width, self.height, visible=True),"dodge")}
    
    def updateCamera(self, mouseX, mouseY):
        self.vals["cx"] += mouseX
        self.vals["cy"] = max(-90, min(90, self.vals["cy"]+mouseY))
    
    def redraw(self, inter):
        self.vals.setInterpol(inter)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(90, self.aspect, 0.1, 3000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
        glPushMatrix() # Matrix used to render GUI bow.
        glMultMatrixf([-0.98649979, -0.04556412, -0.15729615,  0,
                       -0.08630754,  0.96094722,  0.26292863,  0,
                        0.13917318,  0.27295488, -0.95190674,  0,
                        4.5,        -1.79999995, -3.5,         1])
        self.assets["bow"].render()
        glPopMatrix()
    
        glRotate(self.vals.d["cy"], 1, 0, 0) # Rotate from camera
        glRotate(self.vals.d["cx"], 0, 1, 0)
        
        glTranslatef(0.0+self.vals.d["x"], 0.0+self.vals.d["y"], 0.0+self.vals.d["z"]) # Move world from camera
        
        glPushMatrix()
        glScalef(30, 30, 30)
        self.assets["mainWorld"].render() # Render "skybox"
        glPopMatrix()
        
        arrows = self.vals.d["playerArrows"].items
        for key in arrows:
            arrow = arrows[key]
            glPushMatrix()
            glTranslate(arrow.coords.x, arrow.coords.y, arrow.coords.z) # arrow position
            glMultMatrixf(arrow.quat.rotationMatrix()) # arrow rotation
            glScalef(4,4,4)
            self.assets["arrow"].render()
            glPopMatrix()
            
        ## Transparents are drawn last due to how OpenGL handles the z-buffer
        glPushMatrix()
        glTranslatef(68, 59, -15)
        glScalef(15, 15, 15)
        glRotatef(-90, 0, 1, 0)
        self.assets["mouseInstr"].render()
        glTranslatef(2, 0, 0)
        self.assets["keyInstr"].render()
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(68, 140, 0)
        glScalef(0, 30, 60)
        glRotatef(-90, 0, 1, 0)
        self.assets["logo"].render()
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(*self.target.getPos())
        glScalef(*self.target.getScale())
        glRotatef(-90, 0, 1, 0)
        self.assets["targetGame"].render()
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(*self.dodge.getPos())
        glScalef(*self.dodge.getScale())
        glRotatef(-90, 0, 1, 0)
        self.assets["dodgeGame"].render()
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(*self.quit.getPos())
        glScalef(*self.quit.getScale())
        glRotatef(90, 0, 1, 0)
        self.assets["quit"].render()
        glPopMatrix()

        if self.assets.get("lastScore", None):
            glPushMatrix()
            glTranslatef(68, 64, 45)
            glScalef(15, 5, 15)
            glRotatef(-90, 0, 1, 0)
            self.assets["last"].render()
            glTranslatef(0,-2,0)
            self.assets["lastDisplay"].render()
            glPopMatrix()
    
    def loadAssets(self, assets):
        super().loadAssets(assets)
        self.assets["mainWorld"] = renderGL.GLModel("main.3ds")
        self.assets["bow"] = renderGL.GLModel("bow.dae")
        self.assets["arrow"] = renderGL.GLModel("arrow.3ds")
        self.assets["mouseInstr"] = renderGL.GLModel("square.3ds", image="mouse.png")
        self.assets["keyInstr"] = renderGL.GLModel("square.3ds", image="keys.png")
        self.assets["quit"] = renderGL.GLModel("square.3ds", image="quitGame.png")
        self.assets["targetGame"] = renderGL.GLModel("square.3ds", image="target.png")
        self.assets["dodgeGame"] = renderGL.GLModel("square.3ds", image="dodge.png")
        self.assets["logo"] = renderGL.GLModel("square.3ds", image="logo.png")
        if self.assets.get("lastScore", None): # Last score appears when returning from game
            font = pygame.font.SysFont("Fixedsys", 64)
            surface = font.render("Last score:", 1, (255, 255, 255))
            self.assets["last"] = renderGL.GLModel("square.3ds", rawSurface=surface)
            surface = font.render(self.assets["lastScore"], 1, (255, 255, 255))
            self.assets["lastDisplay"] = renderGL.GLModel("square.3ds", rawSurface=surface)
            
class DodgeGame(miscClasses.Screen):
    def __init__(self, width, height, verbose=False, visible=True):
        super().__init__(width, height, verbose, visible)
        self.vals = miscClasses.GameState(x=0, y=-30, z=0, cx=0, cy=0, speed=5, worldArrows=EntityArray({}))
        if random.random() < .5:
            self.world = "dayscape"
        else:
            self.world = "cityscape"
        self.frames = 0
        self.ports = [ArrowPort(Vector(-240, 180, 0,    normalize=False), 0, 0, -1, 3, 1, 1),
                      ArrowPort(Vector( 0,   180, -240, normalize=False), -1, 0, 0, 1, 1, 3),
                      ArrowPort(Vector( 240, 180, 0,    normalize=False), -3, -1, -1, 0, 0, 1),
                      ArrowPort(Vector( 0,   180, 240,  normalize=False), -1, -1, -3, 1, 0, 0)]
        self.target = PlayerTarget(self.vals, 15, 15, 15)
        
                  
    
    def update(self, inputManager, time):
        self.vals.update()
        if inputManager.locked:
            self.frames += 1
            
        ## Movement
            if inputManager.isKeyDown(pygame.K_w):
                self.vals["z"] += math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] -= math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_s):
                self.vals["z"] -= math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] += math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_a):
                self.vals["z"] += math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] += math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_d):
                self.vals["z"] -= math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] -= math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                
            self.vals["x"] = max(-56, min(56, self.vals["x"]))        
            self.vals["z"] = max(-56, min(56, self.vals["z"]))
            
            if self.frames % 5 == 0:
                self.vals["worldArrows"].add(self.ports[random.randint(0, 3)].genArrow())   
            self.vals["worldArrows"] = self.vals["worldArrows"].update(time)
            for key in self.vals["worldArrows"]:
                arrow = self.vals["worldArrows"][key]
                if arrow.inBox(*self.target.getBox()):
                    minutes = str(self.frames // 1800)
                    seconds = str((self.frames % 1800) // 30)
                    if len(seconds) < 2: seconds = "0" + seconds
                    milli = ("%0.2f" % ((self.frames % 30) / 30))[2:]
                    self.assets["lastScore"] = "%s:%s.%s" % (minutes, seconds, milli)
                    return {"update":("dodge", MainMenu(self.width, self.height, visible=True), "main")}
                        
                     
            self.updateCamera(inputManager.mouseX, inputManager.mouseY)
    
    def updateCamera(self, mouseX, mouseY):
        self.vals["cx"] += mouseX
        self.vals["cy"] = max(-90, min(90, self.vals["cy"]+mouseY))
        
    def redraw(self, inter):
        self.vals.setInterpol(inter)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(90, self.aspect, 0.1, 3000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glRotate(self.vals.d["cy"], 1, 0, 0)
        glRotate(self.vals.d["cx"], 0, 1, 0)
        
        glTranslatef(0.0+self.vals.d["x"], 0.0+self.vals.d["y"], 0.0+self.vals.d["z"])
        
        glPushMatrix()
        glScalef(60, 60, 60)
        self.assets[self.world].render()
        glPopMatrix()
        
        arrows = self.vals.d["worldArrows"]
        for key in arrows:
            arrow = arrows[key]
            glPushMatrix()
            glTranslate(arrow.coords.x, arrow.coords.y, arrow.coords.z)
            glMultMatrixf(arrow.quat.rotationMatrix())
            glScalef(4,4,4)
            self.assets["arrow"].render()
            glPopMatrix()
            
        for arrow in self.ports:
            glPushMatrix()
            glTranslatef(arrow.pos.x, arrow.pos.y, arrow.pos.z)
            glScalef(5,5,5)
            self.assets["cube"].render()
            glPopMatrix()
  
    def loadAssets(self, assets):
        super().loadAssets(assets)
        self.assets["arrow"] = renderGL.GLModel("arrow.3ds")
        self.assets["dayscape"] = renderGL.GLModel("dayscape.3ds")
        self.assets["cityscape"] = renderGL.GLModel("cityscape.3ds")
        self.assets["cube"] = renderGL.GLModel("cube.3ds")
        
    def unloadAssets(self):
        pass
        
class TargetGame(miscClasses.Screen):
    def __init__(self, width, height, verbose=False, visible=True):
        super().__init__(width, height, verbose, visible)
        self.vals = miscClasses.GameState(x=0, y=-30, z=0, cx=0, cy=0, speed=5, playerArrows=EntityArray({}))
        self.targets = []
        self.targetsHit = 0
        if random.random() < .5:
            self.world = "dayscape"
        else:
            self.world = "cityscape"
        self.frames = 0
        self.delay = 180
        
    def update(self, inputManager, time):
        self.vals.update()
        if inputManager.locked:
            self.frames += 1
            
        ## Movement
            if inputManager.isKeyDown(pygame.K_w):
                self.vals["z"] += math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] -= math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_s):
                self.vals["z"] -= math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] += math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_a):
                self.vals["z"] += math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] += math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
            if inputManager.isKeyDown(pygame.K_d):
                self.vals["z"] -= math.sin(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                self.vals["x"] -= math.cos(self.vals["cx"]*math.pi/180)*self.vals["speed"]
                
            self.vals["x"] = max(-56, min(56, self.vals["x"]))        
            self.vals["z"] = max(-56, min(56, self.vals["z"]))
                     
            self.updateCamera(inputManager.mouseX, inputManager.mouseY)
            
            if self.frames % 30 == 0:
                self.targets.append(self.genTarget())
                                    
            if inputManager.mouseDownLen(1) % 8 == 1:
                self.vals["playerArrows"].add(ArrowQuat.fromCamera(self.vals["x"], self.vals["y"], self.vals["z"], self.vals["cx"], self.vals["cy"]))
            self.vals["playerArrows"] = self.vals["playerArrows"].update(time)
            
            for arrow in self.vals["playerArrows"]: # checks for collision between arrow and target
                for ti in range(len(self.targets)):
                    if self.vals["playerArrows"][arrow].inBox(*self.targets[ti][0].getBox()):
                        self.vals["playerArrows"][arrow].frame = -1
                        self.targetsHit += 1
                        if self.targetsHit >= 30:
                            minutes = str(self.frames // 1800)
                            seconds = str((self.frames % 1800) // 30)
                            if len(seconds) < 2: seconds = "0" + seconds
                            milli = ("%0.2f" % ((self.frames % 30) / 30))[2:]
                            self.assets["lastScore"] = "%s:%s.%s" % (minutes, seconds, milli)
                            return {"update":("target", MainMenu(self.width, self.height, visible=True), "main")}
                        del self.targets[ti]
                        if len(self.targets) == 0:
                            self.targets.append(self.genTarget())
                        break
                        
                        
    
    def updateCamera(self, mouseX, mouseY):
        self.vals["cx"] += mouseX
        self.vals["cy"] = max(-90, min(90, self.vals["cy"]+mouseY))
        
    def redraw(self, inter):
        self.vals.setInterpol(inter)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(90, self.aspect, 0.1, 3000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
        glPushMatrix()
        glMultMatrixf([-0.98649979, -0.04556412, -0.15729615,  0,
                       -0.08630754,  0.96094722,  0.26292863,  0,
                        0.13917318,  0.27295488, -0.95190674,  0,
                        4.5,        -1.79999995, -3.5,         1])
        self.assets["bow"].render()
        glPopMatrix()

        glRotate(self.vals.d["cy"], 1, 0, 0)
        glRotate(self.vals.d["cx"], 0, 1, 0)
        
        glTranslatef(0.0+self.vals.d["x"], 0.0+self.vals.d["y"], 0.0+self.vals.d["z"])
        
        glPushMatrix()
        glScalef(60, 60, 60)
        self.assets[self.world].render()
        glPopMatrix()
        
        arrows = self.vals.d["playerArrows"].items
        for key in arrows:
            arrow = arrows[key]
            glPushMatrix()
            glTranslate(arrow.coords.x, arrow.coords.y, arrow.coords.z)
            glMultMatrixf(arrow.quat.rotationMatrix())
            glScalef(4,4,4)
            self.assets["arrow"].render()
            glPopMatrix()
            
        for target in self.targets:            
            glPushMatrix()
            glTranslatef(*target[0].getPos())
            glRotatef(target[1], 0, 1, 0)
            glScalef(20, 20, 20)
            self.assets["target"].render()
            glPopMatrix()
        
    def loadAssets(self, assets):
        super().loadAssets(assets)
        self.assets["bow"] = renderGL.GLModel("bow.dae")
        self.assets["arrow"] = renderGL.GLModel("arrow.3ds")
        self.assets["target"] = renderGL.GLModel("target.3ds")
        self.assets["dayscape"] = renderGL.GLModel("dayscape.3ds")
        self.assets["cityscape"] = renderGL.GLModel("cityscape.3ds")
        
    def unloadAssets(self):
        pass
        
    def genTarget(self):
        x = y = z = angle = 0
        row = random.randint(1, 4)
        column = random.randint(1, 3)
        offset = random.randint(-15, 15) * 6
        y = 40 + column * 30
        if row == 1:
            x = 140 + column * 20
            z = offset
        elif row == 2:
            x = -140 - column * 20
            z = offset
        elif row == 3:
            x = offset
            z = 140 + column * 20
            angle = 90
        else:
            x = offset
            z = -140 - column * 20
            angle = 90
        return (Target(x, y, z, 20, 20, 20), angle)
        
        
class ArrowPort(object): # Where arrows can spawn from
    def __init__(self, pos, xlo, ylo, zlo, xhi, yhi, zhi):
        self.pos = pos
        self.xlo = xlo
        self.ylo = ylo
        self.zlo = zlo
        self.xhi = xhi
        self.yhi = yhi
        self.zhi = zhi
        
    def genArrow(self):
        direction = Vector(random.randint(self.xlo*10, self.xhi*10)/10,
                           random.randint(self.ylo*10, self.yhi*10)/10,
                           random.randint(self.zlo*10, self.zhi*10)/10)
        velocity = direction.scaled(random.randint(5, 10))
        quat = velocity.normalized().getQuaternionTo(Vector.default())
        gravity = Vector(0, -10, 0, normalize=False)
        return ArrowQuat(self.pos, quat, velocity, gravity, True)
    
            
if __name__ == "__main__":    
  from game import Game
  fps = 60
  ups = 30
  game = Game(fps, ups)
  game.run()
  del game