import math # There's a lot of math.

class Vector(object):
    defaultVector = None
    def __init__(self, x=1, y=0, z=0, normalize=True):
        self.x = x
        self.y = y
        self.z = z
        if normalize:
            self.normalize()
    
    def __add__(self, other):
        v = self.copy()
        v.x += other.x
        v.y += other.y
        v.z += other.z
        return v
    
    def __sub__(self, other):
        v = self.copy()
        v.x -= other.x
        v.y -= other.y
        v.z -= other.z
        return v
        
    def __mul__(self, other):
        v = self.copy()
        v.x *= other
        v.y *= other
        v.z *= other
        return v
    
    def __eq__(self, other):
        if not isinstance(other, Vector):
            return False
        else:
            return (math.isclose(self.x, other.x) and
                    math.isclose(self.y, other.y) and
                    math.isclose(self.z, other.z))
                    
    def __ne__(self, other):
        return not self == other
        
    def __repr__(self):
        return "Vector(x=%1.3f, y=%1.3f, z=%1.3f)" % (self.x, self.y, self.z)
        
    def dot(self, other):
        return (self.x*other.x + self.y*other.y + self.z*other.z)
        
    def cross(self, other):
        return Vector(self.y*other.z - self.z*other.y,
                      self.z*other.x - self.x*other.z,
                      self.x*other.y - self.y*other.x, normalize=False)
        
        
    def copy(self, normalize=False):
        return Vector(self.x, self.y, self.z, normalize=normalize)
        
    def normalize(self):
        len = self.magnitude()
        if len == 0:
            self.x = self.y = self.z = 0
        else:
            self.x /= len
            self.y /= len
            self.z /= len
        
    def normalized(self):
        v = self.copy()
        v.normalize()
        return v
        
    def magnitude(self):
        return (self.x**2 + self.y**2 + self.z**2)**.5
        
    def scaled(self, n):
        v = self.copy()
        v.x *= n
        v.y *= n
        v.z *= n
        return v
        
    def asQuaternion(self):
        return Quaternion(0, self.x, self.y, self.z)
        
    def getQuaternionTo(self, other):
        # From https://bitbucket.org/sinbad/ogre/src/9db75e3ba05c/OgreMain/include/OgreVector3.h?fileviewer=file-view-default#cl-651
        q = None
        dot = self.normalized().dot(other.normalized())
        if dot >= .99999:
            return Quaternion(1,0,0,0)
            
        if dot < -.99999:
            axis = Vector(1,0,0).cross(self)
            if axis.magnitude() == 0:
                axis = Vector(0,1,0).cross(self)
            axis.normalize()
            q = Quaternion.fromAngleAxis(math.pi, axis)
        else:
            s = ((1+dot)*2)**.5
            c = self.cross(other)
            q = Quaternion(s/2, c.x/s, c.y/s, c.z/s)
        return q
        
    @staticmethod
    def default():
        if not Vector.defaultVector:
            Vector.defaultVector = Vector(0,1,0)
        return Vector.defaultVector
        
    @staticmethod
    def interpolate(va, vb, delta):
        return Vector(va.x + (vb.x - va.x)*delta, 
                      va.y + (vb.y - va.y)*delta, 
                      va.z + (vb.z - va.z)*delta, normalize=False)
        

