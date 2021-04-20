# Copyright 2021 Ian Eborn
# A sub-class of the "SimpleThirdPersonCamera" class, providing one implementaton of
# the collision-related elements of the camera-system.
#
# Specifically, this class primarily implements the "setupCollision" and "getNearestCollision" methods,
# using Panda3D's built-in collision system.

# Panda3D importations
from panda3d.core import CollisionNode, CollisionTraverser, CollisionHandlerQueue, CollisionSegment

# Import the base-class
from SimpleThirdPersonCamera import *

# The class that implements our camera-controller
class SimpleThirdPersonCameraPandaCollision(SimpleThirdPersonCamera):
    def __init__(self, tilt, intendedDistance, shoulderSideDistance, height,
                 adjustmentSpeed, sideSwitchSpeed,
                 initialShoulderSide,
                 ownerNodePath,
                 camera,
                 colliderRadius = 1):

        # This should be set before initialising the super-class, as
        # it will be used in "setupCollision" (below), which is called
        # by the super-class's constructor-method.
        self.colliderRadius = colliderRadius

        SimpleThirdPersonCamera.__init__(self, tilt, intendedDistance, shoulderSideDistance, height,
                                         adjustmentSpeed, sideSwitchSpeed,
                                         initialShoulderSide,
                                         ownerNodePath,
                                         camera)

    # Build the collision-related elements that inform the camera's behaviour
    #
    # This implementation uses Panda's built-in collision-system
    def setupCollision(self):
        # A traverser, which enacts the actual collision-detection
        self.traverser = CollisionTraverser()

        # We'll use a queue, since we only want the nearest collision in a given update
        self.collisionQueue = CollisionHandlerQueue()

        # Our collision-objects: four segments, extending backwards for the "intended distance".
        self.colliderNode = CollisionNode("camera collider")
        self.colliderNode.addSolid(CollisionSegment(-self.colliderRadius, -self.colliderRadius, 0,
                                                    -self.colliderRadius, -self.intendedDistance, 0))
        self.colliderNode.addSolid(CollisionSegment(self.colliderRadius, -self.colliderRadius, 0,
                                                    self.colliderRadius, -self.intendedDistance, 0))
        self.colliderNode.addSolid(CollisionSegment(0, -self.colliderRadius, -self.colliderRadius,
                                                    0, -self.intendedDistance, -self.colliderRadius))
        self.colliderNode.addSolid(CollisionSegment(0, -self.colliderRadius, self.colliderRadius,
                                                    0, -self.intendedDistance, self.colliderRadius))

        self.colliderNode.setIntoCollideMask(0)
        self.colliderNode.setFromCollideMask(1)

        self.collider = self.cameraBase.attachNewNode(self.colliderNode)

        # Add our collision -objects and -handler to our traverser
        self.traverser.addCollider(self.collider, self.collisionQueue)

    # Check for a collision relevant to the camera
    #
    # This implementation uses Panda's built-in collision-system
    def getNearestCollision(self, sceneRoot):
        # Ask the traverser to check for collisions
        self.traverser.traverse(sceneRoot)

        # If there have been any collisions...
        if self.collisionQueue.getNumEntries() > 0:

            # Sort the collision-entries, which orders them from
            # nearest to furthest, I believe.
            self.collisionQueue.sortEntries()

            # Then get the first--i.e. nearest--of them.
            entry = self.collisionQueue.getEntry(0)

            # Now, use the collision-position to determine how far away the
            # collision occurred from the camera's base-position, and return that.
            pos = entry.getSurfacePoint(sceneRoot)
            diff = self.cameraBase.getPos(sceneRoot) - pos

            return diff.length()

        # In there were no collisions, just return the "intended distance"
        return self.intendedDistance

    # A method to clean up the controller's collision elements
    def cleanupCollision(self):
        if self.collider is not None:
            self.traverser.removeCollider(self.collider)
            self.collider.removeNode()
            self.collider = None
            self.colliderNode = None

        self.traverser = None
        self.collisionQueue = None