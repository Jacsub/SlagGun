import math
import pygame

from engine.clamp import *
from engine.matrix import *
from engine.abstract import *
from engine.image import *



class Texture(): # This is here so I don't have to make a copy of a
                 # surface for every triangle it's mapped to
    def __init__(self, texturePath):
        self.surface = pygame.image.load(texturePath)
    
    def get_colour_at(self, index:tuple):
        return self.surface.get_at(index)



AMBIENTLIGHT = (10, 10, 10) # This is the colour absolute shadow is interpolated to 



class Tri(Abstract): # This should be a child to an abstract which will serve as a wrapper for a group of polys.
    def __init__(self, 
                 vertices:list[list[float]], 
                 albedo:tuple, 
                 lit:bool, 
                 tags:list[str]=None):   
        super().__init__(ORIGIN, I3, ["Tri"] + tags if tags else [])
        
        # Vertices should be an array of 3 arrays.
        # Each array is a coordinate, done in clockwise 
        # order if you're looking at the opaque side.

        # This gets converted to a 3x3 matrix with each
        # collumb being a coordinate.

        # Is this really annoying? Yes!
        # But it makes it easier to apply transformation 
        # matrices to polygons so I'll just hate myself later 

        self.vertices = Matrix(vertices).get_transpose()
        self.albedo = albedo
        self.lit = lit
        
    def get_vertices(self):
        return self.vertices
    
    def set_vertices(self, vertices):
        self.vertices = vertices

    def get_albedo(self):
        return self.albedo
    
    def set_albedo(self, albedo:tuple):
        self.albedo = albedo

    def get_normal(self):
        vertex1 = self.vertices.get_collumb(0)
        vertex2 = self.vertices.get_collumb(1)
        vertex3 = self.vertices.get_collumb(2)

        edge1 = vertex2.subtract(vertex1)
        edge2 = vertex3.subtract(vertex1)

        return self.objectiveDistortion.apply(edge1.get_cross_product(edge2)).set_magnitude(1)
    

    def get_light_cast(self, lights:list[Abstract], triObjectiveVertices:Matrix):
        vertices = triObjectiveVertices.get_contents()
        center = []

        for i in range(3):
            center.append([(vertices[i][0] + vertices[i][1] + vertices[i][2]) / 3])

        center = Matrix(center)

        casts = [AMBIENTLIGHT]

        for light in lights:
            dirAndDist = light.get_direction_and_distance(center)

            if dirAndDist[1] > 0.1:
                angleAmount = self.get_normal().get_dot_product(dirAndDist[0])
                
                interpolationAmount = (1 / ((dirAndDist[1] / light.brightness) ** 2)) * ((angleAmount + 1) / 2)

                cast = interpolate_colour((0, 0, 0), light.colour, interpolationAmount)
            else:
                cast = (255, 255, 255)
                
            casts.append(cast)

        return add_colours(casts)
        


class GradientTri(Tri): # This is just a tri with coloured vertices instead of a flat colour
    def __init__(self,
                 vertices:list[list[float]], 
                 albedo1:tuple,
                 albedo2:tuple,
                 albedo3:tuple,
                 lit:bool, 
                 tags:list[str]=None):
        super().__init__(vertices, (0, 0, 0), lit, tags)

        self.albedo1 = albedo1
        self.albedo2 = albedo2
        self.albedo3 = albedo3

    def get_albedo1(self):
        return self.albedo1
    
    def get_albedo1(self, albedo1:tuple):
        self.albedo1 = albedo1

    def get_albedo2(self):
        return self.albedo2
    
    def get_albedo2(self, albedo2:tuple):
        self.albedo1 = albedo2

    def get_albedo3(self):
        return self.albedo3
    
    def get_albedo3(self, albedo3:tuple):
        self.albedo1 = albedo3



class TextureTri(Tri): # Tri with a texture
    def __init__(self,
                 vertices:list[list[float]], 
                 texture:Texture,
                 uv1:tuple,
                 uv2:tuple,
                 uv3:tuple,
                 lit:bool, 
                 tags:list[str]=None):
        super().__init__(vertices, (0, 0, 0), lit, tags)

        self.texture = texture

        self.uv1 = uv1
        self.uv2 = uv2
        self.uv3 = uv3



