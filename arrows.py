import random, math
from Quaternion import Vector, Quaternion

class ArrowQuat(object):
    frameRemove = 0
    def __init__(self, coords, quat, velocity, gravity, moving, frame=80):
        self.coords = coords
        self.quat = quat
        self.velocity = velocity  
        self.gravity = gravity
        self.moving = moving
        self.frame = frame
    
    def update(self, dt):
        self.frame -= 1
        if self.moving:
            newCoords = self.coords + self.velocity + self.gravity.scaled(.5*dt**2)
            newQuat = (newCoords-self.coords).normalized().getQuaternionTo(Vector.default())
            newVel = self.velocity + self.gravity.scaled(dt)
            return ArrowQuat(newCoords, newQuat, newVel, self.gravity, self.moving, self.frame)
        else:
            return self.copy()
      
    def copy(self):
        return ArrowQuat(self.coords, self.quat, self.velocity, self.gravity, self.moving, self.frame)
        
    def inBox(self, x1, y1, z1, x2, y2, z2): # If center is within a box
        return ((self.coords.x >= x1 and self.coords.x <= x2) and
                (self.coords.y >= y1 and self.coords.y <= y2) and
                (self.coords.z >= z1 and self.coords.z <= z2))
    
    @staticmethod
    def interpolate(aqa, aqb, dt):
        coords = Vector.interpolate(aqa.coords, aqb.coords, dt)
        quat = Quaternion.interpolate(aqa.quat, aqb.quat, dt)
        return ArrowQuat(coords, quat, None, None, None)
    
    @staticmethod
    def fromCamera(x, y, z, cx, cy): # Grabs an arrow to shoot from near the viewport
        direction = Vector(math.cos( cy*math.pi/180) * math.sin( cx*math.pi/180),
                           math.sin(-cy*math.pi/180),
                           math.cos( cy*math.pi/180) * -math.cos( cx*math.pi/180))
        position = (Vector(-x, -y, -z, normalize=False) 
                    + direction
                    + Vector(5*math.cos(cx*math.pi/180), 0, 5*math.sin(cx*math.pi/180), normalize=False))
        velocity = direction.scaled(20)
        quat = velocity.normalized().getQuaternionTo(Vector.default())
        gravity = Vector(0, -10, 0, normalize=False)
        return ArrowQuat(position, quat, velocity, gravity, True)
    
    
class EntityArray(object): # Array capable of updating and interpolating several objects at once
    def __init__(self, items):
        self.items = items
        
    def __getitem__(self, key):
        return self.items[key]
        
    def __setitem__(self, key, value):
        self.items[key] = value
        
    def __delitem__(self, key):
        del self.items[key]
        
    def __iter__(self):
        return iter(self.items)
        
    def add(self, item):
        if not hasattr(item, "update") or not hasattr(item, "interpolate"):
            raise ValueError("Item does not allow update(dt) or interpolate(a, b, dt)")
        n = 0
        while n in self.items:
            n = random.randint(2, 2**31)
        self.items[n] = item
        
        
    def update(self, dt):
        output = {}
        for key in self.items:
            if self[key].frame > type(self[key]).frameRemove:
                output[key] = type(self[key]).update(self[key], dt)
        return EntityArray(output)
    
    @staticmethod
    def interpolate(eaa, eab, dt):
        output = {}
        for key in eaa:
            if key in eab:
                output[key] = type(eaa[key]).interpolate(eaa[key], eab[key], dt)
        return EntityArray(output)
        
class Target(object): # has functions to check for collision
    def __init__(self, x, y, z, xlen, ylen, zlen):
        self.x = x
        self.y = y
        self.z = z
        self.xlen = xlen
        self.ylen = ylen
        self.zlen = zlen
        
    def getPos(self):
        return(self.x, self.y, self.z)
        
    def getScale(self):
        return(self.xlen, self.ylen, self.zlen)
        
    def getBox(self):
        return (self.x-self.xlen, self.y-self.ylen, self.z-self.zlen,
                self.x+self.xlen, self.y+self.ylen, self.z+self.zlen)
                
class PlayerTarget(object): # When the player is the target
    def __init__(self, vals, xlen, ylen, zlen):
        self.vals = vals
        self.xlen = xlen
        self.ylen = ylen
        self.zlen = zlen
        
    def getBox(self):
        return (-self.vals["x"]-self.xlen, -self.vals["y"]-self.ylen, -self.vals["z"]-self.zlen,
                -self.vals["x"]+self.xlen, -self.vals["y"]+self.ylen, -self.vals["z"]+self.zlen)
        