class Quaternion(object):
    def __init__(self, w=1, x=0, y=0, z=0, normalize=True):
        self.w = w
        self.x = x
        self.y = y
        self.z = z
        if normalize:
            self.normalize()
              
    def __eq__(self, other):
        if not isinstance(other, Quaternion):
            return False
        else:
            return (math.isclose(self.w, other.w) and
                    math.isclose(self.x, other.x) and
                    math.isclose(self.y, other.y) and
                    math.isclose(self.z, other.z))
                    
    def __ne__(self, other):
        return not self == other
        
    def __repr__(self):
        return "Quaternion(w:%s, x:%s, y:%s, z:%s)" % (self.w, self.x, self.y, self.z)
        
    def __mul__(self, other):
        try:
            w = self.w*other.w - self.x*other.x - self.y*other.y - self.z*other.z
            x = self.w*other.x + self.x*other.w + self.y*other.z - self.z*other.y
            y = self.w*other.y - self.x*other.z + self.y*other.w + self.z*other.x
            z = self.w*other.z + self.x*other.y - self.y*other.x + self.z*other.w
            return Quaternion(w, x, y, z)
        except:
            raise ValueError("implicit multiplication is exclusive to Quaternions. Use Quaternion.scaled(n) for integers and floats instead.")
        
    def __repr__(self):
        return "Quaternion(w=%1.3f, x=%1.3f, y=%1.3f, z=%1.3f)" % (self.w, self.x, self.y, self.z)
        
    def __pow__(self, other):
        return self.ln().scaled(other).exp()
            
    def exp(self):
        # Adapted from https://math.stackexchange.com/questions/939229/unit-quaternion-to-a-scalar-power
        q = self.copy()
        ew = math.exp(self.w) # e^w
        vm = (q.x**2+q.y**2+q.z**2)**.5 # different from magnitude slightly
        val = ew*math.sin(vm)/vm if vm > 0.00001 else 0 # Value used to change xyz. I don't understand the math much but it's important
        q.w = ew*math.cos(vm)
        q.x *= val
        q.y *= val
        q.z *= val
        return q
        
    def ln(self):
        q = self.copy()
        vm = (q.x**2+q.y**2+q.z**2)**.5
        val = math.atan2(vm, q.w)/vm if vm > 0.00001 else 0
        q.w = math.log(self.magnitude())
        q.x *= val
        q.y *= val
        q.z *= val
        return q
        
    def scaled(self, n):
        q = self.copy()
        q.w *= n
        q.x *= n
        q.y *= n
        q.z *= n
        return q
        
    def copy(self, normalize=False):
        return Quaternion(self.w, self.x, self.y, self.z, normalize=normalize)
    
    def conjugate(self):
        self.x, self.y, self.z = -self.x, -self.y, -self.z
        
    def conjugated(self):
        q = self.copy()
        q.conjugate()
        return q
        
    def normalize(self):
        len = self.magnitude()
        if len == 0:
            self.w = 1
            self.x = self.y = self.z = 0
        else:
            self.w /= len
            self.x /= len
            self.y /= len
            self.z /= len
        
    def normalized(self):
        q = self.copy()
        q.normalize()
        return q
        
    def magnitude(self):
        return (self.w**2+self.x**2+self.y**2+self.z**2)**.5
    
    def rotationMatrix(self):
        return [ 1 - 2*self.y**2 - 2*self.z**2,     2*self.x*self.y - 2*self.z*self.w, 2*self.x*self.z + 2*self.y*self.w, 0,
                 2*self.x*self.y + 2*self.z*self.w, 1 - 2*self.x**2 - 2*self.z**2,     2*self.y*self.z - 2*self.x*self.w, 0,
                 2*self.x*self.z - 2*self.y*self.w, 2*self.y*self.z + 2*self.x*self.w, 1 - 2*self.x**2 - 2*self.y**2,     0,
                 0,                                 0,                                 0,                                 1 ]
                 
    def toEuler(self):
        if abs(self.x*self.y + self.w*self.z -.5) < .001:
            return Vector(  2 * math.atan2(self.x, self.w),  math.pi/2, 0, normalize=False )
        elif abs(self.x*self.y + self.w*self.z +.5) < .001:
            return Vector( -2 * math.atan2(self.x, self.w), -math.pi/2, 0, normalize=False )
        else:
            return Vector( math.atan2( 2*( -self.w*self.x + self.y*self.z ), 1 - 2*( self.x**2+self.y**2 ) ),
                           math.asin(  2*(  self.w*self.y - self.z*self.x ) ),
                           math.atan2( 2*( -self.w*self.z + self.x*self.y ), 1 - 2*( self.y**2+self.z**2 ) ),
                           normalize=False )

    @staticmethod
    def interpolate(quatA, quatB, delta):
        return (quatB * quatA.conjugated())**delta * quatA
            
    @staticmethod
    def fromAngleAxis(angle, vector):
        angle /= 2
        w = math.cos(angle)
        x = vector.x * math.sin(angle)
        y = vector.y * math.sin(angle)
        z = vector.z * math.sin(angle)
        return Quaternion(w, x, y, z)
        
if __name__ == "__main__":    
  from game import Game
  fps = 60
  ups = 30
  game = Game(fps, ups)
  game.run()
  del game