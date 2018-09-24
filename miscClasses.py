import random

class Screen(object): # Base object used to guarantee compatibility
  def __init__(self, width, height, verbose, visible):
    self.width = width
    self.height = height
    self.aspect = width/height
    self.verbose = verbose
    self.visible = visible
    
  def update(self, inputManager, time):
    pass
    
  def redraw(self, inter):
    pass
  
  def loadAssets(self, assets):
    self.assets = assets # Connects screen to global dictionary
    
  def unloadAssets(self):
    pass
    
class GameState(object): # Manage interpolated data with previous data
  def __init__(self, **kwargs):
    self.d = InterpolFinder(kwargs)
    
  def __getitem__(self, key):
    return self.d.nextState[key]
    
  def __setitem__(self, key, val):
    self.d.nextState[key] = val
  
  def __delitem__(self, key):
    del self.d[key]
    
  def update(self):
    self.d.update()
    
  def setInterpol(self, inter):
    self.d.setInterpol(inter)
  
class InterpolFinder(object):
  def __init__(self, items):
    self.prevState = items.copy()
    self.nextState = items.copy()
    self.changes = dict()
    self.inter = 0.0
    
  def __repr__(self):
    return "<InterpolFinder with state of %d>" % self.inter
    
  def __len__(self):
    return len(self.items)
    
  def __getitem__(self, key):
    try:
      prev = self.prevState[key]
      next = self.nextState[key]
      inter = getattr(prev, "interpolate", lambda a, b, delta: a + (b-a)*delta) 
      return inter(prev, next, self.inter) # Uses interpolation function if found
    except KeyError:
      raise KeyError( "%s does not exist within this InterpolFinder" % key)
    
  def __setitem__(self, key, val):
    self.nextState[key] = val
    
  def __delitem__(self, key):
    if key in self.prevState:
      del self.prevState[key]
    if key in self.nextState:
      del self.nextState[key]    
    if key in self.nextState:
      del self.nextState[key]
      
  def __iter__(self):
    raise IndexError("GameStates are not iterable!")
  
  def update(self):
    self.prevState = self.nextState.copy()
        
  def setInterpol(self, inter):
    self.inter = inter
  