from engine.matrix import *

class Abstract:
    def __init__(self, 
                 location:Matrix=None, 
                 distortion:Matrix=None, 
                 tags:list[str]=None): # I'm well aware this is clapped. 
        
                             # Unfortunately for people unlucky enough to see this, default values in Python
                             # are created at the definition of the function, instead of when it's called. 
                
                             # This means if I assign default values in the parameter list, EVERY abstract 
                             # that uses those default values will then share those parameters, even when I 
                             # change them.
                             
                             # Guess how long it took to find that out while debugging.
        
        
            
        # Just to clarify, the locations and distortions are all stored in objective space.
        
        # If you're wondering why I don't just store the relative locations, it's
        # becasue I tried it and it was slow.
            
        # In every raster cycle, you need to find the positions of every vertex
        # relative to the camera. With objective coordinates being stored, you
        # just have to read those from memory and compare them. However, with
        # relative coordinates I had to make a recursive function which
        # would spend four million years every frame traversing all the way up
        # the scene tree to the objective origin doing matrix applications for
        # each link.
        
        # While storing it like this makes it harder to find local coordinates,
        # you only need to compare the current abstract with its superstract
        # to find them, whereas finding objective coordinates with stored 
        # coordinates in local space requires analysing the entire scene tree.

        self.parent = None # You used to be able to define these at initialisation but I literally never used it
        self.children = []
        
        self.objectiveLocation = location if location else ORIGIN
        self.objectiveDistortion = distortion if distortion else I3     # I hate If Expressions too if that's any consolation
        
                                                                        # Sorry, I mean
                                                                        
                                                                        # if that's any consolation:
                                                                        #     I hate If Expressions too
        
        self.tags = tags if tags else []
        
        
        
    def get_tags(self):
        return self.tags
    
    def add_tag(self, tag:str):
        self.tags.append(tag)
    
    def remove_tag(self, tag:str):
        self.tags.remove(tag)
        
    def check_for_tag(self, tag:str):
        return tag in self.tags
    
    def get_children_with_tag(self, tag:str):
        found = []
        for child in self.children:
            if child.check_for_tag(tag):
                found.append(child)
        
        return found
    
    def get_substracts_with_tag(self, tag:str):
        found = []
        for child in self.children:
            if child.check_for_tag(tag):
                found.append(child)
                
            found += child.get_substracts_with_tag(tag)
            
        return found
        
    
    
    def get_type(self):
        return self.__class__
    
    def get_children_of_type(self, type): # Children are the abstracts directly underneath an abstract
        found = []
        for child in self.children:
            if child.__class__ == type:
                found.append(child)

        return found
    
    def get_substracts_of_type(self, type): # Substracts are all abstracts underneath an abstract,
        found = []                          # meaning its children, its children's children, etc.
        for child in self.children:
            if child.__class__ == type:     # The same applies to parents and superstracts;
                found.append(child)         # parents are directly above, superstracts are everything
                                            # above
            found += child.get_substracts_of_type(type)
            
        return found
        
        
    # Heirachy functions
        
    def get_parent(self):
        return self.parent
    
    def set_parent(self, newParent):
        if self.parent:
            self.parent.children.remove(self)
        self.parent = newParent
            
        if not self in newParent.children:
            newParent.children.append(self)
        
        
        
    def get_children(self):
        return self.children
    
    def add_child_relative(self, newChild):
        if newChild.parent:
            newChild.parent.children.remove(newChild)
        newChild.parent = self

        newChild.set_location_relative(newChild.objectiveLocation)
        newChild.set_distortion_relative(newChild.objectiveDistortion)
        
        if not newChild in self.children:
            self.children.append(newChild)
        
    def remove_child(self, child):
        if self.parent:
            child.parent = self.parent
        else:
            return
            
        self.children.remove(child)

        self.parent.children.append(child)
        
        

    def kill_self(self): # This is figurative and does not need to be shown to Pastoral
        if self.parent:
            for child in self.children:
                child.parent = self.parent

            self.parent.remove_child(self)  
            
            del self
        else:
            print("Why are you trying to delete the origin? Not cool man")

    def kill_self_and_substracts(self): # Neither does this
        if self.children:
            for child in self.children:
                child.delete_self_and_substracts()
        
        if self.parent:
            self.parent.children.remove(self)
            del self

    

    # Transform functionsDO NOT TOUCH EVER!!!!!!!!!!!11🚫🚫🚫🚫🚫🚫🚫🚫
    # ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔☣️☣️☣️☣️☣️☣️☣️☣️☣️☣️☣️
    # ☠️☠️☠️☠️☠️☠️☠️☠️☠️☠️☠️☠️☠️☠️☠️☠️☠️
    # THIS TOOK FOUR ENTIRE DAYS TO DEBUG THE LAST TIME IT BROKE

    # Location functions 

    # Objective

    def get_location_objective(self):
        return self.objectiveLocation

    def set_location_objective(self, location:Matrix):
        vector = location.subtract(self.objectiveLocation)

        self.objectiveLocation = location

        for child in self.get_children():
            child.translate_objective(vector)
    
    def translate_objective(self, vector:Matrix):
        self.objectiveLocation = self.objectiveLocation.add(vector)

        for child in self.get_children():
            child.translate_objective(vector)

    # Relative

    def get_location_relative(self):
        if self.parent:
            return self.parent.objectiveDistortion.get_3x3_inverse().apply(self.objectiveLocation.subtract(self.parent.objectiveLocation))
            # This subtracts the parent's location to move the origin to the parent, and then reverses the
            # parent's distortion to get the relative coordinate
        else:
            return self.objectiveLocation
            # If it has no parent, it must be the root, so we just have to find it's objective location

    def set_location_relative(self, location:Matrix):
        if self.parent:
            self.set_location_objective(self.parent.objectiveDistortion.apply(location).add(self.parent.objectiveLocation))
            # This starts by distorting the location to make it relative to the parent's axes, and then
            # moves it from the objective origin to the parent
        else:
            self.set_location_objective(location)

    def translate_relative(self, vector:Matrix):
        if self.parent:
            self.translate_objective(self.objectiveDistortion.apply(vector))
            # We only need to apply the distortion here, because vector is just a 
            # direction and a magnitude instead of being a point in space
        else:
            self.translate_objective(vector)



    # Distortion functions (I've spent four days and counting debugging these)

    # Objective

    def get_distoriton_objective(self):
        return self.objectiveDistortion
        
    def set_distortion_objective(self, distortion:Matrix, pivot:Matrix=None):
        distortionPivot = pivot if pivot else self.objectiveLocation

        transformation = distortion.apply(self.objectiveDistortion.get_3x3_inverse())

        # That's the distortion matrix you have to apply to skew the current distortion
        # to the target one. This works because:

        # [transformation][currentDistortion] has to equal [targetDistortion]    <--------------------------------
        #                                                                                                        |
        # We can apply the inverse of the current distortion on the right                                        |
        # of both sides of the equation without making it invalid                                                |          This stupid arrow
        #                                                                                                        |          took longer to make than
        # [transformation][currentDistortion][currentDistortion]^-1 = [targetDistortion][currentDistortion]^-1   |          everything else in this 
        #                                                                                                        |          explanation
        # Then [currentDistortion][currentDistortion]^-1 cancel out to make I3, which doesn't change             |          
        # matrices when it's applied to them.                                                                    |
        #                                                                                                        |
        # Therefore ----------------------------------------------------------------------------------------------

        self.objectiveDistortion = distortion
        self.objectiveLocation = transformation.apply(self.objectiveLocation.subtract(distortionPivot)).add(distortionPivot)

        # That last line changed the abstract's location to move it round the pivot point.
        # Most of the time you won't need a pivot, but it's used when this recurrs over
        # an abstract's substracts.

        # That worked because:

        # Applying a transformation matrix to a point transforms it relative to the origin.

        # |                   /
        # |    x      --->   /    x
        # |                 /
        # +--------        /-------- 

        # Therefore, if we want to transform around a pivot thats' not the origin,
        # we can subtract the location of a pivot from the point's location
        # so the new location of the point is what it's location relative to the 
        # pivot was.

        # |     x                                           |          
        # |          subtract location of p from everything | x        Now p is
        # |   p                        --->                 |          the origin.
        # +--------                                         p--------

        # *Now* we can apply our transformation, because we've effectively mored the
        # origin to the pivot. Then, we just move the origin back by adding the
        # pivot's location back to everything.

        for child in self.children:
            child.distort_objective(transformation, distortionPivot) # This makes all the substracts
                                                           # move to keep their relative
                                                           # transforms

    def distort_objective(self, transformation:Matrix, pivot:Matrix=None):
        distortionPivot = pivot if pivot else self.objectiveLocation

        self.objectiveDistortion = transformation.apply(self.objectiveDistortion)
        self.objectiveLocation = transformation.apply(self.objectiveLocation.subtract(distortionPivot)).add(distortionPivot)

        for child in self.children:
            child.distort_objective(transformation, distortionPivot)

    # Relative

    def get_distortion_relative(self):
        if self.parent:
            return self.parent.objectiveDistortion.get_3x3_inverse().apply(self.objectiveDistortion)
            # Here we just undo the parent's distortion
        else:
            return self.objectiveDistortion
        
    def set_distortion_relative(self, distortion):
        if self.parent:
            self.set_distortion_objective(self.parent.objectiveDistortion.apply(distortion))
        else:
            self.set_distortion_objective(distortion)

    def distort_relative(self, transformation):
        if self.parent:
            self.distort_objective(self.parent.objectiveDistortion.apply(transformation).apply(self.parent.objectiveDistortion.get_3x3_inverse()))
            # We need to appply the inverse at the end of this function but *not* set_distortion_relative
            # becasue reasons. I'll be entirely honest idk why I just applied the inverse on a whim while
            # bug fixing and it worked but it messed up set_distortion_relative when I put it on there

            # I think it's something do with how transformation is a difference and it isn't relative to 
            # actual points?
        else:
            self.distort_objective(transformation)
    


    # Rotation functions
        
    def rotate_euler_radians(self, x:float, y:float, z:float): # This follows the order yxz
        sinx = math.sin(x)
        cosx = math.cos(x)
        siny = math.sin(y)
        cosy = math.cos(y)
        sinz = math.sin(z)
        cosz = math.cos(z)
        
        rotationMatrix = Matrix([[cosz, -sinz, 0], # This is wrong, fix later
                                 [sinz, cosz, 0],
                                 [0, 0, 1]]).apply(
                         
                         Matrix([[1, 0, 0],
                                 [0, cosx, -sinx],
                                 [0, sinx, cosx]])).apply(
                                     
                         Matrix([[cosy, 0, siny],
                                 [0, 1, 0],
                                 [-siny, 0, cosy]]))
        
        self.distort_relative(rotationMatrix) # Change back to relative when it's fixed
        

# This is the head of our heirachy

ROOT = Abstract()