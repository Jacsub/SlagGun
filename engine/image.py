import math
import pygame

from engine.clamp import *



pygame.init()
SCREENSIZE = (640, 480)
SCREENSIZEFROMCENTER = (SCREENSIZE[0] / 2, SCREENSIZE[1] / 2)
WINDOW = pygame.display.set_mode(SCREENSIZE)
pygame.display.set_caption("yeentooth")
clock = pygame.time.Clock()


# These are some processing functions which will help us out at the rendering step

def average_colours(colours:list[tuple]):
    average = [0, 0, 0]

    length = len(colours)

    for colour in colours:
        for i in range(3):
            average[i] += colour[i]

    for component in average:
        component /= length

    return (average[0], average[1], average[2])

def clamp_colour(colour:tuple):
    return (clamp(colour[0], 0, 255),
            clamp(colour[1], 0, 255),
            clamp(colour[2], 0, 255))



# Blend modes

def multiply_colours(colours:list[tuple]):
    result = [1, 1, 1]

    for colour in colours:
        for i in range(3):
            result[i] *= colour[i] / 255

    return (result[0] * 255, result[1] * 255, result[2] * 255)

def add_colours(colours:list[tuple]):
    result = []

    for i in range(3):
        channel = 0

        for colour in colours:
            channel += colour[i]

        result.append(clamp(channel, 0, 255))

    return (result[0], result[1], result[2])

def screen_colours(colours:list[tuple]):
    result = [1, 1, 1]

    for colour in colours:
        for i in range(3):
            result[i] *= (1 - (colour[i] / 255))

    return ((1 - result[0]) * 255, (1 - result[1]) * 255, (1 - result[2]) * 255)

def overlay_colours(colour1, colour2):
    result = []

    for i in range(3):
        channel1 = colour1[i] / 255
        channel2 = colour2[i] / 255

        if channel2 >= 0.5:
            result.append(1 - 2 * (1 - channel1) * (1 - channel2))
        else:
            result.append(2 * channel1 * channel2)

    return (result[0] * 255, result[1] * 255, result[2] * 255)

def squash_colour(colour1, colour2):
    result = []

    for i in range(3):
        amount = colour2[i]

        space = 255 - amount

        result.append(space * (colour1[i] / 255) + amount)

    return (result[0], result[1], result[2])



def interpolate_colour(colour1:tuple, colour2:tuple, t:float):
    return (clamp(math.floor(colour1[0] + (colour2[0] - colour1[0]) * abs(t)), 0, 255),
            clamp(math.floor(colour1[1] + (colour2[1] - colour1[1]) * abs(t)), 0, 255),
            clamp(math.floor(colour1[2] + (colour2[2] - colour1[2]) * abs(t)), 0, 255))

def interpolate_value(float1:float, float2:float, t:float):
    return float1 + (float2 - float1) * abs(t)

def interpolate_coordinate(coordinate1:tuple, coordinate2:tuple, t:float):
    return (math.floor(coordinate1[0] + (coordinate2[0] - coordinate1[0]) * abs(t)),
            math.floor(coordinate1[1] + (coordinate2[1] - coordinate1[1]) * abs(t)))
    


