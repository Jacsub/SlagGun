from engine.clamp import *
from engine.matrix import *
from engine.abstract import *

GRAVFIELDSTRENGTH = 9.81 # The strength of the scene's gravitational field 
                         # measured in Newtons per kilogram (NKg^-1)

                         # It's also the acceleration things will fall at in units per second per second (ms^-2)

                         # It's named like a constant but you're free to change it if you want

GRAVDIRECTION = Matrix([[0],  # This is the direction gravity points in as a vector. You probably won't need to
                        [-1], # change this unless it's for a game mechanic
                        [0]])



class SphereCollider(Abstract):
    def __init__(self, radius:float, body:Abstract=None, location:Matrix=None, distortion:Matrix=None, tags:list[str]=None):
        super().__init__(location, distortion, tags)

        self.radius = radius

        if body:
            self.body = body
            body.set_collider(self)
        else:
            self.body = None

        self.intersectionMethods = {
            SphereCollider : self.intersect_sphere, 
            PlaneCollider : self.intersect_plane
        }

        self.collisionNormalMethods = {
            SphereCollider : self.get_collision_normal_sphere,
            PlaneCollider : self.get_collision_normal_plane
        }

    def intersect_sphere(self, sphere:Abstract, collide:bool=False):
        difference = sphere.objectiveLocation.subtract(self.objectiveLocation)

        if difference.get_magnitude() < self.radius + sphere.radius:
            if collide:
                if sphere.body.dynamic:
                    if self.body.dynamic:
                        sphere.body.set_location_objective(sphere.body.objectiveLocation.add(difference.multiply_scalar(0.5)))
                        self.body.set_location_objective(self.body.objectiveLocation.subtract(difference.multiply_scalar(0.5)))

                    else:
                        sphere.body.set_location_objective(sphere.body.objectiveLocation.add(difference))

                else:
                    if self.body.dynamic:
                        self.body.set_location_objective(self.body.objectiveLocation.subtract(difference))
                    
            return True

        return False
    
    def intersect_plane(self, plane:Abstract, collide:bool=False):
        relativeToPlane = plane.objectiveDistortion.get_3x3_inverse().apply(self.objectiveLocation.subtract(plane.objectiveLocation)).get_contents()

        if (abs(relativeToPlane[0][0]) < plane.width / 2 and 
                relativeToPlane[1][0] < self.radius and 
                abs(relativeToPlane[2][0]) < plane.length / 2):
            
            if collide and self.body.dynamic:
                difference = Matrix([[0], 
                                     [self.radius - relativeToPlane[1][0]],
                                     [0]]) 
                
                objectiveDifference = plane.body.objectiveDistortion.apply(difference)
                
                self.body.translate_objective(objectiveDifference) # Now the sphere is no longer intersecting the plane

            return True
        
        return False
    
    def intersect(self, collider:Abstract, collide:bool=False):
        return self.intersectionMethods[type(collider)](collider, collide)
    

    
    def get_collision_normal_sphere(self, sphere):
        direction = self.objectiveLocation.subtract(sphere.objectiveLocation)

        try:
            return direction.set_magnitude(1) # This just makes its magnitude 1
        except:
            return ORIGIN
        
    def get_collision_normal_plane(self, plane):
        direction = plane.objectiveDistortion.apply(Matrix([[0],
                                              [1],
                                              [0]]))
        
        return direction.set_magnitude(1)
    
    def get_collision_normal(self, collider):
        return self.collisionNormalMethods[type(collider)](collider)
    

    
class PlaneCollider(Abstract):
    def __init__(self, width:float, length:float, body:Abstract=None, location:Matrix=None, distortion:Matrix=None, tags:list[str]=None):
        super().__init__(location, distortion, tags)

        self.length = length
        self.width = width

        if body:
            self.body = body
            body.set_collider(self)
        else:
            self.body = None

        self.intersectionMethods = {
            SphereCollider : self.intersect_sphere, 
            PlaneCollider : self.intersect_plane
        }

        self.collisionNormalMethods = {
            SphereCollider : self.get_collision_normal_sphere, 
            PlaneCollider : self.get_collision_normal_plane
        }



    def intersect_sphere(self, sphere:Abstract, collide:bool=False):
        relativeToPlane = self.objectiveDistortion.get_3x3_inverse().apply(sphere.objectiveLocation.subtract(self.objectiveLocation)).get_contents()

        if (abs(relativeToPlane[0][0]) < self.width / 2 and 
                relativeToPlane[1][0] < sphere.radius and 
                abs(relativeToPlane[2][0]) < self.length / 2):
            
            if collide and sphere.body.dynamic:
                difference = Matrix([[0], 
                                     [sphere.radius - relativeToPlane[1][0]],
                                     [0]]) 
                objectiveDifference = self.body.objectiveDistortion.apply(difference)
                
                sphere.body.translate_objective(objectiveDifference) # Now the sphere is no longer intersecting the plane

            return True
        
        return False
    
    def intersect_plane(self, plane:Abstract, collide:bool=False):
        return False
    
    def intersect(self, collider:Abstract, collide:bool=False):
        #print(f"Collider: {collider}")
        return self.intersectionMethods[type(collider)](collider, collide)
    


    def get_collision_normal_sphere(self, sphere):
        direction = self.objectiveDistortion.apply(Matrix([[0],
                                                            [1],
                                                            [0]]))
        
        return direction.set_magnitude(-1)
        
    def get_collision_normal_plane(self, plane):
        return ORIGIN
    
    def get_collision_normal(self, collider):
        return self.collisionNormalMethods[type(collider)](collider)



