import pygame

from engine.clamp import *
from engine.matrix import *
from engine.abstract import *

HEADSHADOWAMOUNT = 0.7 # When you're pointed 90 degrees from something making a sound,
                       # you'll hear it at a normal volume in your ear closest to the sound.
                       # However, for your other ear, your head's in the way; so it sounds quieter.

                       # This is called the head shadow effect.

                       # This constant is how much quieter sound is to the further ear compared to 
                       # the closer one.



class SoundEffect(Abstract):
    def __init__(self, 
                 sound:str, 
                 volume:float=None, 
                 location:Matrix=None, 
                 distortion:Matrix=None, 
                 tags:list[str]=None):
        
        super().__init__(location, distortion, tags)

        self.sound = pygame.mixer.Sound(sound)
        self.channel = None
        self.volume = volume if volume else 1

    def play(self, loops:int=None):
        self.sound.stop()
        self.channel = pygame.mixer.find_channel(True)
        self.sound.play(loops if loops else 0)
    
    def stop(self):
        self.channel = None
        self.sound.stop()



class Listener(Abstract):
    def __init__(self, 
                 volume:float, 
                 sensitivity:float=None, 
                 location:Matrix=None, 
                 distortion:Matrix=None, 
                 tags:list[str]=None):
        
        super().__init__(location, distortion, tags)

        self.volume = volume
        self.sensitivity = sensitivity if sensitivity else 1 # This scales how quiet things get with distance
                                                             # A sensitivity of 2 means you need to move twice
                                                             # the distance away from something to make it as quiet
                                                             # as it would be at 1

    def listen(self):
        sounds = ROOT.get_substracts_of_type(SoundEffect)

        inversion = self.objectiveDistortion.get_3x3_inverse()

        for sound in sounds:
            if sound.channel:
                channel = sound.channel

                differenceVector = sound.objectiveLocation.subtract(self.objectiveLocation)
                distance = differenceVector.get_magnitude()
                directionVector = inversion.apply(differenceVector)

                # Calculate the angle both "ears" are at to the sound

                # Mathmatically, that's finding the angle between the Listener's x axis and the vector from the listener to the sound

                # We can use the dot product to figure this out:

                #  cos^1 ( a . b /
                #          |a||b| ) = angle between two vectors

                # I'm actually not going to cos it tho, cause it's a lot more useful to have a number between 1 and 0 here

                dotProduct = directionVector.get_contents()[0][0]

                # Because the x axis is just 1, 0, 0, the dot product is just the x component.

                angle = -dotProduct / distance

                # The magnitude of the x axis is 1, and we calculated the other magnitude earlier so we can just use that.

                baseVolume = clamp(self.volume * sound.volume * (1 / ((distance / self.sensitivity) ** 2)), 0, sound.volume)

                # Now we're just quieting the further ear.
                if directionVector.get_contents()[0][0] > 0:
                    channel.set_volume(baseVolume * (1 - (-angle * HEADSHADOWAMOUNT)), baseVolume)
                else:
                    channel.set_volume(baseVolume, baseVolume * (1 - (angle * HEADSHADOWAMOUNT)))