class Mesh(Abstract):
    def __init__(self, 
                 location:Matrix=None, 
                 distortion:Matrix=None, 
                 tags:list[str]=None):
        super().__init__(location, distortion, tags)
    
    def change_tris_to_gradient(self, colour1, colour2, colour3):
        for tri in self.get_substracts_of_type(Tri) + self.get_substracts_of_type(TextureTri):
            self.add_child_relative(GradientTri(tri.vertices.get_transpose().get_contents(), colour1, colour2, colour3, tri.lit, tri.tags))
            tri.kill_self_and_substracts()
            del tri
    
    def change_tris_to_flat_colour(self, colour):
        for tri in self.get_substracts_of_type(GradientTri) + self.get_substracts_of_type(TextureTri):
            self.add_child_relative(Tri(tri.vertices.get_transpose().get_contents(), colour, tri.lit, tri.tags))
            tri.kill_self_and_substracts()
            del tri



class Plane(Mesh):
    def __init__(self, 
                 quadResolution:tuple,
                 colour:tuple, 
                 lit:bool=None,
                 location:Matrix=None, 
                 distortion:Matrix=None,
                 tags:list[str]=None,):
        super().__init__(location if location else ORIGIN, 
                         distortion if distortion else I3,
                         tags if tags else [])
        
        self.quadResolution = quadResolution # Number of quads along each side
        self.colour = colour
        self.lit = lit if lit is not None else False

        self.generate_plane()

    def generate_plane(self):
        quadWidth = 1 / self.quadResolution[0]
        quadHeight = 1 / self.quadResolution[1]

        for i in range(self.quadResolution[0]):
            for j in range(self.quadResolution[1]):
                corner = (-0.5 + quadWidth * i, -0.5 + quadHeight * j)

                self.add_child_relative(Tri([[corner[0], 0, corner[1]],
                                             [corner[0], 0, corner[1] + quadHeight],
                                             [corner[0] + quadWidth, 0, corner[1]]], self.colour, self.lit, ["PlaneTri"]))
                self.add_child_relative(Tri([[corner[0] + quadWidth, 0, corner[1] + quadHeight],
                                             [corner[0] + quadWidth, 0, corner[1]],
                                             [corner[0], 0, corner[1] + quadHeight]], self.colour, self.lit, ["PlaneTri"]))
        
    def set_quad_resolution(self, quadResolution:tuple):
        tris = self.get_children_with_tag("PlaneTri")
        for tri in tris:
            tri.kill_self()
        
        self.quadResolution = quadResolution

        self.generate_plane()

    def set_pattern_triangles(self, colour1:tuple, colour2:tuple):
        tris = self.get_children_with_tag("PlaneTri")

        for i in range(0, len(tris), 2):
            tris[i].set_albedo(colour1)
            tris[i+1].set_albedo(colour2)

    def set_pattern_gradient(self, left, right):
        tris = self.get_children_with_tag("PlaneTri")

        step = []

        for i in range(3):
            step.append((left[i] - right[i]) / self.quadResolution[1])

        for i in range(self.quadResolution[1]):
            for j in range(self.quadResolution[0] * 2):
                tris[i * self.quadResolution[0] * 2 + j].set_albedo((left[0] + j * step[0], 
                                                                 left[1] + j * step[1], 
                                                                 left[2] + j * step[2]))
    
    def set_pattern_texture(self, texture:Texture):
        textureHeight = texture.surface.get_height() - 1

        UVWidth = math.floor((texture.surface.get_width() - 1)/ self.quadResolution[0])
        UVHeight = math.floor((textureHeight - 1) / self.quadResolution[1]) 

        tris = self.get_children_with_tag("PlaneTri")

        for i in range(self.quadResolution[1]):
            for j in range(0, self.quadResolution[0] * 2, 2):
                currentTri = tris[i * self.quadResolution[0] * 2 + j]

                self.add_child_relative(TextureTri(currentTri.vertices.get_transpose().get_contents(), texture, 
                                                   (i * UVWidth, textureHeight - (j/2) * UVHeight),
                                                   (i * UVWidth, textureHeight - ((j/2)+1) * UVHeight),
                                                   ((i+1) * UVWidth, textureHeight - (j/2) * UVHeight), True))
                
                currentTri = tris[i * self.quadResolution[0] * 2 + j + 1]

                self.add_child_relative(TextureTri(currentTri.vertices.get_transpose().get_contents(), texture, 
                                                   ((i+1) * UVWidth, textureHeight - (j/2 + 1) * UVHeight),
                                                   (i * UVWidth, textureHeight - ((j/2)+1) * UVHeight),
                                                   ((i+1) * UVWidth, textureHeight - (j/2) * UVHeight), True))
        
        for tri in tris:
            tri.kill_self_and_substracts()