class Image(): # This is like a shitty fake version of pygame.Surface
    def __init__(self, resolution:tuple, pixelSize:tuple, colorspace:bool):
        self.resolution = resolution
        self.pixelSize = pixelSize
        self.colorspace = colorspace
        
        if colorspace:
            defaultPixel = (0, 0, 0)
        else:
            defaultPixel = 0.0

        self.contents = []
        for row in range(resolution[1]):
            self.contents.append([])
            for pixel in range(resolution[0]):
                self.contents[row].append(defaultPixel)

    def set_resolution(self, resolution:tuple):
        self.resolution = resolution

        self.contents = [[self.colorspace] * self.resolution[0]] * self.resolution[1]
    
    def get_resolution(self):
        return self.resolution
    
    def set_pixel_size(self, pixelSize:tuple):
        self.pixelSize = pixelSize

    def fill(self, value):
        for i in range(self.resolution[1]):
            for j in range(self.resolution[0]):
                self.contents[i][j] = value

    def draw_horizontal_line(self, 
                             x1:int, 
                             x2:int, 
                             y:int,
                             depthBuffer, 
                             depth1:float,
                             depth2:float, 
                             colour1:tuple=None, 
                             colour2:tuple=None,
                             **kwargs):
        texture = kwargs.get("texture", None) 

        uv1 = kwargs.get("uv1", None)
        uv2 = kwargs.get("uv2", None)

        lightCast = kwargs.get("lightCast", None)

        if 0 <= y < self.resolution[1]:
            lineLength = abs(x2 - x1)
            for i in range(x1, x2, 1 if x1 < x2 else -1):
                if 0 <= i < self.resolution[0]:
                    interpolationAmount = (i - x1) / lineLength
                    depth = interpolate_value(depth1, depth2, interpolationAmount)
                    
                    if depth <= depthBuffer.contents[y][i]:
                        if colour2:
                            pixelColour = interpolate_colour(colour1, colour2, interpolationAmount)
                            self.contents[y][i] = pixelColour
                            depthBuffer.contents[y][i] = depth
                        elif texture:
                            if lightCast:
                                self.contents[y][i] = overlay_colours(texture.get_colour_at(interpolate_coordinate(uv1, uv2, interpolationAmount)), lightCast)
                            else:
                                self.contents[y][i] = texture.get_colour_at(interpolate_coordinate(uv1, uv2, interpolationAmount))
                                
                            depthBuffer.contents[y][i] = depth
                        else:
                            self.contents[y][i] = colour1
                            depthBuffer.contents[y][i] = depth
                            
                            

    def draw_flat_based_triangle(self, 
                                 bottomLeft:tuple, 
                                 bottomRight:tuple, 
                                 point:tuple, 
                                 depthBuffer,
                                 depth1:float,
                                 depth2:float,
                                 depth3:float,
                                 colour1:tuple=None, 
                                 colour2:tuple=None, 
                                 colour3:tuple=None,
                                 **kwargs):
        texture = kwargs.get("texture", None) 

        uv1 = kwargs.get("uv1", None)
        uv2 = kwargs.get("uv2", None)
        uv3 = kwargs.get("uv3", None)

        lightCast = kwargs.get("lightCast", None)

        height = point[1] - bottomLeft[1]
        leftToPoint = bottomLeft[0] - point[0]
        rightToPoint = bottomRight[0] - point[0]
         
        for y in range(bottomLeft[1], point[1], 1 if height > 0 else -1):
            amountDone = abs((y - bottomLeft[1]) / height)

            left = math.floor(bottomLeft[0] - (leftToPoint * amountDone))
            right = math.floor(bottomRight[0] - (rightToPoint * amountDone))
            
            leftDepth = interpolate_value(depth1, depth3, amountDone)
            rightDepth = interpolate_value(depth2, depth3, amountDone)

            if colour2:
                self.draw_horizontal_line(left, right, y, depthBuffer, leftDepth, rightDepth, 
                                        interpolate_colour(colour1, colour3, amountDone), 
                                        interpolate_colour(colour2, colour3, amountDone))
                
            elif texture:
                self.draw_horizontal_line(left, right, y, depthBuffer, leftDepth, rightDepth,
                                          texture=texture,
                                          uv1=interpolate_coordinate(uv1, uv3, amountDone),
                                          uv2=interpolate_coordinate(uv2, uv3, amountDone),
                                          lightCast=lightCast)
            else:
                self.draw_horizontal_line(left, right, y, depthBuffer, leftDepth, rightDepth, colour1)
                
                

    def draw_triangle(self, 
                      vertex1:tuple,
                      vertex2:tuple,
                      vertex3:tuple,
                      depthBuffer,
                      depth1:float,
                      depth2:float,
                      depth3:float,
                      colour1:tuple=None,
                      colour2:tuple=None,
                      colour3:tuple=None,
                      **kwargs):
        
        texture = kwargs.get("texture", None) 

        uv1 = kwargs.get("uv1", None)
        uv2 = kwargs.get("uv2", None)
        uv3 = kwargs.get("uv3", None)

        lightCast = kwargs.get("lightCast", None)

        # Find the middle vertex
        heights = [vertex1[1], vertex2[1], vertex3[1]]

        # Believe it or not, this is a sorting algorithm.
        if heights[0] > heights[1]:
            if heights[0] > heights[2]:
                if heights[1] > heights[2]:
                    vertices = [vertex1, vertex2, vertex3]
                    colours = [colour1, colour2, colour3]
                    depths = [depth1, depth2, depth3]
                    uvs = [uv1, uv2, uv3]
                else:
                    vertices = [vertex1, vertex3, vertex2]
                    colours = [colour1, colour3, colour2]
                    depths = [depth1, depth3, depth2]
                    uvs = [uv1, uv3, uv2]
            else:
                vertices = [vertex3, vertex1, vertex2]
                colours = [colour3, colour1, colour2]
                depths = [depth3, depth1, depth2]
                uvs = [uv3, uv1, uv2]
        else:
            if heights[0] < heights[2]:
                if heights[1] < heights[2]:
                    vertices = [vertex3, vertex2, vertex1]
                    colours = [colour3, colour2, colour1]
                    depths = [depth3, depth2, depth1]
                    uvs = [uv3, uv2, uv1]
                else:
                    vertices = [vertex2, vertex3, vertex1]
                    colours = [colour2, colour3, colour1]
                    depths = [depth2, depth3, depth1]
                    uvs = [uv2, uv3, uv1]
            else:
                vertices = [vertex2, vertex1, vertex3]
                colours = [colour2, colour1, colour3]
                depths = [depth2, depth1, depth3]
                uvs = [uv2, uv1, uv3]
                

        triangleHeight = vertices[0][1] - vertices[2][1]
        topToBottomHorizontal = vertices[0][0] - vertices[2][0]

        if triangleHeight > 0:
            sliceAmount = (vertices[1][1] - vertices[2][1]) / triangleHeight
        else:
            sliceAmount = 0
        
        sliceCoordinate = (math.floor(vertices[2][0] + (topToBottomHorizontal * (sliceAmount))), vertices[1][1])
        sliceDepth = interpolate_value(depths[0], depths[2], 1 - sliceAmount)
        
        if colour2:
            sliceColour = interpolate_colour(colours[0], colours[2], 1 - sliceAmount)

            self.draw_flat_based_triangle(vertices[1], sliceCoordinate, vertices[2], 
                                          depthBuffer, depths[1], sliceDepth, depths[2],
                                          colours[1], sliceColour, colours[2])
            self.draw_flat_based_triangle(vertices[1], sliceCoordinate, vertices[0], 
                                          depthBuffer, depths[1], sliceDepth, depths[0],
                                          colours[1], sliceColour, colours[0])
            
        elif texture:
            sliceUV = interpolate_coordinate(uvs[0], uvs[2], 1 - sliceAmount)

            self.draw_flat_based_triangle(vertices[1], sliceCoordinate, vertices[2], 
                                          depthBuffer, depths[1], sliceDepth, depths[2],
                                          texture=texture,
                                          uv1=uvs[1], uv2=sliceUV, uv3=uvs[2],
                                          lightCast=lightCast)
            self.draw_flat_based_triangle(vertices[1], sliceCoordinate, vertices[0], 
                                          depthBuffer, depths[1], sliceDepth, depths[0],
                                          texture=texture,
                                          uv1=uvs[1], uv2=sliceUV, uv3=uvs[0],
                                          lightCast=lightCast)
            
        else:
            self.draw_flat_based_triangle(vertices[1], sliceCoordinate, vertices[2], 
                                          depthBuffer, depths[1], sliceDepth, depths[2],
                                          colour1)
            self.draw_flat_based_triangle(vertices[1], sliceCoordinate, vertices[0],
                                          depthBuffer, depths[1], sliceDepth, depths[0],
                                          colour1)

    def render_image(self, target:pygame.Surface, position:tuple):
        for row in range(position[1], position[1] + self.resolution[1]):
            for pixel in range(position[0], position[0] + self.resolution[0]):
                pygame.draw.rect(target, 
                                 self.contents[row][pixel], 
                                 pygame.Rect((pixel * self.pixelSize[0], row * self.pixelSize[1]), self.pixelSize))

    def render_depthbuffer(self, target, position):
        for row in range(position[1], position[1] + self.resolution[1]):
            for pixel in range(position[0], position[0] + self.resolution[0]):
                pygame.draw.rect(target, 
                                 (clamp(self.contents[row][pixel] * 25, 0, 255), 
                                  clamp(self.contents[row][pixel] * 25, 0, 255),
                                  clamp(self.contents[row][pixel] * 25, 0, 255)),
                                 pygame.Rect((pixel * self.pixelSize[0], row * self.pixelSize[1]), self.pixelSize))



# This will be the colour display triangles get rendered to

DISPLAY = Image((128, 96), (5, 5), True)

displaySizeX = DISPLAY.resolution[0] / 2
displaySizeY = DISPLAY.resolution[1] / 2

# This stores the depth information of the scene, so we can
# check if a pixel should be behind another pixel already rendered.
DEPTHBUFFER = Image((128, 96), (5, 5), False)