class Body(Abstract):
    def __init__(self,  
                 mass:float, 
                 bounciness:float=None,
                 roughness:float=None,
                 dynamic:bool=None, 
                 location:Matrix=None,
                 distortion:Matrix=None, 
                 collider:Abstract=None,
                 velocity:Matrix=None,
                 tags:list[str]=None, 
                 gravityDirection:Matrix=None):
        super().__init__(location, distortion, tags)

        self.mass = mass
        self.bounciness = bounciness if bounciness is not None else 0
        self.roughness = roughness if roughness is not None else 10

        self.dynamic = dynamic if dynamic is not None else True

        self.oldObjectiveLocation = self.objectiveLocation # We store this so we can figure out how fast something's
                                                                # moved even when it's been translated through code

        if collider:
            self.collider = collider
            self.set_collider(collider)
        else:
            self.collider = None
        
        self.velocity = velocity if velocity else ORIGIN # A 3D collumb vector measured in units per second (ms^

        self.forces = []

        self.gravityDirection = gravityDirection if gravityDirection else GRAVDIRECTION

    def set_collider(self, collider:Abstract):
        self.collider = collider
        self.add_child_relative(collider)

    def add_force(self, force:Matrix):
        self.forces.append(force)

    def clear_forces(self):
        self.forces.clear()

    def apply_forces(self, frameDelta:float):
        if self.dynamic:
            #print(f"Applying forces to {self.tags}")
            #print(f"{self.tags}'s velocity is {self.velocity}")
            resultantForce = ORIGIN

            for force in self.forces:
                resultantForce = resultantForce.add(force)

            # Process acceleration using F = ma

            # a = F /
            #     m
            if frameDelta > 0:
                acceleration = resultantForce.multiply_scalar(1 / self.mass)

                # Process velocity using v = u + at
                self.velocity = self.velocity.add(acceleration.multiply_scalar(frameDelta))

                # Translate according to velocity
                self.translate_objective(self.velocity.multiply_scalar(frameDelta))
        else:
            # If it's kinematic, we can just say it's velocity is its change in position since the last frame over the frame delta
            self.velocity = self.objectiveLocation.subtract(self.oldObjectiveLocation).multiply_scalar(1 / frameDelta)
            self.oldObjectiveLocation = self.objectiveLocation

        self.clear_forces()



