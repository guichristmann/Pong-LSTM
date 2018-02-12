# this version uses only keyboard controls
import numpy as np
from keras.models import load_model
import pygame
from time import sleep
from pygame.locals import *
import sys
import math
import random

TICKS = 0

INPUT_THRESHOLD = 0.95

HISTORY_SIZE = 30
history_i = 0
HISTORY = [None] * HISTORY_SIZE

# colors
BACKGROUND = (44, 62, 80) # #4CD4B0
BALL = (236, 240, 241) # EDD834
PADDLE1_COLOR = (39, 174, 96) # 7D1424
PADDLE2_COLOR = (39, 174, 96)
TEXT = (231, 76, 60)

# screen and general constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# game objects constants
PADDLE_BOUNDARY_OFFSET = int(0.0625 * SCREEN_WIDTH) # how many pixels the paddle is away from the border of the screen
PADDLE_SPEED = int(0.015 * SCREEN_HEIGHT)
PADDLE_WIDTH = int(0.025 * SCREEN_WIDTH)
PADDLE_HEIGHT = int(0.2 * SCREEN_HEIGHT)
BALL_RADIUS = int(0.008 * (SCREEN_WIDTH + SCREEN_HEIGHT))
BALL_ACCEL = 0.5
BALL_START_SPEED = 5.
BALL_MAX_SPEED = 12.


class Ball():
    def __init__(self):
        self.pos = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        self.vel_x = 0.
        self.vel_y = 0.
        self.cur_speed = BALL_START_SPEED

    def moveBall(self):
        if self.pos[1] + self.vel_y > SCREEN_HEIGHT - BALL_RADIUS:  
            self.vel_y = - self.vel_y
        elif self.pos[1] + self.vel_y < BALL_RADIUS:
            self.vel_y = - self.vel_y

        self.pos = (int(self.pos[0] + self.vel_x), int(self.pos[1] + self.vel_y))

    def updateBall(self):
        self.moveBall()

class Paddle():
    def __init__(self, x_pos, cpu=False):
        self.width = PADDLE_WIDTH
        self.length = PADDLE_HEIGHT

        self.cpu = cpu

        self.speed = PADDLE_SPEED

        self.pos = (x_pos, SCREEN_HEIGHT/2)

    def moveUp(self):
        if not self.pos[1] - PADDLE_SPEED - self.length/2 <= 0:
            self.pos = (self.pos[0], self.pos[1] - PADDLE_SPEED)

    def moveDown(self):
        if not self.pos[1] + PADDLE_SPEED + self.length/2 >= SCREEN_HEIGHT:
            self.pos = (self.pos[0], self.pos[1] + PADDLE_SPEED)

    def getRekt(self):
        left = self.pos[0] - self.width/2
        top = self.pos[1] - self.length/2
        return pygame.Rect(left, top, self.width, self.length)

