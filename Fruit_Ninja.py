from pykinect2 import PyKinectV2, PyKinectRuntime 
from pykinect2.PyKinectV2 import * 

import ctypes 
import _ctypes 
import pygame 
import sys 
import math
import random

if sys.hexversion >= 0x03000000:
    import _thread as thread
else:
    import thread

# colors for drawing different bodies; seven different colors 
SKELETON_COLORS = [pygame.color.THECOLORS["red"], 
                  pygame.color.THECOLORS["blue"], 
                  pygame.color.THECOLORS["green"], 
                  pygame.color.THECOLORS["orange"], 
                  pygame.color.THECOLORS["purple"], 
                  pygame.color.THECOLORS["yellow"], 
                  pygame.color.THECOLORS["violet"]]

class GameRuntime(pygame.sprite.Sprite):

    def __init__(self):
        pygame.init()

        self.screen_width = 1920 
        self.screen_height = 1080

        # init players that are visible 
        self.playerList = [-1,-1,-1,-1,-1,-1]
        self.seen = []

        # head coords
        self.headX = 0
        self.headY = 0   
        self.headConvertX = 0
        self.headConvertY = 0
        self.ai = False

        # coordinates mapped to the color frame
        self.p1rx = 0
        self.p1ry = 0
        self.p1lx = 0
        self.p1ly = 0
        # real world coordinates for pausing
        self.p1rmx = 0
        self.p1lmx = 0
        self.p1rmy = 0
        self.p1lmy = 0

        # player 2-6 coordinates to track 
        self.p2rx = 0
        self.p2ry = 0
        self.p2lx = 0
        self.p2ly = 0

        self.p3rx = 0
        self.p3ry = 0
        self.p3lx = 0
        self.p3ly = 0

        self.p4rx = 0
        self.p4ry = 0
        self.p4lx = 0
        self.p4ly = 0

        self.p5rx = 0
        self.p5ry = 0
        self.p5lx = 0
        self.p5ly = 0

        self.p6rx = 0
        self.p6ry = 0
        self.p6lx = 0
        self.p6ly = 0

        # current mode 
        self.mode = 'intro' 
        self.prevMode = ''
        self.retryMode = ''

        #statically initialize all the fruit and bombs once
        fruit.start()
        bomb.start()

        # bomb explosion sprites
        Explosion.start()
        self.explosions = pygame.sprite.Group()

        # GAME VARIABLES 
        # where all fruit is temporarilty stored; draw function goes through this
        self.imageFruit = []
        self.bombs = []

        self.gravity = .5
        self.score = 0
        self.lives = 3
        self.highScore = 0

        self.startTime = 0
        self.classicMinutes = 0
       
        self.totalLaunches = 0         

        # launch time between vollies in seconds
        self.fruitLaunchTime = 3
        self.minFruit = 1
        self.maxFruit = 2
        self.maxBombChance = 5
        
        # images
        # intro screen
        self.waveBG = pygame.image.load('wave_bg.jpeg')
        self.logo = pygame.image.load('logo.png')
        self.arcadeMode = pygame.image.load('Arcade_mode.png')
        self.zenMode = pygame.image.load('Zen_mode.png')
        self.questionMark = pygame.image.load('help.png')
        self.classicMode = pygame.image.load('Classic.png')
        self.vs = pygame.image.load('vs.png')
        # help screen
        self.oldMan = pygame.image.load('oldman.png')
        self.ninjaSlicing = pygame.image.load('ninjaSlicing.png')
        self.pineapple = pygame.image.load('fruits/Pineapple.png')
        self.banana = pygame.image.load('fruits/Banana.png')
        self.bombClassic = pygame.image.load('bombs/classicBomb.png')
        self.bombArcade = pygame.image.load('bombs/arcadeBomb.png')
        # classic Mode 
        self.blackX = pygame.image.load('blackX.png')
        self.redX = pygame.image.load('redX.png')
        self.scoreMellon = pygame.image.load('scoreMellon.png')
        self.kozHead = pygame.image.load('kozHead.png')
        # game over
        self.ninja = pygame.image.load('ninja.png')
        self.scroll = pygame.image.load('scroll.png')
        self.dojo = pygame.image.load('Dojo.png')
        self.replay = pygame.image.load('retry.png')
        self.exit = pygame.image.load('exit.png')
        self.coolNinja = pygame.image.load('coolNinja.png')
        self.easterEgg = False
        # zen mode
        self.back = pygame.image.load('back.png')
        # vs mode
        self.p1score = 0
        self.p2score = 0
        self.oldMan1 = pygame.image.load('p1Score.png')
        self.oldMan2 = pygame.image.load('p2Score.png')
       
        # sound 
        self.introMusic = pygame.mixer.music.load('sounds/introMusic.mp3')
        pygame.mixer.music.play(-1)
        self.musicVolume = .4
        pygame.mixer.music.set_volume(self.musicVolume)
        self.splat1 = pygame.mixer.Sound('sounds/splat1.wav')
        self.explosion = pygame.mixer.Sound('sounds/explosion.wav')
        
        #KINECT and pygame stuff learned from workshop
        # handle when game ends
        self._done = False
        #pygame builtin clock; manage fps 
        self._clock = pygame.time.Clock()
        # set width and height of the pygame window 
        self._screen = pygame.display.set_mode((960,540), pygame.HWSURFACE|pygame.DOUBLEBUF, 32)
        self.width = 960
        self.height = 540
        # give us the kinect sources we want
        # want color and body sources
        self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body | PyKinectV2.FrameSourceTypes_Depth | PyKinectV2.FrameSourceTypes_Infrared) 
        # back buffer surface for Kinect color frames, 32bit color, width and height equal to the Kinect color frame size 
        self._frame_surface = pygame.Surface((self._kinect.color_frame_desc.Width, self._kinect.color_frame_desc.Height), 0, 32) 
        # here we will store skeleton data  
        self._bodies = None   
               
    # ~ adapted from pykinect github; https://github.com/Kinect/PyKinect2/blob/master/examples/PyKinectBodyGame.py ~
    def draw_body_bone(self, joints, jointPoints, color, joint0, joint1):
        joint0State = joints[joint0].TrackingState;
        joint1State = joints[joint1].TrackingState;

        # both joints are not tracked
        if (joint0State == PyKinectV2.TrackingState_NotTracked) or (joint1State == PyKinectV2.TrackingState_NotTracked): 
            return

        # both joints are not *really* tracked
        if (joint0State == PyKinectV2.TrackingState_Inferred) and (joint1State == PyKinectV2.TrackingState_Inferred):
            return

        # ok, at least one is good 
        start = (jointPoints[joint0].x, jointPoints[joint0].y)
        end = (jointPoints[joint1].x, jointPoints[joint1].y)

        try:
            pygame.draw.line(self._frame_surface, color, start, end, 8)
        except: # need to catch it due to possible invalid positions (with inf)
            pass
    
    # check to make sure our hands are being properly tracked in the color world 
    def draw_hand_circle(self, joints, jointPoints, color, joint0):
        joint0State = joints[joint0].TrackingState;

        # both joints are not tracked
        if (joint0State == PyKinectV2.TrackingState_NotTracked): 
            return

        # both joints are not *really* tracked
        if (joint0State == PyKinectV2.TrackingState_Inferred):
            return

        # ok, at least one is good 
        start = (int(jointPoints[joint0].x), int(jointPoints[joint0].y))

        try:
            pygame.draw.circle(self._frame_surface, color, start, 20, 0)
        except:
            pass
        
    def draw_body(self, joints, jointPoints, color):
        # Right Arm    
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ShoulderRight, PyKinectV2.JointType_ElbowRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ElbowRight, PyKinectV2.JointType_WristRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristRight, PyKinectV2.JointType_HandRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HandRight, PyKinectV2.JointType_HandTipRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristRight, PyKinectV2.JointType_ThumbRight);

        # Left Arm
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ShoulderLeft, PyKinectV2.JointType_ElbowLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ElbowLeft, PyKinectV2.JointType_WristLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_HandLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HandLeft, PyKinectV2.JointType_HandTipLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_ThumbLeft);

        # our hand circles
        self.draw_hand_circle(joints, jointPoints, color, PyKinectV2.JointType_HandRight)
        self.draw_hand_circle(joints, jointPoints, color, PyKinectV2.JointType_HandLeft)      

    # draws our color frames to the screen
    # takes color image from kinect and gives to pygame 
    def draw_color_frame(self, frame, target_surface): 
        target_surface.lock() 
        address = self._kinect.surface_as_array(target_surface.get_buffer()) 
        ctypes.memmove(address, frame.ctypes.data, frame.size) 
        del address 
        target_surface.unlock() 

    def hitFruit(self):
        
        for fruit in self.imageFruit:
            #print(fruit.x, fruit.y)
            fruitCX = fruit.x - fruit.w
            fruitCY = fruit.y - fruit.h
            if ((self.p1rx > fruit.x-fruit.w and self.p1rx < fruit.x+fruit.w and 
                 self.p1ry > fruit.y-fruit.h and self.p1ry < fruit.y+fruit.h) or
                (self.p1lx > fruit.x-fruit.w and self.p1lx < fruit.x+fruit.w and
                self.p1ly > fruit.y-fruit.h and self.p1ly < fruit.y+fruit.h)):
                if self.mode != 'vs':
                    self.score += 1
                else:
                    self.p1score += 1

                self.imageFruit.remove(fruit)
                pygame.mixer.Sound.play(self.splat1)       

    def player2HitFruit(self):
        for fruit in self.imageFruit:
            #print(fruit.x, fruit.y)
            fruitCX = fruit.x - fruit.w
            fruitCY = fruit.y - fruit.h
            if ((self.p2rx > fruit.x-fruit.w and self.p2rx < fruit.x+fruit.w and 
                 self.p2ry > fruit.y-fruit.h and self.p2ry < fruit.y+fruit.h) or
                (self.p2lx > fruit.x-fruit.w and self.p2lx < fruit.x+fruit.w and
                self.p2ly > fruit.y-fruit.h and self.p2ly < fruit.y+fruit.h)):
                if self.mode != 'vs':
                    self.score += 1
                else:
                    self.p2score += 1

                self.imageFruit.remove(fruit)
                pygame.mixer.Sound.play(self.splat1)  

    def player3HitFruit(self):
        for fruit in self.imageFruit:
            #print(fruit.x, fruit.y)
            fruitCX = fruit.x - fruit.w
            fruitCY = fruit.y - fruit.h
            if ((self.p3rx > fruit.x-fruit.w and self.p3rx < fruit.x+fruit.w and 
                 self.p3ry > fruit.y-fruit.h and self.p3ry < fruit.y+fruit.h) or
                (self.p3lx > fruit.x-fruit.w and self.p3lx < fruit.x+fruit.w and
                self.p3ly > fruit.y-fruit.h and self.p3ly < fruit.y+fruit.h)):
                self.score += 1
                self.imageFruit.remove(fruit)
                pygame.mixer.Sound.play(self.splat1)  

    def player4HitFruit(self):
        for fruit in self.imageFruit:
            #print(fruit.x, fruit.y)
            fruitCX = fruit.x - fruit.w
            fruitCY = fruit.y - fruit.h
            if ((self.p4rx > fruit.x-fruit.w and self.p4rx < fruit.x+fruit.w and 
                 self.p4ry > fruit.y-fruit.h and self.p4ry < fruit.y+fruit.h) or
                (self.p4lx > fruit.x-fruit.w and self.p4lx < fruit.x+fruit.w and
                self.p4ly > fruit.y-fruit.h and self.p4ly < fruit.y+fruit.h)):
                self.score += 1
                self.imageFruit.remove(fruit)
                pygame.mixer.Sound.play(self.splat1)  

    def player5HitFruit(self):
        for fruit in self.imageFruit:
            #print(fruit.x, fruit.y)
            fruitCX = fruit.x - fruit.w
            fruitCY = fruit.y - fruit.h
            if ((self.p5rx > fruit.x-fruit.w and self.p5rx < fruit.x+fruit.w and 
                 self.p5ry > fruit.y-fruit.h and self.p5ry < fruit.y+fruit.h) or
                (self.p5lx > fruit.x-fruit.w and self.p5lx < fruit.x+fruit.w and
                self.p5ly > fruit.y-fruit.h and self.p5ly < fruit.y+fruit.h)):
                self.score += 1
                self.imageFruit.remove(fruit)
                pygame.mixer.Sound.play(self.splat1)  

    def player6HitFruit(self):
        for fruit in self.imageFruit:
            #print(fruit.x, fruit.y)
            fruitCX = fruit.x - fruit.w
            fruitCY = fruit.y - fruit.h
            if ((self.p6rx > fruit.x-fruit.w and self.p6rx < fruit.x+fruit.w and 
                 self.p6ry > fruit.y-fruit.h and self.p6ry < fruit.y+fruit.h) or
                (self.p6lx > fruit.x-fruit.w and self.p6lx < fruit.x+fruit.w and
                self.p6ly > fruit.y-fruit.h and self.p6ly < fruit.y+fruit.h)):
                self.score += 1
                self.imageFruit.remove(fruit)
                pygame.mixer.Sound.play(self.splat1)            
   
    def blitFruit(self):
        for fruit in self.imageFruit:
            self._frame_surface.blit(fruit.image, (fruit.x-fruit.w, fruit.y-fruit.h))

    def makeTestFruit(self):
        
        x = random.randint(400,1920-400)
        v = random.randint(23,28)
        vx = random.randint(-5,5)
        self.imageFruit += [fruit(x,1150,v, vx)]

    def cleanFruit(self):
        for fruit in self.imageFruit:
            if fruit.y >1150:
                self.imageFruit.remove(fruit)
                if self.mode != 'zen':
                    self.loseLife()

    def loseLife(self):
        self.lives -= 1
       
    def drawLives(self):
        redX = pygame.transform.scale(self.redX, (100,100))
        margin = 10
        if self.lives == 2:
            self._frame_surface.blit(redX, (1920-300-margin,margin))
        elif self.lives == 1:
            self._frame_surface.blit(redX, (1920-300-margin,margin))
            self._frame_surface.blit(redX, (1920-200-margin,margin))
        elif self.lives == 0:
            self._frame_surface.blit(redX, (1920-100-margin,margin))
            self._frame_surface.blit(redX, (1920-200-margin,margin))
            self._frame_surface.blit(redX, (1920-300-margin,margin))
            self.mode = "gameOver"
    def whoWon(self):
        if self.p1score >= 50:              
            self.mode = 'gameOver' 
            self.runGameOver()   
        if self.p2score >50:
            self.mode = 'gameOver' 
                              
    def getTime(self):
        self.startTime = pygame.time.get_ticks()

    def hitBomb(self):
        for bomb in self.bombs:
            bombCX = bomb.x-bomb.w
            bombCY = bomb.y-bomb.y
            if ((self.p1rx > bomb.x-bomb.w and self.p1rx < bomb.x+bomb.w and 
                 self.p1ry > bomb.y-bomb.h and self.p1ry < bomb.y+bomb.h) or
                (self.p1lx > bomb.x-bomb.w and self.p1lx < bomb.x+bomb.w and
                self.p1ly > bomb.y-bomb.h and self.p1ly < bomb.y+bomb.h)):
                if self.mode != 'vs':
                    if bomb.bombType == 1:
                        self.explosions.add(Explosion(bomb.x,bomb.y))
                        self.score -= 10
                    if bomb.bombType == 0:
                        self.mode = "gameOver"
                else:
                    if bomb.bombType == 1:
                        self.explosions.add(Explosion(bomb.x,bomb.y))
                        self.p1score -= 10
                self.bombs.remove(bomb)
                
                pygame.mixer.Sound.play(self.explosion) 
                   
    def hitBombP2(self):

        for bomb in self.bombs:
            bombCX = bomb.x-bomb.w
            bombCY = bomb.y-bomb.y
            if ((self.p2rx > bomb.x-bomb.w and self.p2rx < bomb.x+bomb.w and 
                 self.p2ry > bomb.y-bomb.h and self.p2ry < bomb.y+bomb.h) or
                (self.p2lx > bomb.x-bomb.w and self.p2lx < bomb.x+bomb.w and
                self.p2ly > bomb.y-bomb.h and self.p2ly < bomb.y+bomb.h)):
                if self.mode != 'vs':
                    if bomb.bombType == 1:
                        self.explosions.add(Explosion(bomb.x,bomb.y))
                        self.score -= 10
                    if bomb.bombType == 0:
                        self.mode = "gameOver"
                else:
                    if bomb.bombType == 1:
                        self.explosions.add(Explosion(bomb.x,bomb.y))
                        self.p2score -= 10
                self.bombs.remove(bomb)
                
                pygame.mixer.Sound.play(self.explosion)     
                  
    def makeBomb(self, type):
        x = random.randint(300,1600)
        v = random.randint(23,28)
        vx = random.randint(-5,5)
        self.bombs += [bomb(type,x,1150,v, vx)]      

    def blitBomb(self):
        for bomb in self.bombs:
            self._frame_surface.blit(bomb.image, (bomb.x-bomb.w, bomb.y-bomb.h))

    def cleanBomb(self):
        for bomb in self.bombs:
            if bomb.y >1150:
                self.bombs.remove(bomb)        
                
    def launchFruit(self, num):
        self.totalLaunches += 1
        for i in range(0,num):
            self.makeTestFruit()          
        
    def drawLines(self):
        xVals = []

        if len(self.imageFruit) >= 2:
            for fruit in self.imageFruit:
                xVals += [(fruit.x-fruit.w//2, fruit.y-fruit.h//2)]
                        
            xVals.sort()
    
            for i in range (1, len(xVals)):
                fruit1 = xVals[i]
                fruit2 = xVals[i-1]            
                pygame.draw.line(self._frame_surface, (0,0,0), (fruit1[0], fruit1[1]), (fruit2[0], fruit2[1]), 5)      
                
    def reset(self):
        self.imageFruit = []
        self.bombs = []                 

    # bulk of code that actually detects human skelton and tracks to the color frame 
    # also learned and adapted from kinect workshop (my adaptions allow 6 player detection)
    def scanBody(self):
        # We have a body frame, so can get skeletons 
        if self._kinect.has_new_body_frame():  
            
            self._bodies = self._kinect.get_last_body_frame() 
                    
            # we have detected a body
            if self._bodies is not None:  

                for i in range(0, self._kinect.max_body_count):                                
                    
                    body = self._bodies.bodies[i]                    
                    
                    # no bodies tracked do nothing
                    if not body.is_tracked:  
                        # reset the players 
                        
                        continue
                  
                    joints = body.joints

                    # convert joint coordinates to color space
                    joint_points = self._kinect.body_joints_to_color_space(joints)

                    # draw desired joints 
                    self.draw_body(joints, joint_points, SKELETON_COLORS[i]) 

                    playerNum = i
                    if self.playerList[0] == -1:
                        self.playerList[0] = playerNum                        
                        self.seen += [playerNum]

                    if self.playerList[1] == -1 and playerNum not in self.seen:                       
                        self.playerList[1] = playerNum  
                        self.seen += [playerNum]
                    if self.playerList[2] == -1 and playerNum not in self.seen:
                        self.playerList[2] = playerNum  
                        self.seen += [playerNum]
                    if self.playerList[3] == -1 and playerNum not in self.seen:
                        self.playerList[3] = playerNum  
                        self.seen += [playerNum]
                    if self.playerList[4] == -1 and playerNum not in self.seen:
                        self.playerList[4] = playerNum 
                        self.seen += [playerNum]
                    if self.playerList[5] == -1 and playerNum not in self.seen:
                        self.playerList[5] = playerNum  
                        self.seen += [playerNum]
                                                                                                                                                                                             
                    if playerNum == self.playerList[0]:
                        # save hand coordinates relative to kinect
                        # right hand

                        if joints[PyKinectV2.JointType_Head].TrackingState != PyKinectV2.TrackingState_NotTracked:
                            self.headX = joints[PyKinectV2.JointType_Head].Position.x  
                            self.headY = joints[PyKinectV2.JointType_Head].Position.y  

                            self.headConvertX = joint_points[PyKinectV2.JointType_Head].x
                            self.headConvertY = joint_points[PyKinectV2.JointType_Head].y

                        if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:   
                            self.p1rx = (joint_points[PyKinectV2.JointType_HandRight].x)
                            self.p1ry = (joint_points[PyKinectV2.JointType_HandRight].y)  
                            
                            self.p1rmx = joints[PyKinectV2.JointType_HandRight].Position.x   
                            self.p1rmy = joints[PyKinectV2.JointType_HandRight].Position.y
                                                                                 
                            
                        # left hand
                        if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked: 
                            self.p1lx = joint_points[PyKinectV2.JointType_HandLeft].x
                            self.p1ly = joint_points[PyKinectV2.JointType_HandLeft].y 

                            self.p1lmx = joints[PyKinectV2.JointType_HandLeft].Position.x   
                            self.p1lmy = joints[PyKinectV2.JointType_HandLeft].Position.y   

                    
                    # hands together, pause
                    if abs(self.p1rmx - self.p1lmx) <= .1 and abs(self.p1rmy - self.p1lmy) <= .1:
                        self.mode = 'help'                                            
                    else:                      
                        self.mode = self.prevMode

                    # if players put hands to head, secret AI help mode
                    if (abs(self.p1rmx - self.headX) <= .3 and
                        abs(self.p1lmx - self.headX) <= .3 and
                        abs(self.p1rmy - self.headY) <= .3 and
                        abs(self.p1lmy - self.headY) <= .3):
                        self.ai = True                       
                    else:
                        self.ai = False
                                                                    
                    # a second player enters the frame 
                    # store his data sep from player 1
                    if playerNum == self.playerList[1]:
                        
                        if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:   
                            self.p2rx = (joint_points[PyKinectV2.JointType_HandRight].x)
                            self.p2ry = (joint_points[PyKinectV2.JointType_HandRight].y)                                  
                        
                        if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked: 
                            self.p2lx = joint_points[PyKinectV2.JointType_HandLeft].x
                            self.p2ly = joint_points[PyKinectV2.JointType_HandLeft].y

                    if playerNum == self.playerList[2]:
                        
                        if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:   
                            self.p3rx = (joint_points[PyKinectV2.JointType_HandRight].x)
                            self.p3ry = (joint_points[PyKinectV2.JointType_HandRight].y)                                  
                        
                        if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked: 
                            self.p3lx = joint_points[PyKinectV2.JointType_HandLeft].x
                            self.p3ly = joint_points[PyKinectV2.JointType_HandLeft].y

                    if playerNum == self.playerList[3]:
                        
                        if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:   
                            self.p4rx = (joint_points[PyKinectV2.JointType_HandRight].x)
                            self.p4ry = (joint_points[PyKinectV2.JointType_HandRight].y)                                  
                        
                        if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked: 
                            self.p4lx = joint_points[PyKinectV2.JointType_HandLeft].x
                            self.p4ly = joint_points[PyKinectV2.JointType_HandLeft].y

                    if playerNum == self.playerList[4]:
                        
                        if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:   
                            self.p5rx = (joint_points[PyKinectV2.JointType_HandRight].x)
                            self.p5ry = (joint_points[PyKinectV2.JointType_HandRight].y)                                  
                        
                        if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked: 
                            self.p5lx = joint_points[PyKinectV2.JointType_HandLeft].x
                            self.p5ly = joint_points[PyKinectV2.JointType_HandLeft].y

                    if playerNum == self.playerList[5]:
                        
                       if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:   
                            self.p6rx = (joint_points[PyKinectV2.JointType_HandRight].x)
                            self.p6ry = (joint_points[PyKinectV2.JointType_HandRight].y)                                  
                        
                       if joints[PyKinectV2.JointType_HandLeft].TrackingState != PyKinectV2.TrackingState_NotTracked: 
                            self.p6lx = joint_points[PyKinectV2.JointType_HandLeft].x
                            self.p6ly = joint_points[PyKinectV2.JointType_HandLeft].y
                                                                                                                                      
    def run(self):
        # main loop
        while not self._done:
          
            for event in pygame.event.get():
                # if user clicks exit end the loop
                if event.type == pygame.QUIT:
                    self._done = True                
                
                if event.type == pygame.MOUSEBUTTONDOWN:                  
                    self.launchFruit(1)

                if event.type == pygame.KEYDOWN:
                    # if user presses 'm' key, mute/unmute music 
                    if event.key == pygame.K_m:
                        if self.musicVolume == .4:
                            self.musicVolume = 0
                            pygame.mixer.music.set_volume(0)
                        else:
                            self.musicVolume = .4
                            pygame.mixer.music.set_volume(.4)  
                    # cheats for demo       
                    elif event.key == pygame.K_1:
                        self.makeBomb(0)
                    elif event.key == pygame.K_2:
                        self.makeBomb(1)        
                    elif event.key == pygame.K_f:
                        self.launchFruit(1)
                    elif event.key == pygame.K_k:
                        if self.easterEgg == False:
                            self.easterEgg = True
                        else:
                            self.easterEgg = False                                  

            # We have a color frame. Fill out back buffer surface with frame's data  
            if self._kinect.has_new_color_frame(): 
                frame = self._kinect.get_last_color_frame() 
                self.draw_color_frame(frame, self._frame_surface) 
                frame = None

            # mode dispatcher
            if self.mode == 'intro':
                
                self.runIntro()

            if self.mode == 'game':

                self.runGame()

            if self.mode == 'gameOver':

                self.runGameOver()

            if self.mode == 'help':

                self.runHelp()

            if self.mode == 'zen':
                
                self.runZen()

            if self.mode == 'vs':
                
                self.runVS()                                  
                                                   
            # keep aspect ratio scaling properly 
            h_to_w = float(self._frame_surface.get_height()) / self._frame_surface.get_width() 
            target_height = int(h_to_w * self._screen.get_width()) 
            surface_to_draw = pygame.transform.scale(self._frame_surface, (self._screen.get_width(), target_height)); 

            # redraw entire fram 
            self._screen.blit(surface_to_draw, (0,0)) 
            surface_to_draw = None 
            pygame.display.update() 
 
            # --- Limit to 60 frames per second 
            self._clock.tick(60) 
                           
        self._kinect.close()
        pygame.quit()        

    def runIntro(self):     
        self.prevMode = 'intro'
        # draw intro bg and icons 
        #self._frame_surface.fill((255,255,255))
        waveBG = pygame.transform.scale(self.waveBG, (1920, 1080))
        self._frame_surface.blit(waveBG, (0,0))
        logo = pygame.transform.scale(self.logo, (900,400))
        self._frame_surface.blit(logo, (960-450,50))        
        # classic button
        classic = pygame.transform.scale(self.classicMode, (300,300))
        self._frame_surface.blit(classic, (1280+50, 500))
        # zen button
        zenMode = pygame.transform.scale(self.zenMode, (300,300))
        self._frame_surface.blit(zenMode, (640-350, 500))
        qMark = pygame.transform.scale(self.questionMark, (150,150))
        self._frame_surface.blit(qMark, (1920-180, 10))
        txt = pygame.font.Font('freesansbold.ttf',25)
        TextSurf=txt.render(str('Need Help?'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (1920-170,160))
        txt = pygame.font.Font('freesansbold.ttf',25)
        TextSurf=txt.render(str('Put your hands'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (1920-200,190))
        txt = pygame.font.Font('freesansbold.ttf',25)
        TextSurf=txt.render(str('Together.'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (1920-160,220))
        # vs button
        vs = pygame.transform.scale(self.vs, (250,250))
        self._frame_surface.blit(vs, (825, 600))

        # scan body and show user where their arms and hand are over the intro screen 
        self.scanBody()
                      
        rightX = self.p1rx
        rightY = self.p1ry
        leftX = self.p1lx
        leftY = self.p1ly
        
        # classic 
        if ((rightX >= 1280+50 and rightX <= 1280+350 and
            rightY >=500 and rightY <= 800) or 
            (leftX >= 1920-160 and leftX <= 1920-10 and
             leftY >=500 and leftY <= 800)):      
             self.startTime = pygame.time.get_ticks()
             self.mode = 'game' 
        
        # zen       
        if ((rightX >= 640-350 and rightX <= 640-50 and
            rightY >=500 and rightY <= 800) or 
            (leftX >= 640-350 and leftX <= 640-50 and
             leftY >=500 and leftY <= 800)):   
                self.startTime = pygame.time.get_ticks()  
                self.mode = 'zen'      
        
        # vs mode        
        if ((rightX >=825 and rightX <= 825+250 and
            rightY >=600 and rightY <= 850) or 
            (leftX >= 825 and leftX <= 825+250 and
             leftY >=600 and leftY <= 850)):         
                self.startTime = pygame.time.get_ticks()  
                self.mode = 'vs'   
        
    def runHelp(self):  
        waveBG = pygame.transform.scale(self.waveBG, (1920, 1080))
        self._frame_surface.blit(waveBG, (0,0))
        self._frame_surface.blit(self.oldMan,(600,25))
        self._frame_surface.blit(self.ninjaSlicing,(900, 25))
        self._frame_surface.blit(self.pineapple, (300,350))
        self._frame_surface.blit(self.banana, (400,450))
        self._frame_surface.blit(self.bombClassic, (300,650))
        self._frame_surface.blit(self.bombArcade, (400,750))
        self.scanBody()

        txt = pygame.font.Font('freesansbold.ttf',25)
        TextSurf=txt.render(str('Tired of the music? Press M to mute.'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (30,20))    
        txt = pygame.font.Font('freesansbold.ttf',25)
        TextSurf=txt.render(str('Hmmm...I wonder what pressing K does'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (1400,20))     

        txt = pygame.font.Font('freesansbold.ttf',50)
        TextSurf=txt.render(str('Try and slice the fruit like these!'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (500,440))
        txt = pygame.font.Font('freesansbold.ttf',50)
        TextSurf=txt.render(str('Hit as many as you can to increase your score!'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (500,500))

        txt = pygame.font.Font('freesansbold.ttf',50)
        TextSurf=txt.render(str('Watch out for these.'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (500,700))
        txt = pygame.font.Font('freesansbold.ttf',50)
        TextSurf=txt.render(str('Hitting the red one will end the game.'),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (500,760))

        if self.prevMode == 'game':
            txt = pygame.font.Font('freesansbold.ttf',50)
            TextSurf=txt.render(str('The timer is still going!!'),True,(255,255,255))
            self._frame_surface.blit(TextSurf, (600,1000))

    def runGameOver(self):
        # remove fruit and bombs 
        self.cleanFruit()
        self.cleanBomb()

        self.prevMode = 'gameOver'
        waveBG = pygame.transform.scale(self.waveBG, (1920, 1080))
        self._frame_surface.blit(waveBG, (0,0))
        ninja = pygame.transform.scale(self.ninja, (300,700))
        self._frame_surface.blit(ninja, (75,200))
        self._frame_surface.blit(self.scroll, (400,100))
        dojo = pygame.transform.scale(self.dojo, (200,200))
        self._frame_surface.blit(dojo, (1500,150))
        iconW, iconH = dojo.get_size()
        replay = pygame.transform.scale(self.replay, (230, 230))
        self._frame_surface.blit(replay, (1500,425))
        exit = pygame.transform.scale(self.exit, (200, 200))
        self._frame_surface.blit(exit, (1515,700))
        self._frame_surface.blit(self.coolNinja, (700,420))

        # print score 
        if self.retryMode != 'vs':
            if self.score > self.highScore:
                self.highScore = self.score
            txt = pygame.font.Font('freesansbold.ttf',80)
            TextSurf=txt.render('Score:'+ str(self.score),True,(0,0,0))
            self._frame_surface.blit(TextSurf, (550,300))
            txt = pygame.font.Font('freesansbold.ttf',40)
            TextSurf=txt.render('Highscore:'+ str(self.highScore),True,(0,0,0))
            self._frame_surface.blit(TextSurf, (550,400))
            txt = pygame.font.Font('freesansbold.ttf',50)
        else:
            if self.p1score > self.p2score:
                txt = pygame.font.Font('freesansbold.ttf',80)
                TextSurf=txt.render('Player 1 Wins!',True,(0,0,0))
                self._frame_surface.blit(TextSurf, (550,300))
            else:
                txt = pygame.font.Font('freesansbold.ttf',80)
                TextSurf=txt.render('Player 2 Wins!',True,(0,0,0))
                self._frame_surface.blit(TextSurf, (550,300))

        txt = pygame.font.Font('freesansbold.ttf',50)
        TextSurf=txt.render('GAME OVER',True,(0,0,0))
        self._frame_surface.blit(TextSurf, (750,150))
        
        rightX = self.p1rx
        rightY = self.p1ry
        leftX = self.p1lx
        leftY = self.p1ly
        
        # player wants to replay       
        if ((rightX >= 1500 and rightX <= 1730 and
            rightY >=425 and rightY <= 655) or 
            (leftX >= 1500 and leftX <= 1730 and
             leftY >=425 and leftY <= 655)):
               
                self.mode = self.retryMode
                self.prevMode = self.retryMode
                self.reset()
                self.lives = 3
                self.startTime = 0
                self.score = 0
                self.totalLaunches = 0                    
                self.fruitLaunchTime = 3
                self.minFruit = 1
                self.maxFruit = 2
                self.maxBombChance = 5
                self.p1score = 0
                self.p2score = 0
                
        # player wants to go to menu
        if ((rightX >= 1500 and rightX <= 1700 and
            rightY >=150 and rightY <= 350) or 
            (leftX >= 1500 and leftX <= 1700 and
             leftY >=150 and leftY <= 350)):
                self.mode = 'intro'
                self.prevMode = 'intro'

                self.reset()
                self.lives = 3
                self.startTime = 0
                self.score = 0
                self.totalLaunches = 0                    
                self.fruitLaunchTime = 3
                self.minFruit = 1
                self.maxFruit = 2
                self.maxBombChance = 5    
                self.p1score = 0
                self.p2score = 0           

        # player wants to quit
        if ((rightX >= 1515 and rightX <= 1715 and
            rightY >=700 and rightY <= 900) or 
            (leftX >= 1515 and leftX <= 1715 and
             leftY >=700 and leftY <= 900)):
                pygame.quit()
             
        self.scanBody()               

    def runGame(self):        
        self.retryMode = 'game'
        self.prevMode = 'game'
        #draw, score, timer, lives
        # lives and x's
        margin = 10
        blackX = pygame.transform.scale(self.blackX, (100,100))
        self._frame_surface.blit(blackX, (1920-100-margin,margin))
        self._frame_surface.blit(blackX, (1920-200-margin,margin))
        self._frame_surface.blit(blackX, (1920-300-margin,margin))

        #score
        scoreMellon = pygame.transform.scale(self.scoreMellon, (250,250))
        self._frame_surface.blit(scoreMellon, (margin, margin))
        txt = pygame.font.Font('freesansbold.ttf',150)
        TextSurf=txt.render(str(self.score),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (margin*2+250,50))

        if self.ai == True:
            self.scanBody()
            self.blitFruit()   
            self.drawLines()
            self.drawLives()
            if self.easterEgg == True:
                headW, headH = self.kozHead.get_size()    
                self._frame_surface.blit(self.kozHead, (self.headConvertX-headW//2, self.headConvertY-headH//2))   

        elif self.mode != 'help':

            # in game timer
            if self.startTime == 0:
                self.getTime()       
            realClock = (pygame.time.get_ticks()-self.startTime)//1000
            if realClock > 60:
                self.classicMinutes += 1
                self.getTime()                 
            txt = pygame.font.Font('freesansbold.ttf', 50)
            TextSurfTimer=txt.render(('Time: %d:%d')%(self.classicMinutes, realClock),True,(255,255,255))
            self._frame_surface.blit(TextSurfTimer, (1920-260, 120))
                      
            # gravity and angle of fruit  
            for fruit in self.imageFruit:
                fruit.y -= fruit.v
                fruit.v -= self.gravity
                fruit.x += fruit.vx

            # bomb physics
            for bomb in self.bombs:
                bomb.y -= bomb.v
                bomb.v -= self.gravity
                bomb.x += bomb.vx
        
            # game logic 
            if self.totalLaunches <= 10:
                if self.totalLaunches<=5:
                    if self.totalLaunches == 0:
                        pass
                    else:
                        self.maxFruit = self.totalLaunches
            if self.totalLaunches>10 and self.fruitLaunchTime == 3:
                self.fruitLaunchTime = 2
                self.minFruit = 3
                self.maxFruit = 10
                self.maxBombChance = 4
            if self.totalLaunches >= 20:
                self.fruitLaunchTime = 1        

            gameClock = (pygame.time.get_ticks()-self.startTime)/1000
            if gameClock > 2 and gameClock% self.fruitLaunchTime < .01:
                rand = random.randint(self.minFruit,self.maxFruit)
                self.launchFruit(rand)

                bombChance = random.randint(1,self.maxBombChance)
                if bombChance == 2:
                    type = random.randint(0,1)
                    self.makeBomb(type)            
                    
            if self.easterEgg == True:
                headW, headH = self.kozHead.get_size()    
                self._frame_surface.blit(self.kozHead, (self.headConvertX-headW//2, self.headConvertY-headH//2))            

            self.scanBody()
            self.drawLives()

            self.blitFruit()        
            self.cleanFruit()
            self.hitFruit()
            self.player2HitFruit() 
            self.player3HitFruit()   
            self.player4HitFruit()   
            self.player5HitFruit()   
            self.player6HitFruit()      
            
            self.blitBomb()
            self.cleanBomb()
            self.hitBomb()
            self.hitBombP2()

            self.explosions.update(30)
            self.explosions.draw(self._frame_surface)    
        
    def runZen(self):
        self.retryMode = 'zen'
        self.prevMode = 'zen'
        #draw, score, timer, lives
        # lives and x's
        margin = 10
        #score
        scoreMellon = pygame.transform.scale(self.scoreMellon, (250,250))
        self._frame_surface.blit(scoreMellon, (margin, margin))
        txt = pygame.font.Font('freesansbold.ttf',150)
        TextSurf=txt.render(str(self.score),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (margin*2+250,50))
        back = pygame.transform.scale(self.back, (150,150))
        self._frame_surface.blit(back, (1920-160, 10))

        rightX = self.p1rx
        rightY = self.p1ry
        leftX = self.p1lx
        leftY = self.p1ly

        # player is done playing 
        if ((rightX >= 1920-160 and rightX <= 1920-10 and
            rightY >=10 and rightY <= 160) or 
            (leftX >= 1920-160 and leftX <= 1920-10 and
             leftY >=10 and leftY <= 160)):
               
                # reset
                self.reset()
                self.lives = 3
                self.startTime = 0
                self.score = 0
                self.totalLaunches = 0                    
                self.fruitLaunchTime = 3
                self.minFruit = 1
                self.maxFruit = 2
                self.maxBombChance = 5
                self.mode = 'intro'
                self.prevMode = 'intro'
                print('here')
         
        if self.easterEgg == True:
                headW, headH = self.kozHead.get_size()    
                self._frame_surface.blit(self.kozHead, (self.headConvertX-headW//2, self.headConvertY-headH//2))   
                           
        if self.ai == True:
            self.scanBody()
            self.blitFruit()   
            self.drawLines()
            self.drawLives()
            if self.easterEgg == True:
                headW, headH = self.kozHead.get_size()    
                self._frame_surface.blit(self.kozHead, (self.headConvertX-headW//2, self.headConvertY-headH//2))   
        
        elif self.mode != 'help':
            # gravity and angle of fruit  
            for fruit in self.imageFruit:
                fruit.y -= fruit.v
                fruit.v -= self.gravity
                fruit.x += fruit.vx

            # bomb physics
            for bomb in self.bombs:
                bomb.y -= bomb.v
                bomb.v -= self.gravity
                bomb.x += bomb.vx
        
            # game logic 
            if self.totalLaunches <= 10:
                if self.totalLaunches<=5:
                    if self.totalLaunches == 0:
                        pass
                    else:
                        self.maxFruit = self.totalLaunches
            if self.totalLaunches>10 and self.fruitLaunchTime == 3:
                self.fruitLaunchTime = 2
                self.minFruit = 3
                self.maxFruit = 10
                self.maxBombChance = 4
            if self.totalLaunches >= 20:
                self.fruitLaunchTime = 1        

            gameClock = (pygame.time.get_ticks()-self.startTime)/1000
            if gameClock > 2 and gameClock% self.fruitLaunchTime < .01:
                rand = random.randint(self.minFruit,self.maxFruit)
                self.launchFruit(rand)

                bombChance = random.randint(1,self.maxBombChance)
                if bombChance == 2:
                    type = random.randint(0,1)
                    self.makeBomb(1)                                                            
            
            self.scanBody()            

            self.blitFruit()        
            self.cleanFruit()
            self.hitFruit()
            self.player2HitFruit() 
            self.player3HitFruit()   
            self.player4HitFruit()   
            self.player5HitFruit()   
            self.player6HitFruit()      
            
            self.blitBomb()
            self.cleanBomb()
            self.hitBomb()
            self.hitBombP2()

            self.explosions.update(30)
            self.explosions.draw(self._frame_surface)   

    def runVS(self):
        self.retryMode = 'vs'
        self.prevMode = 'vs'
        #draw, score, timer        
        margin = 10
        # player 1 score
        
        self.whoWon()

        manW, manH = self.oldMan1.get_size()

        self._frame_surface.blit(self.oldMan1, (margin, margin))
        txt = pygame.font.Font('freesansbold.ttf',150)
        TextSurf=txt.render(str(self.p1score),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (300,50))

        # player 2 score       
        self._frame_surface.blit(self.oldMan2, (1920-manW, margin))
        txt = pygame.font.Font('freesansbold.ttf',150)
        TextSurf=txt.render(str(self.p2score),True,(255,255,255))
        self._frame_surface.blit(TextSurf, (1920 -margin*2-manW,50))

        txt = pygame.font.Font('freesansbold.ttf',100)
        TextSurf=txt.render('First to 50 WINS',True,(0,0,0))
        self._frame_surface.blit(TextSurf, (600,50))
        
        rightX = self.p1rx
        rightY = self.p1ry
        leftX = self.p1lx
        leftY = self.p1ly       
              
        if self.mode != 'help':
            # gravity and angle of fruit  
            for fruit in self.imageFruit:
                fruit.y -= fruit.v
                fruit.v -= self.gravity
                fruit.x += fruit.vx

            # bomb physics
            for bomb in self.bombs:
                bomb.y -= bomb.v
                bomb.v -= self.gravity
                bomb.x += bomb.vx
        
            # game logic 
            if self.totalLaunches <= 10:
                if self.totalLaunches<=5:
                    if self.totalLaunches == 0:
                        pass
                    else:
                        self.maxFruit = self.totalLaunches
            if self.totalLaunches>10 and self.fruitLaunchTime == 3:
                self.fruitLaunchTime = 2
                self.minFruit = 3
                self.maxFruit = 10
                self.maxBombChance = 4
            if self.totalLaunches >= 20:
                self.fruitLaunchTime = 1        

            gameClock = (pygame.time.get_ticks()-self.startTime)/1000
            if gameClock > 2 and gameClock% self.fruitLaunchTime < .01:
                rand = random.randint(self.minFruit,self.maxFruit)
                self.launchFruit(rand)

                bombChance = random.randint(1,self.maxBombChance)
                if bombChance == 2:
                    type = random.randint(0,1)
                    self.makeBomb(1)                                                            
            
                     
 
            self.scanBody()            

            self.blitFruit()        
            self.cleanFruit()
            self.hitFruit()
            self.player2HitFruit() 
            self.player3HitFruit()   
            self.player4HitFruit()   
            self.player5HitFruit()   
            self.player6HitFruit()      
            
            self.blitBomb()
            self.cleanBomb()
            self.hitBomb()
            self.hitBombP2()

            self.explosions.update(30)
            self.explosions.draw(self._frame_surface)                
             
class fruit(pygame.sprite.Sprite):
    @staticmethod
    #initialize the fruit and it's images only once 
    def start():
        banana = pygame.image.load('fruits/Banana.png')
        greenApple = pygame.image.load('fruits/Green_Apple.png')
        mango = pygame.image.load('fruits/Mango.png')
        pear = pygame.image.load('fruits/Pear.png')
        pineapple = pygame.image.load('fruits/Pineapple.png')
        watermelon = pygame.image.load('fruits/Watermelon.png')
        strawberry = pygame.image.load('fruits/Strawberry.png')
        orange = pygame.image.load('fruits/Orange.png')

        fruit.images = [banana, greenApple, mango, pear, pineapple, watermelon, strawberry, orange]
        
    def __init__(self, x, y, v, vx):
        super(fruit, self).__init__()
        image = random.choice(fruit.images)
        self.w, self.h = image.get_size()
        self.image = image
        self.x = x 
        self.y = y 
        # initial velocity 
        self.v = v 
        self.vx = vx

class bomb(pygame.sprite.Sprite):
    @staticmethod
    #initialize the fruit and it's images only once 
    def start():
        classicBomb = pygame.image.load('bombs/classicBomb.png')
        arcadeBomb = pygame.image.load('bombs/arcadeBomb.png')

        bomb.images = [classicBomb, arcadeBomb]
    
    def __init__(self, bombType, x,y,v,vx):
        super(bomb, self).__init__()
        self.bombType = bombType
        image = bomb.images[bombType]
        self.w, self.h = image.get_size()
        self.image = image
        self.x = x 
        self.y = y 
        # initial velocity 
        self.v = v 
        self.vx = vx

'''
Adapted from:
Lukas Peraza, 2016 for 15-112 Pygame Lecture
'''
class Explosion(pygame.sprite.Sprite):
    @staticmethod
    def start():
        image = pygame.image.load('explosion.png')
        rows, cols = 5, 5
        width, height = image.get_size()
        cellWidth, cellHeight = width / cols, height / rows
        Explosion.frames = []
        for i in range(rows):
            for j in range(cols):
                subImage = image.subsurface(
                    (j * cellWidth, i * cellHeight, cellWidth, cellHeight))
                newSub = pygame.transform.scale(subImage, (200,200))
                Explosion.frames.append(newSub)

    def __init__(self, x, y):
        super(Explosion, self).__init__()

        self.x, self.y = x, y
        self.frame = 0
        self.frameRate = 20
        self.aliveTime = 0

        self.updateImage()

    def updateImage(self):
        self.image = Explosion.frames[self.frame]
        w, h = self.image.get_size()
        self.rect = pygame.Rect(self.x - w / 2, self.y - h / 2, w, h)

    def update(self, dt):
        self.aliveTime += dt
        self.frame = self.aliveTime // (1000 // self.frameRate)
        if self.frame < len(Explosion.frames):
            self.updateImage()
        else:
            self.kill()
               
game = GameRuntime();
game.run()