class Cube(Mesh):
    def __init__(self, 
                 colour:tuple, 
                 lit:bool=None,
                 location:Matrix=None, 
                 distortion:Matrix=None,
                 tags:list[str]=None):
        super().__init__(location if location else ORIGIN, 
                         distortion if distortion else I3,
                         tags if tags else [])
        self.colour = colour
        self.lit = lit if lit is not None else False

        self.generate_cube()

    def generate_cube(self):
        # Front
        face1 = Matrix([[-0.5, -0.5, 0.5],
                        [0.5, -0.5, 0.5],
                        [-0.5, 0.5, 0.5]]).get_transpose()
        
        face2 = Matrix([[0.5, 0.5, 0.5],
                        [-0.5, 0.5, 0.5],
                        [0.5, -0.5, 0.5]]).get_transpose()
        
        rotation = I3
        
        for i in range(4):
            self.add_child_relative(Tri(rotation.apply(face1).get_transpose().get_contents(), self.colour, self.lit, ["CubeTri"]))
            self.add_child_relative(Tri(rotation.apply(face2).get_transpose().get_contents(), self.colour, self.lit, ["CubeTri"]))

            rotation = rotation.apply(Matrix([[0, 0, 1],
                                              [0, 1, 0],
                                              [-1, 0, 0]]))
            
        rotation = Matrix([[1, 0, 0],
                           [0, 0, -1],
                           [0, 1, 0]])

        for i in range(2):
            self.add_child_relative(Tri(rotation.apply(face1).get_transpose().get_contents(), self.colour, self.lit, ["CubeTri"]))
            self.add_child_relative(Tri(rotation.apply(face2).get_transpose().get_contents(), self.colour, self.lit, ["CubeTri"]))

            rotation = rotation.apply(Matrix([[1, 0, 0],
                                              [0, -1, 0],
                                              [0, 0, -1]]))

        
    def set_pattern_texture(self, texture:Texture):
        textureSize = texture.surface.get_size()

        tris = self.get_children_with_tag("CubeTri")

        for i in range(6):
            self.add_child_relative(TextureTri(tris[i * 2].get_vertices().get_transpose().get_contents(),
                                               texture,
                                               (0, 0), 
                                               (textureSize[0] - 1, 0), 
                                               (0, textureSize[1] - 1), True))
            
            self.add_child_relative(TextureTri(tris[i * 2 + 1].get_vertices().get_transpose().get_contents(),
                                               texture,
                                               (textureSize[0] - 1, textureSize[1] - 1), 
                                               (textureSize[0] - 1, 0), 
                                               (0, textureSize[1] - 1), True))
            
        for tri in tris:
            tri.kill_self_and_substracts()