class Pong():
    def __init__(self, sizeX, sizeY, two_players=False, model=None):
        pygame.init()

        self.two_players = two_players

        self.font = pygame.font.Font(None, 80)

        self.state = False

        self.model = model

        self.screen_size = (sizeX, sizeY)
        self.screen = pygame.display.set_mode(self.screen_size) # screen where shit is drawn onto

        self.logInfo = {'ball_x': None, 'ball_y': None, 'vel_x': None, 'vel_y': None,
                        'p1_x': None, 'p1_y': None, 'p2_x': None, 'p2_y': None, 
                        'hit_p1': 0., 'hit_p2': 0., 'p1_up': 0., 'p1_down': 0.,
                        'p2_up': 0., 'p2_down': 0.}        
        
        self.clock = pygame.time.Clock()

        self.resetGame() # initializes all objects needed for the game to run
    
    def restartGame(self):
        # creates both paddles
        self.paddle1 = Paddle(0 + PADDLE_BOUNDARY_OFFSET)

        if self.two_players:
            self.paddle2 = Paddle(SCREEN_WIDTH - PADDLE_BOUNDARY_OFFSET, cpu=False)
        else:
            self.paddle2 = Paddle(SCREEN_WIDTH - PADDLE_BOUNDARY_OFFSET, cpu=True)

        # create ball
        self.ball = Ball()
        # give ball a random move vector
        self.ball.vel_x, self.ball.vel_y = self.newMoveVector(random.random())
        # randomly gives ball a direction, i.e., left or right
        if bool(random.getrandbits(1)):
            self.ball.vel_x = - self.ball.vel_x

    def resetGame(self):
        self.scores = [0] * 2 # set both player scores to 0

        # creates both paddles
        self.paddle1 = Paddle(0 + PADDLE_BOUNDARY_OFFSET)

        if self.two_players:
            self.paddle2 = Paddle(SCREEN_WIDTH - PADDLE_BOUNDARY_OFFSET, cpu=False)
        else:
            self.paddle2 = Paddle(SCREEN_WIDTH - PADDLE_BOUNDARY_OFFSET, cpu=True)

        # create ball
        self.ball = Ball()
        # give ball a random move vector
        self.ball.vel_x, self.ball.vel_y = self.newMoveVector(random.random())
        # randomly gives ball a direction, i.e., left or right
        if bool(random.getrandbits(1)):
            self.ball.vel_x = - self.ball.vel_x

    def resetLogInfo(self):
        self.logInfo = {'ball_x': None, 'ball_y': None, 'vel_x': None, 'vel_y': None,
                        'p1_x': None, 'p1_y': None, 'p2_x': None, 'p2_y': None, 
                        'hit_p1': 0., 'hit_p2': 0., 'p1_up': 0., 'p1_down': 0.,
                        'p2_up': 0., 'p2_down': 0.}

    def handleInput(self):
        # handles key presses
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(1)

        keys = pygame.key.get_pressed()
        if keys[K_s]:
            self.paddle1.moveDown()
            self.logInfo['p1_down'] = 1.
        elif keys[K_w]:
            self.paddle1.moveUp()
            self.logInfo['p1_up'] = 1.
        elif keys[K_r]:
            self.resetGame()

        if self.paddle2.cpu:
            if self.ball.pos[1] > self.paddle2.pos[1]:
                self.paddle2.moveDown()
                self.logInfo['p2_down'] = 1.
            elif self.ball.pos[1] < self.paddle2.pos[1]:
                self.paddle2.moveUp()
                self.logInfo['p2_up'] = 1.
            else:
                pass
        else:
            if keys[K_UP]:
                self.paddle2.moveUp()
                self.logInfo['p2_up'] = 1.
            elif keys[K_DOWN]:
                self.paddle2.moveDown()
                self.logInfo['p2_down'] = 1. 

        # save ball information
        self.logInfo['ball_x'] = self.ball.pos[0]/float(SCREEN_WIDTH)
        self.logInfo['ball_y'] = self.ball.pos[1]/float(SCREEN_HEIGHT)
        self.logInfo['vel_x'] = self.ball.vel_x/BALL_MAX_SPEED
        self.logInfo['vel_y'] = self.ball.vel_y/BALL_MAX_SPEED
        self.logInfo['p1_x'] = self.paddle1.pos[0]/float(SCREEN_WIDTH)
        self.logInfo['p1_y'] = self.paddle1.pos[1]/float(SCREEN_HEIGHT)
        self.logInfo['p2_x'] = self.paddle2.pos[0]/float(SCREEN_WIDTH)
        self.logInfo['p2_y'] = self.paddle2.pos[1]/float(SCREEN_HEIGHT)

    def LSTM_Input(self):
        last_states = np.array(HISTORY[history_i:] + HISTORY[:history_i])
        next_frame = self.model.predict(last_states.reshape(1, last_states.shape[0], last_states.shape[1]))

        #print next_frame[0][8], next_frame[0][9]
        if next_frame[0][8] > INPUT_THRESHOLD:
            print "P1_HIT Predicted"
            self.logInfo['hit_p1'] = 1.
        if next_frame[0][9] > INPUT_THRESHOLD:
            print "P2_HIT Predicted"
            self.logInfo['hit_p2'] = 1.

        #print next_frame[0][0], self.ball.pos[0] / float(SCREEN_WIDTH)
        #print next_frame[0][1], self.ball.pos[1] / float(SCREEN_HEIGHT)

        #print next_frame[0][4], next_frame[0][6]
        self.paddle1.pos = (next_frame[0][4] * SCREEN_WIDTH, next_frame[0][5] * SCREEN_HEIGHT)
        self.paddle2.pos = (next_frame[0][6] * SCREEN_WIDTH, next_frame[0][7] * SCREEN_HEIGHT)
        self.ball.pos = (next_frame[0][0] * SCREEN_WIDTH, next_frame[0][1] * SCREEN_HEIGHT)
        self.ball.vel_x = next_frame[0][2] * BALL_MAX_SPEED
        self.ball.vel_y = next_frame[0][3] * BALL_MAX_SPEED

        #print "P1 Up-Down:", next_frame[0][0], next_frame[0][1]
        #print "P2 Up-Down:", next_frame[0][2], next_frame[0][3]
        if next_frame[0][10] > INPUT_THRESHOLD:
            self.paddle1.moveUp()
            print 'P1_UP'
            self.logInfo['p1_up'] = 1.
        if next_frame[0][11] > INPUT_THRESHOLD:
            self.paddle1.moveDown()
            print 'P1_DOWN'
            self.logInfo['p1_down'] = 1. 

        if next_frame[0][12] > INPUT_THRESHOLD:
            self.paddle2.moveUp()
            print 'P2_UP'
            self.logInfo['p2_up'] = 1.

        if next_frame[0][13] > INPUT_THRESHOLD:
            self.paddle2.moveDown()
            print 'P2_DOWN'
            self.logInfo['p2_down'] = 1. 

    def checkCollision(self, paddle): # checks if ball has hit a paddle
        if abs(self.ball.pos[0] - paddle.pos[0]) < BALL_RADIUS + 1 + PADDLE_WIDTH/2 and\
           self.ball.pos[1] - BALL_RADIUS + 1 <= paddle.pos[1] + paddle.length/2 + 2 and\
           self.ball.pos[1] >= paddle.pos[1] - paddle.length/2 - BALL_RADIUS + 1:
            
            collision_height = self.ball.pos[1] - paddle.pos[1] + PADDLE_HEIGHT/2
            per = float(collision_height) / PADDLE_HEIGHT

            if per < 0.:
                per = 0.
            if per > 1.:
                per = 1.

            return per

        else: # no collision occured
            return None

    def madePoint(self):
        if self.ball.pos[0] < PADDLE_BOUNDARY_OFFSET:
            return 1
        elif self.ball.pos[0] > SCREEN_WIDTH - PADDLE_BOUNDARY_OFFSET:
            return 2
        else:
            return 0

    def newMoveVector(self, v):
        angle = + (math.pi/2 * v - math.pi/4)

        if not self.ball.cur_speed == BALL_MAX_SPEED:
            self.ball.cur_speed += BALL_ACCEL

        return (self.ball.cur_speed * math.cos(angle), self.ball.cur_speed * math.sin(angle))


    def updateGame(self):
        self.ball.updateBall() # updates ball position

        # checks if ball collided against paddles and calculates new direction
        #v = self.checkCollision(self.paddle1)
        #if v:
        #    #self.ball.vel_x, self.ball.vel_y = self.newMoveVector(v)
        #    self.logInfo['hit_p1'] = 1.

        #v = self.checkCollision(self.paddle2)
        #if v: 
        #    #self.ball.vel_x, self.ball.vel_y = self.newMoveVector(v)
        #    #self.ball.vel_x = -self.ball.vel_x
        #    self.logInfo['hit_p2'] = 1.
        #       
        ## checks if someone scored a point
        #if self.madePoint() == 1:
        #    self.scores[1] += 1
        #    self.restartGame()
        #elif self.madePoint() == 2:
        #    self.scores[0] += 1
        #    self.restartGame()


    def drawBall(self):
        pygame.draw.circle(self.screen, BALL, self.ball.pos, BALL_RADIUS, 0)

    def drawPaddles(self):
        pygame.draw.rect(self.screen, PADDLE1_COLOR, self.paddle1.getRekt())
        pygame.draw.rect(self.screen, PADDLE2_COLOR, self.paddle2.getRekt())

    def drawScore(self):
        p1_score_text = self.font.render(str(self.scores[0]), True, TEXT)
        rect_p1 = p1_score_text.get_rect(center=(int(float(SCREEN_WIDTH*0.075)), 40))

        p2_score_text = self.font.render(str(self.scores[1]), True, TEXT)
        rect_p2 = p2_score_text.get_rect(center=(int(float(SCREEN_WIDTH*0.925)), 40))

        self.screen.blit(p1_score_text, rect_p1)
        self.screen.blit(p2_score_text, rect_p2)


    def drawScreen(self):
        self.screen.fill(BACKGROUND)

        self.drawPaddles()
        self.drawBall()

        self.drawScore()

        pygame.display.flip()

    def write_history(self):
        global HISTORY, history_i

        norm_data = (self.logInfo['ball_x'], self.logInfo['ball_y'], self.logInfo['vel_x'],
                     self.logInfo['vel_y'], self.logInfo['p1_x'], self.logInfo['p1_y'],
                     self.logInfo['p2_x'], self.logInfo['p2_y'], self.logInfo['hit_p1'], 
                     self.logInfo['hit_p2'], self.logInfo['p1_up'], self.logInfo['p1_down'], 
                     self.logInfo['p2_up'], self.logInfo['p2_down'])

        HISTORY[history_i] = np.array(norm_data)

        history_i += 1
        if history_i == HISTORY_SIZE:
            history_i = 0

    def run(self):
        global TICKS
        self.state = True

        while self.state: # while game is running
            self.handleInput() # takes care of input
            if TICKS > HISTORY_SIZE:
                self.LSTM_Input() # LSTM takes care of input

            self.updateGame() # updates the state of the game according to input
            self.drawScreen() # updates the screen

            #print self.scores

            self.write_history()
            self.resetLogInfo()

            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit(1)

            self.clock.tick(60)
            TICKS += 1

def calcDistance(p1, p2): # returns distance between two points
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage", sys.argv[0], "<model>"
        sys.exit(1)
    #
    #size = int(sys.argv[1])

    model = load_model(sys.argv[1])

    # if two_players equals True, second player will be cpu controlled
    game = Pong(SCREEN_WIDTH, SCREEN_HEIGHT, two_players=True, model=model)
    game.run()