def process_bodies(frameDelta):
    bodies = ROOT.get_substracts_of_type(Body)

    bodiesToCheck = []

    for body in bodies:
        bodiesToCheck.append(body) # I had to do this otherwise they'd just be the same list

    if frameDelta > 0:
        for i in range(len(bodies)):
            body = bodiesToCheck.pop(0)
                
            if body.collider:

                if body.dynamic:
                    body.add_force(body.gravityDirection.set_magnitude(GRAVFIELDSTRENGTH * body.mass))

                    for otherBody in bodiesToCheck:
                        
                        if body.collider.intersect(otherBody.collider, True):
                            
                            # Here, we figure out the forces each body experiences.

                            # Newton's law of restitution says momentum (mass * velocity) is conserved:

                            # m1u1 + m2u2 = m1v1 + m2v2

                            # We also know that the coefficient of restitution is the speed of separation
                            # divided by the speed of approach:

                            # e = v1 - v2 /
                            #     u2 - u1

                            # We can figure out e by finding the midpoint between both body's bounciness
                            # levels, and we already have u1 and u2. From this, we can solve for v1 and v2

                            # e(u2 - u1) = v1 - v2


                            # - For v1:

                            # v2 = v1 - e(u2 - u1)

                            # m1u1 + m2u2 = m1v1 + m2(v1 - e(u2-u1))

                            #             = m1v1 + m2v1 - m2 * e(u2-u1)

                            #             = v1(m1 + m2) - m2 * e(u2-u1)

                            # m1u1 + m2u2 + m2 * e(u2-u1) / 
                            #          m1 + m2               = v1

                            # (then just multiply by mass again to find momentum)


                            # Now we know v1, we can just use that to find m2v2

                            # m1u1 + m2u2 = m1v1 + m2v2

                            # m1u1 + m2u2 - m1v1 = m2v2


                            # If you're still alive after reading that algebra, then we've just found
                            # the final momentums of both bodies! Because force is just the rate of 
                            # change of momentum (impulse over time), we can find the force applied by
                            # dividing the change in momentum by our frame delta.

                            collisionNormal = body.collider.get_collision_normal(otherBody.collider)

                            e = (body.bounciness + otherBody.bounciness) / 2

                            m1 = body.mass
                            m2 = otherBody.mass

                            u1 = body.velocity.get_dot_product(collisionNormal)
                            u2 = otherBody.velocity.get_dot_product(collisionNormal)

                            if otherBody.dynamic:
                                # Calculate impulse on body
                                v1 = ((m1 * u1) + (m2 * u2) + (m2 * e * (u2 - u1)) /
                                                        (m1 + m2))

                                bodyImpulse = collisionNormal.multiply_scalar((m1 * v1) - (m1 * u1))

                                body.add_force(bodyImpulse.multiply_scalar(1 / frameDelta))

                                # Calculate impulse on the other body
                                otherMomentum = (m1 * u1) + (m2 * u2) - (m1 * v1)

                                otherImpulse = collisionNormal.multiply_scalar(otherMomentum - (m2 * u2))

                                otherBody.add_force(otherImpulse.multiply_scalar(1 / frameDelta))

                            else:
                                # Here, we already know the other body's velocity, which simplifiys our calculations a bit.

                                # m1u1 + m2u2 = m1v1 + m2v2

                                # e = v1 - v2/ 
                                #     u2 - u1

                                # We know e, u1, u2 and v2, so:

                                # e(u2 - u1) + v2 = v1

                                # m1v1 = m1(e(u2 - u1) + v2)

                                v2 = otherBody.velocity.get_dot_product(collisionNormal)

                                bodyMomentum = m1 * (e * (u2 - u1) + v2)

                                bodyImpulse = collisionNormal.multiply_scalar(bodyMomentum - (m1 * u1))

                                body.add_force(bodyImpulse.multiply_scalar(1 / frameDelta))

                            # Now we've sorted out exchange of momentum, we need to apply friction.

                            # We just need to find the component not parallel to the surface, and apply a force 
                            # opposing it.

                            # The magnitude of this force is whichever's smaller:

                            # The force pushing the particle, or the object's limiting friction.

                            limitingFriction = (body.roughness + otherBody.roughness) / 2
                            
                            # This is the direction opposing the body's movement parallel to the collision surface
                            bodyOpposingForce = body.velocity.subtract(collisionNormal.multiply_scalar(u1)).multiply_scalar(-limitingFriction * m1)

                            body.add_force(bodyOpposingForce)
                            
                            otherBodyOpposingForce = otherBody.velocity.subtract(collisionNormal.multiply_scalar(u2)).multiply_scalar(-limitingFriction * m2)

                            otherBody.add_force(otherBodyOpposingForce)


                            
                else:
                    for otherBody in bodies:
                        if body.collider.intersect(otherBody.collider, True):

                            collisionNormal = body.collider.get_collision_normal(otherBody.collider)

                            e = (body.bounciness + otherBody.bounciness) / 2

                            m1 = body.mass
                            m2 = otherBody.mass

                            u1 = body.velocity.get_dot_product(collisionNormal)
                            u2 = otherBody.velocity.get_dot_product(collisionNormal)

                            if otherBody.dynamic:
                                # This is almost exactly the same as above, just rearranged a bit differently

                                # m1u1 + m2u2 = m1v1 + m2v2

                                # e = v1 - v2/ 
                                #     u2 - u1

                                # We know e, u1, u2 and v2, so:

                                # v1 - e(u2 - u1) = v2

                                # m2v2 = m2(v1 - e(u2 - u1))
                                
                                v1 = body.velocity.get_dot_product(collisionNormal)

                                otherMomentum = m2 * (v1 - e * (u2 - u1))

                                otherImpulse = collisionNormal.multiply_scalar(otherMomentum - (m2 * u2))

                                otherBody.add_force(otherImpulse.multiply_scalar(1 / frameDelta))

                        
                            # Now we've sorted out exchange of momentum, we need to apply friction.

                            # We just need to find the component not parallel to the surface, and apply a force 
                            # opposing it.

                            # The magnitude of this force is whichever's smaller:

                            # The force pushing the particle, or the object's limiting friction.

                            friction = (body.roughness + otherBody.roughness) / 2
                            
                            # This is the direction opposing the body's movement parallel to the collision surface
                            bodyOpposingForce = body.velocity.subtract(collisionNormal.multiply_scalar(u1)).multiply_scalar(-friction * m1)

                            # As you can see, this isn't an accurate simulation of friction. But it's close enough!
                            body.add_force(bodyOpposingForce)
                            
                            otherBodyOpposingForce = otherBody.velocity.subtract(collisionNormal.multiply_scalar(u2)).multiply_scalar(-friction * m2)

                            otherBody.add_force(otherBodyOpposingForce)
                
            else:
                print(f"{body.tags} doesn't have a collider!")
                    
        for body in bodies:
            body.apply_forces(frameDelta)