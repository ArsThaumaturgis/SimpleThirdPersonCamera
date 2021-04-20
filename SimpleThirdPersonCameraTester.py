# Copyright 2021 Ian Eborn
# A small demo-program illustrating basic usage of the associated third-person camera-controller.
#
# Specifically, this program creates and loads a simple player-object and environment, with the
# camera-controller attached to the player-object. The user can then drive the player-object around,
# with the camera reacting to the presence of obstacles behind the player-object.

# Panda-related importations
from direct.showbase.ShowBase import ShowBase

from panda3d.core import PandaNode, Vec3, Vec4
from panda3d.core import CollisionHandlerPusher, CollisionTraverser, CollisionSphere, CollisionNode
from panda3d.core import DirectionalLight
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

# The importation of the third-person camera-controller, as well as some related constants
from SimpleThirdPersonCameraPandaCollision import SimpleThirdPersonCameraPandaCollision
from SimpleThirdPersonCamera import SIMPLE_THIRD_PERSON_CAMERA_SIDE_LEFT,\
    SIMPLE_THIRD_PERSON_CAMERA_SIDE_RIGHT,\
    SIMPLE_THIRD_PERSON_CAMERA_SIDE_CENTRE

# A simple player-class
#
# Note: In a proper game, it would likely be better--easier to navigate, for one thing--to
#       have this "Player" class in a separate Python-file. However, for this very-simple
#       demo-program, it's perhaps okay to just include it here for simplicity's sake!
class Player():
    def __init__(self, gameReference):
        # In general, I would suggest keeping a reference to the game-object
        # in a "common" Python-file, allowing it to be accessed from various places.
        # However, for something very simple like this, just passing it into the
        # constructor and using it there seems fine.

        # The basics: a root-node and a (static) model
        self.manipulator = gameReference.render.attachNewNode(PandaNode("player"))

        self.model = gameReference.loader.loadModel("DemoModels/standInPlayer")
        self.model.reparentTo(self.manipulator)

        # Collision, so that the player doesn't pass through walls
        self.colliderNode = CollisionNode("player collider")
        self.colliderNode.addSolid(CollisionSphere(0, 0, 0, 1))
        self.colliderNode.setIntoCollideMask(0)
        self.colliderNode.setFromCollideMask(2)
        self.collider = self.manipulator.attachNewNode(self.colliderNode)
        self.collider.setZ(1)

        # The camera-controller!
        self.cameraController = SimpleThirdPersonCameraPandaCollision(-5, 5, 0.5, 2.0, 7.0, 10.0,
                                                                      SIMPLE_THIRD_PERSON_CAMERA_SIDE_LEFT,
                                                                      self.manipulator,
                                                                      gameReference.camera,
                                                                      colliderRadius = 0.5)

        # Some variables used by the player's movement.
        self.velocity = Vec3(0, 0, 0)
        self.acceleration = 300.0
        self.maxSpeed = 15.0
        self.friction = 50.0
        self.turnSpeed = 200.0

    # A simple method that allows us to cycle through the positions that the camera
    # can hold: left, right, and centre.
    def switchCameraSide(self):
        if self.cameraController.currentSide == SIMPLE_THIRD_PERSON_CAMERA_SIDE_LEFT:
            self.cameraController.setCurrentSide(SIMPLE_THIRD_PERSON_CAMERA_SIDE_RIGHT)
        elif self.cameraController.currentSide == SIMPLE_THIRD_PERSON_CAMERA_SIDE_RIGHT:
            self.cameraController.setCurrentSide(SIMPLE_THIRD_PERSON_CAMERA_SIDE_CENTRE)
        else:
            self.cameraController.setCurrentSide(SIMPLE_THIRD_PERSON_CAMERA_SIDE_LEFT)

    # The update-method of the player, intended to be called by the game-class
    def update(self, dt, keyMap, sceneRoot):
        # Again, it's perhaps better to have a reference to the game-object
        # in a "common" Python-file from which we could access the scene-root,
        # "render". But for the sake of convenience and cleanness, and given that
        # this is so simple a demo, I'm just passing it in as a parameter.

        # Movement

        # Update velocity according to key-presses and player-direction
        orientationQuat = self.manipulator.getQuat(sceneRoot)
        forward = orientationQuat.getForward()
        right = orientationQuat.getRight()

        walking = False

        if keyMap["up"]:
            self.velocity += forward*self.acceleration*dt
            walking = True
        if keyMap["down"]:
            self.velocity -= forward*self.acceleration*dt
            walking = True
        if keyMap["right"]:
            self.velocity += right*self.acceleration*dt
            walking = True
        if keyMap["left"]:
            self.velocity -= right*self.acceleration*dt
            walking = True

        # Turn the player according to key-presses
        if keyMap["turnRight"]:
            self.manipulator.setH(self.manipulator, -self.turnSpeed*dt)
        if keyMap["turnLeft"]:
            self.manipulator.setH(self.manipulator, self.turnSpeed*dt)

        # Prevent the player from moving too fast
        speed = self.velocity.length()

        if speed > self.maxSpeed:
            speed = self.maxSpeed
            self.velocity.normalize()
            self.velocity *= speed

        # Update the player's position
        self.manipulator.setPos(self.manipulator.getPos() + self.velocity*dt)

        # Apply friction when the player stops moving
        if not walking:
            frictionVal = self.friction*dt
            if frictionVal > speed:
                self.velocity.set(0, 0, 0)
            else:
                frictionVec = -self.velocity
                frictionVec.normalize()
                frictionVec *= frictionVal
                self.velocity += frictionVec

        # And update the camera-controller
        self.cameraController.update(dt, sceneRoot)

    # A method to clean up when destroying this object
    def cleanup(self):
        if self.cameraController is not None:
            self.cameraController.cleanup()
            self.cameraController = None

