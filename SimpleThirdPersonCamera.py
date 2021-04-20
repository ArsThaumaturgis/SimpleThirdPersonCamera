# Copyright 2021 Ian Eborn
# A simple controller for a third-person camera
#
# This is a base-class, intended to be sub-classed. In particular, it doesn't implement the collision-related
# matters that inform the camera's behaviour.

# A Panda-related importation
from panda3d.core import PandaNode

# Some constants describing the position of the camera:
#  - Beside the left shoulder
#  - Centred on the character
#  - And beside the right shoulder
#
# There are two copies of the "centre" option, allowing for both
# American and British spellings.
SIMPLE_THIRD_PERSON_CAMERA_SIDE_LEFT = -1
SIMPLE_THIRD_PERSON_CAMERA_SIDE_CENTRE = 0
SIMPLE_THIRD_PERSON_CAMERA_SIDE_CENTER = 0
SIMPLE_THIRD_PERSON_CAMERA_SIDE_RIGHT = 1

# The base-class itself
class SimpleThirdPersonCamera():
    def __init__(self, tilt, intendedDistance, shoulderSideDistance, height,
                 adjustmentSpeed, sideSwitchSpeed,
                 initialShoulderSide,
                 ownerNodePath,
                 camera):
        # Store our data, in case we want it later
        #
        # Note that we >don't< store the owner's node-path!
        # This is because keeping a reference to that, which
        # will be keeping a reference to this object, could
        # result in a circular reference, which can in turn
        # confuse the garbage-collector. It's not insurmountable
        # by any means, but I'm disinclined to incur that issue
        # without good reason
        #
        # Be aware too that this class doesn't take ownership of the
        # "camera" and "ownerNodePath"--it's assumed that those will
        # be cleaned up as called for by other code.
        self.camera = camera
        self.ownerNodePath = ownerNodePath
        self.shoulderSideDistance = shoulderSideDistance
        self.intendedDistance = intendedDistance
        self.height = height
        self.tilt = tilt
        self.sideSwitchSpeed = sideSwitchSpeed
        self.adjustmentSpeed = adjustmentSpeed

        # The node-structure of the camera-controller:
        # A base, which is positioned either to the left, centre, or right of the owner,
        # and to which the "tilt" is applied; and a "holder", which handles the camera's
        # retreat from obstacles and recovery when there are none
        self.cameraBase = ownerNodePath.attachNewNode(PandaNode("third-person camera-base"))
        self.cameraHolder = self.cameraBase.attachNewNode(PandaNode("third-person camera-holder"))
        camera.reparentTo(self.cameraHolder)

        self.cameraBase.setZ(height)
        self.cameraBase.setP(tilt)
        self.cameraHolder.setY(-intendedDistance)

        # Setup the collision used by the controller--however the relevant sub-class
        # may have implemented that
        self.setupCollision()

        # Initialise the lateral placement of the camera
        self.currentSide = SIMPLE_THIRD_PERSON_CAMERA_SIDE_CENTRE
        self.setCurrentSide(initialShoulderSide)

    # Build the collision-related elements that inform the camera's behaviour
    #
    # Stub, intended to be overridden
    def setupCollision(self):
        pass

    # Check for a collision relevant to the camera
    #
    # Stub, intended to be overridden
    # Should return a distance from the camera-holder; if no collision
    # is found, it should return "self.intendedDistance"
    def getNearestCollision(self, sceneRoot):
        pass

    # Set the lateral position of the camera
    def setCurrentSide(self, side):
        self.currentSide = side

    # Update the camera's state
    def update(self, dt, sceneRoot):
        # Determine how far out the camera is placed at the moment
        currentDistance = abs(self.cameraHolder.getY())

        # Determine where it should be:

        # Default to the assumption that it should be at the "intended distance"
        targetY = self.intendedDistance

        # Check for camera-relevant collisions, and update the "targetY" if called for
        collisionDistance = self.getNearestCollision(sceneRoot)
        if targetY > collisionDistance:
            targetY = collisionDistance

        # Compare the current placement with the target
        yDiff = targetY - currentDistance

        # Update the camera's position based on that "yDiff"
        #
        # The "> 1" section prevents overly-large delta-times from
        # producing overly-large movements
        offsetVal = self.adjustmentSpeed*dt
        if offsetVal > 1:
            offsetVal = 1
        offset = yDiff*offsetVal
        self.cameraHolder.setY(-currentDistance -offset)

        # Update the camera's lateral placement
        #
        # This is similar to the above, but lateral

        currentSideDistance = self.cameraBase.getX()

        sideDiff = self.shoulderSideDistance*self.currentSide - currentSideDistance
        if abs(sideDiff) < 0.001:
            currentSideDistance = self.shoulderSideDistance*self.currentSide
        else:
            offsetVal = self.sideSwitchSpeed*dt
            if offsetVal > 1:
                offsetVal = 1
            offset = sideDiff*offsetVal
            currentSideDistance += offset

        self.cameraBase.setX(currentSideDistance)

    # A method to call when destroying the camera-controller
    def cleanup(self):
        # This class doesn't take ownership of either the camera
        # or the "ownerNodePath", and so simply detaches the former
        # and disengages from the latter. The assumption is that other
        # code is responsible for them.
        # (And indeed, one may want to re-use the camera!)

        if self.camera is not None:
            self.camera.detachNode()
            self.camera = None

        if self.ownerNodePath is not None:
            self.ownerNodePath = None

        # Clean up the controller's objects
        self.cleanupCollision()
        if self.cameraBase is not None:
            self.cameraBase.removeNode()
            self.cameraBase = None

    # A method to clean up whatever collision elements may be used
    # by a given implementation.
    #
    # Stub, intended to be overridden
    def cleanupCollision(self):
        pass