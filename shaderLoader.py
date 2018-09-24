from OpenGL.GL import shaders

# returns a tuple of a shader with a tuple of warnings
def load(folder, vertexAppend=[], fragmentAppend=[]):
  vertexShader = ""
  fragmentShader = ""
  try:
    
    # vertex files
    vertexFiles = list(vertexAppend) + [folder + "vertex.txt"]
    for file in vertexFiles:
      with open(file) as v:
        if vertexShader == "":
          vertexShader += "\n"
        vertexShader += v.read()
        
    # attribute file
    fragmentFiles = list(fragmentAppend) + [folder + "fragment.txt"]
    for file in fragmentFiles:
      with open(file) as f:
        if fragmentShader == "":
          fragmentShader += "\n"
        fragmentShader += f.read()
      
    # get uniforms and attributes
    uniforms = []
    attributes = []
    for shader in (vertexShader, fragmentShader):
      i = -1
      while True:
        i = shader.find("uniform", i+1)
        if i == -1:
          break
        start = shader.find(" ", i+8)
        end = shader.find(";", start+1)
        uniforms.append(shader[start:end].strip())
  
      i = -1
      while True:
        i = shader.find("attribute", i+1)
        if i == -1:
          break
        start = shader.find(" ", i+10)
        end = shader.find(";", start+1)
        attributes.append(shader[start:end].strip())
    
    vertexCompiled = shaders.compileShader(vertexShader, shaders.GL_VERTEX_SHADER)
    fragmentCompiled = shaders.compileShader(fragmentShader, shaders.GL_FRAGMENT_SHADER)
    shader = shaders.compileProgram(vertexCompiled, fragmentCompiled)
    
    # record unused uniforms and attributes
    errors = []
    for uniform in uniforms:
        location = shaders.glGetUniformLocation( shader,  uniform )
        if location in (None,-1):
            errors.append('No uniform: %s'%( uniform ))
        setattr( shader, uniform, location )

    for attribute in attributes:
        location = shaders.glGetAttribLocation( shader, attribute )
        if location in (None,-1):
            errors.append('No attribute: %s'%( attribute ))
        setattr( shader, attribute, location )
    
    return (shader, tuple(errors))
  except:
    if vertexShader == "":
      raise ValueError("Vertex shader files not found")
    elif fragmentShader == "":
      raise ValueError("Vertex shader or fragment Shader files not found")
    else:
      raise ValueError("Shader compile failure")
  