# A simple game-class; the core of the program
class Game(ShowBase):
    def __init__(self):
        # Some initialisation:
        # - Call the super-class's __init__ method
        # - Disable Panda's built-in camera-control
        # - And set a cleanup method for quitting
        ShowBase.__init__(self)

        self.disableMouse()

        self.exitFunc = self.cleanup

        # Input: a basic key-map, followed by some key-events
        self.keyMap = {
            "up" : False,
            "down" : False,
            "left" : False,
            "right" : False,
            "turnLeft" : False,
            "turnRight" : False,
        }

        # Note: Sorry about the weird controls. In the interests of
        #       keeping this demo simple and brief, I'm eschewing
        #       mouse-control. ^^;
        self.accept("w", self.updateKeyMap, ["up", True])
        self.accept("w-up", self.updateKeyMap, ["up", False])
        self.accept("s", self.updateKeyMap, ["down", True])
        self.accept("s-up", self.updateKeyMap, ["down", False])
        self.accept("a", self.updateKeyMap, ["left", True])
        self.accept("a-up", self.updateKeyMap, ["left", False])
        self.accept("d", self.updateKeyMap, ["right", True])
        self.accept("d-up", self.updateKeyMap, ["right", False])
        self.accept("q", self.updateKeyMap, ["turnLeft", True])
        self.accept("q-up", self.updateKeyMap, ["turnLeft", False])
        self.accept("e", self.updateKeyMap, ["turnRight", True])
        self.accept("e-up", self.updateKeyMap, ["turnRight", False])

        # Since the effect of "switchCameraSide" is immediate, there's
        # no reason to use the key-map--indeed, doing so would likely
        # over-complicate things
        self.accept("space", self.switchCameraSide)

        # Allow the player to quit!
        self.accept("escape", self.userExit)

        # The player-object
        self.player = Player(self)

        # Collision-handling for the player's movement.
        # This isn't used by the camera-controller.
        self.pusher = CollisionHandlerPusher()
        self.pusher.setHorizontal(True)
        self.cTrav = CollisionTraverser()

        self.cTrav.addCollider(self.player.collider, self.pusher)
        self.pusher.addCollider(self.player.collider, self.player.manipulator)

        # A simple environment in which to move around.
        self.environment = self.loader.loadModel("DemoModels/environment")
        self.environment.reparentTo(self.render)

        # Light for the environment
        light = DirectionalLight("main light")
        self.lightNodePath = self.render.attachNewNode(light)
        self.lightNodePath.setHpr(25, -45, 0)
        self.render.setLight(self.lightNodePath)

        # Activate built-in shader-support
        self.render.setShaderAuto()

        # Start an update-task to drive the gameplay
        self.updateTask = self.taskMgr.add(self.update, "update")

        # Put up some instructions and feedback-text onto the screen
        self.instructions = OnscreenText(text = "Move: WASD\nTurn: Q and E\nCycle camera-positions: SPACE\nQuit: ESCAPE",
                                         parent = self.a2dTopLeft,
                                         scale = 0.07,
                                         align = TextNode.ALeft,
                                         pos = (0, -0.1))

        self.camPosText = OnscreenText(text = "<CamPos>",
                                       parent = self.a2dTopRight,
                                       scale = 0.07,
                                       align = TextNode.ARight,
                                       pos = (-0.01, -0.1))
        self.updateCamPosText()

    # Update the text that indicate the current lateral-placement of the camera
    def updateCamPosText(self):
        if self.player.cameraController.currentSide == SIMPLE_THIRD_PERSON_CAMERA_SIDE_LEFT:
            self.camPosText.setText("Camera-position: Left")
        elif self.player.cameraController.currentSide == SIMPLE_THIRD_PERSON_CAMERA_SIDE_RIGHT:
            self.camPosText.setText("Camera-position: Right")
        elif self.player.cameraController.currentSide == SIMPLE_THIRD_PERSON_CAMERA_SIDE_CENTRE:
            self.camPosText.setText("Camera-position: Centre")
        else:
            self.camPosText.setText("Camera-position: Er... Unknown! (Unrecognised value for 'currentSide')")

    # Update the key-map when a key is pressed or released
    def updateKeyMap(self, controlName, controlState):
        self.keyMap[controlName] = controlState

    # Tell the player to cycle camera-positions, and
    # update the UI-text that indicates the current camera-position
    def switchCameraSide(self):
        self.player.switchCameraSide()
        self.updateCamPosText()

    # Update the game!
    # Which, in something so simple, just means "update the player, which updates the camera".
    def update(self, task):
        dt = globalClock.getDt()

        self.player.update(dt, self.keyMap, self.render)

        return task.cont

    # A method to clean up on quitting
    def cleanup(self):
        if self.pusher is not None:
            self.pusher.removeCollider(self.player.collider)
            self.pusher = None

        if self.cTrav is not None:
            self.cTrav.removeCollider(self.player.collider)
            self.cTrav = None

        if self.player is not None:
            self.player.cleanup()
            self.player = None

# Run the demo!
game = Game()
game.run()