class Wavefront(Mesh):
    def __init__(self, 
                 obj:str,
                 colour:tuple, 
                 lit:bool=None,
                 location:Matrix=None, 
                 distortion:Matrix=None,
                 tags:list[str]=None,
                 **kwargs):
        
        super().__init__(location if location else ORIGIN, 
                         distortion if distortion else I3,
                         tags if tags else [])
        
        self.obj = obj # Beware! This only works if your Wavefront file
                       # is split into triangles. No quads! Especially no n-gons.

                       # Don't even think about adding vertex normals in there.

        self.texture = kwargs.get("texture", None)

        self.colour = colour
        self.lit = lit if lit is not None else False

        self.generate_mesh(self.obj)

    def generate_mesh(self, obj):
        vertices = []
        uvs = []

        if self.texture:
            textureSize = (self.texture.surface.get_width() - 1,
                           self.texture.surface.get_height() - 1)

        with open(obj, "r") as obj:

            for line in obj:
                if line[0] == "v": # This could be "v" (vertex) or "vt" (texture coordinate)
                                   # so we have to check the second character too.
                    if line[1] == "t": # This means it's a UV coordinate.
                        values = line.split()
                        uvs.append([float(values[1]), float(values[2])])

                    elif line[1] == " ": # We still have to check cause it could also be "vn" or "vp",
                                         # but this means it's a vertex.
                        values = line.split()
                        vertices.append([float(values[1]), float(values[2]), float(values[3])])

                elif line[0] == "f": # If the file's defining a face:

                    # Here the line is gonna be giving us three verteces 
                    # and three uvs in the format vertex1/uv1 v2/uv2 v3/v3,
                    # so we have to split each element in valuses again.

                    # Each one is a one-based index to a vertex or uv defined
                    # earlier in the file.

                    values = line.split()

                    v = []
                    vt = []

                    for i in range(1, 4):
                        indexes = values[i].split("/")
                        v.append(vertices[int(indexes[0]) - 1])

                        try: # Sometimes you won't have UVs so we have to account for it

                            # This is carcinogenic but we have to do this because
                            # wavefront files store uvs with coordinates between
                            # 1 and 0, so we have to scale it by the texture size

                            relativeSpaceUVS = uvs[int(indexes[1]) - 1]
                            textureSpaceUVS = [math.floor(relativeSpaceUVS[0] * textureSize[0]),
                                               textureSize[1] - math.floor(relativeSpaceUVS[1] * textureSize[1])]
                            
                            vt.append(textureSpaceUVS)
                        except:
                            pass

                    # Now we've extracted our values, we can instantiate our tri.
                    if self.texture:
                        self.add_child_relative(TextureTri(v, self.texture, vt[0], vt[1], vt[2], self.lit, ["MeshTri"]))
                    else:
                        self.add_child_relative(Tri(v, self.colour, self.lit, ["MeshTri"]))



class Light(Abstract):
    def __init__(self, 
                 brightness:float, 
                 colour:tuple=None, 
                 location:Matrix=None, 
                 distortion:Matrix=None, 
                 tags:list[str]=None):
        super().__init__(location, distortion, tags)

        self.brightness = brightness if brightness else 1
        self.colour = colour if colour else (255, 255, 255)

    def get_direction_and_distance(self, point):
        direction = self.objectiveLocation.subtract(point)
        distance = direction.get_magnitude()
        direction = direction.set_magnitude(1)

        return (direction, distance)
    


class SunLight(Light):
    def __init__(self, 
                 brightness:float=None,
                 colour:tuple=None, 
                 distortion:Matrix=None, 
                 tags:list[str]=None):
        super().__init__(ORIGIN, distortion, tags)

        self.brightness = brightness if brightness else 1
        self.colour = colour if colour else (255, 255, 255)

    def get_direction_and_distance(self, point):
        return (self.objectiveDistortion.apply(Matrix([[0],
                                                       [1],
                                                       [0]])), 1)

displayWidth = displaySizeX * 2 - 1
displayHeight = displaySizeY * 2 - 1
        
