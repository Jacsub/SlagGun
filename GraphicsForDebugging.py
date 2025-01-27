# SLAY PHYSICS SIM AND TARGETING!!!!!! 👅👅👅👅

import pygame
import numpy
import time
from engine.tooth import *

origin = Abstract()
ROOT.add_child_relative(origin)

gun = Plane((1, 1), (255, 0, 0), False)
gun.set_distortion_relative(Matrix([[0.5, 0, 0],
                                 [0, 1, 0],
                                 [0, 0, 1]]))
origin.add_child_relative(gun)

viewer = Abstract(Matrix([[0],
                        [1],
                        [-3]]))
origin.add_child_relative(viewer)

camera = Camera(ORIGIN, I3, 70)
viewer.add_child_relative(camera)

# Process functions

def process_camera(inputs, frameDelta):

    # Define our speeds
    movementSpeed = 4
    lookSpeed = 2
    
    playerMovement = [[0],
                      [0],
                      [0]]

    # Turn the status of the movement inputs into a vector
    if inputs[pygame.K_w]:
        playerMovement[2] = [1]
    if inputs[pygame.K_s]:
        playerMovement[2] = [-1]

    if inputs[pygame.K_a]:
        playerMovement[0] = [-1]
    if inputs[pygame.K_d]:
        playerMovement[0] = [1]

    if inputs[pygame.K_SPACE]:
        playerMovement[1] = [1]
    if inputs[pygame.K_LSHIFT]:
        playerMovement[1] = [-1]

    # Move the player by the normalised version of that vector
    viewer.translate_relative(Matrix(playerMovement).set_magnitude(movementSpeed * frameDelta))
        
    # Do the same but for the camera pretty much
    if inputs[pygame.K_RIGHT]:
        viewer.rotate_euler_radians(0, lookSpeed * frameDelta, 0)
    if inputs[pygame.K_LEFT]:
        viewer.rotate_euler_radians(0, -lookSpeed * frameDelta, 0)

    if inputs[pygame.K_UP]:
        turnAmount = -lookSpeed * frameDelta
        camera.rotate_euler_radians(turnAmount, 0, 0)
        
        # This checks if the camera exceeded 90 degrees from facing forward, and moves it back if it has.
        if camera.get_distortion_relative().get_contents()[2][2] < 0:
            camera.rotate_euler_radians(-turnAmount, 0, 0)
            
    if inputs[pygame.K_DOWN]:
        turnAmount = lookSpeed * frameDelta
        camera.rotate_euler_radians(turnAmount, 0, 0)
        
        if camera.get_distortion_relative().get_contents()[2][2] < 0:
            camera.rotate_euler_radians(-turnAmount, 0, 0)

    camera.render()

# Main loop

frameDelta = 0

running = True

while running:
    startTime = time.time()

    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

    inputs = pygame.key.get_pressed()

    WINDOW.fill((0, 0, 0))
    process_camera(inputs, frameDelta)

    print("Running a frame!")

    frameDelta = time.time() - startTime

    pygame.display.flip()