class Camera(Abstract):
    def __init__(self, location, distortion, fieldOfView:float):
        super().__init__(location, distortion, ["Camera"])

        self.perspectiveConstant = math.tan((fieldOfView / 180) * math.pi / 2) / (DISPLAY.resolution[1] / 2)
        # This converts the field of view into radians, then finds the perspective
        # constant needed to get that field of view.

        # To figure out this process, let's imagine a tower exactly one unit
        # away from the camera, so we're only dividing by the constant (1 * constant)

        # We can find half the number of units the fov will reach up the tower by taking
        # tan(half the fov), because it makes a right angled triangle and tan(theta) 
        # equals the opposite over the adjacent.

        # Therefore, we know tan(theta) / perspectiveConstant = 1/2 the resolution

        # Rearrange to make perspectiveConstant = tan(theta) / half the resolution
        
    def project_tri(self, cameraLocationMatrix:Matrix, inversion:Matrix, tri:Tri, depthBuffer:Image, lights:list[Light]=[]):
        triLocation = tri.objectiveLocation.get_contents()

        triLocationMatrix = Matrix([[triLocation[0][0], triLocation[0][0], triLocation[0][0]],  # This is the tri's location
                                    [triLocation[1][0], triLocation[1][0], triLocation[1][0]],  # repeated three times as collumbs
                                    [triLocation[2][0], triLocation[2][0], triLocation[2][0]]]) # in a 3x3 matrix

        triObjectiveVertices = tri.objectiveDistortion.apply(tri.get_vertices()).add(triLocationMatrix) # The tri's vertices in objective space
        
        triCameraVertices = inversion.apply(triObjectiveVertices.subtract(cameraLocationMatrix)).get_contents() # This is the tri's vertices
                                                                                                                # relative to the camera
        # Finds the tri's position relative to the camera
        
        if triCameraVertices[2][0] > 0.1 and triCameraVertices[2][1] > 0.1 and triCameraVertices[2][2] > 0.1:
            # Culls all tris behind the camera

            vertex1 = (math.floor(triCameraVertices[0][0] / (triCameraVertices[2][0] * self.perspectiveConstant) + displaySizeX), 
                       math.floor(-triCameraVertices[1][0] / (triCameraVertices[2][0] * self.perspectiveConstant) + displaySizeY))
            
            vertex2 = (math.floor(triCameraVertices[0][1] / (triCameraVertices[2][1] * self.perspectiveConstant) + displaySizeX), 
                       math.floor(-triCameraVertices[1][1] / (triCameraVertices[2][1] * self.perspectiveConstant) + displaySizeY))
            
            vertex3 = (math.floor(triCameraVertices[0][2] / (triCameraVertices[2][2] * self.perspectiveConstant) + displaySizeX), 
                       math.floor(-triCameraVertices[1][2] / (triCameraVertices[2][2] * self.perspectiveConstant) + displaySizeY))

            if ((0 <= vertex1[0] <= displayWidth and # This is the worst way i could possibly do this.
                0 <= vertex1[1] <= displayHeight) or   # Too bad! It works so it's staying
                (0 <= vertex2[0] <= displayWidth and
                0 <= vertex2[1] <= displayHeight) or 
                (0 <= vertex3[0] <= displayWidth and
                0 <= vertex3[1] <= displayHeight)):

                if tri.lit:
                    lightCast = tri.get_light_cast(lights, triObjectiveVertices)
                else:
                    lightCast = None
                
                if type(tri) == GradientTri:
                    if tri.lit:
                        colour1 = overlay_colours(tri.albedo1, lightCast)
                        colour2 = overlay_colours(tri.albedo2, lightCast)
                        colour3 = overlay_colours(tri.albedo3, lightCast)
                    else:
                        colour1 = tri.albedo1
                        colour2 = tri.albedo2
                        colour3 = tri.albedo3

                    DISPLAY.draw_triangle(vertex1, vertex2, vertex3, 
                                          depthBuffer, triCameraVertices[2][0], triCameraVertices[2][1], triCameraVertices[2][2],
                                          colour1, 
                                          colour2, 
                                          colour3)
                    
                elif type(tri) == TextureTri:
                    DISPLAY.draw_triangle(vertex1, vertex2, vertex3,
                                          depthBuffer, triCameraVertices[2][0], triCameraVertices[2][1], triCameraVertices[2][2],
                                          texture=tri.texture,
                                          uv1=tri.uv1, uv2=tri.uv2, uv3=tri.uv3,
                                          lightCast = lightCast)

                else:
                    if tri.lit:
                        colour = overlay_colours(tri.albedo, lightCast)
                    else:
                        colour = tri.albedo

                    DISPLAY.draw_triangle(vertex1, vertex2, vertex3, 
                                          depthBuffer, triCameraVertices[2][0], triCameraVertices[2][1], triCameraVertices[2][2],
                                          colour)
        
    def rasterize(self):
        tris = ROOT.get_substracts_of_type(Tri) + ROOT.get_substracts_of_type(GradientTri) + ROOT.get_substracts_of_type(TextureTri)
        
        lights = ROOT.get_substracts_of_type(Light) + ROOT.get_substracts_of_type(SunLight)

        inversion = self.objectiveDistortion.get_3x3_inverse()
        location = self.objectiveLocation.get_contents()
        locationMatrix = Matrix([[location[0][0], location[0][0], location[0][0]],
                                 [location[1][0], location[1][0], location[1][0]],
                                 [location[2][0], location[2][0], location[2][0]]])
        
        DISPLAY.fill((255, 255, 255))
        DEPTHBUFFER.fill(1024.0)
        
        for tri in tris:
            self.project_tri(locationMatrix, inversion, tri, DEPTHBUFFER, lights)
        
        DISPLAY.render_image(WINDOW, (0, 0))

    def render(self):
        self.rasterize()

        #window.blit(depthBuffer, (0, 0))
