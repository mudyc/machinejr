# (c) Matti Katila, 2011, Licenced in GPL

# Machine Jr is a game to drive a big machine.
# It's controls are designed to fit for a young children.

import os, sys
import random
import pygame
from pygame.locals import *
from pygame import Color
from math import radians

GO_UP = 'goup'
GO_DOWN = 'godown'
CLOSE = 'close'
OPEN = 'open'


class Game:

    def __init__(self):
        pygame.init()
        #self.screen = pygame.display.set_mode((640, 480))
        self.screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
        pygame.display.set_caption('Machine Jr')
        #pygame.mouse.set_visible(0)

        background = pygame.Surface(self.screen.get_size())
        self.bg = background.convert()
        self.bg.fill((200, 220, 250))

        self.snd_proom = pygame.mixer.Sound('snd/proom.ogg')
        self.snd_njiin = pygame.mixer.Sound('snd/njiin.ogg')
        

        self.ground = self.load('tausta.png')
        self.machine = self.load('kaivuri.png')
        self.bucket = self.load('kauha.png')
        self.x = 30
        self.dir = 1
        self.bstate = GO_DOWN
        self.t = 0 # 0..1
        self.ground_y = None
        self.materials = [] # the ground pixels..

    def drive_bstate(self):
        if self.bstate == GO_DOWN:
            self.bstate = CLOSE
        elif self.bstate == CLOSE:
            self.bstate = GO_UP
        elif self.bstate == GO_UP:
            self.bstate = OPEN
            self.ground_y = None
        elif self.bstate == OPEN:
            self.bstate = GO_DOWN
        self.t = 0

    def load(self, f):
        try:
            image = pygame.image.load(f)
        except pygame.error, message:
            print 'Cannot load image:', f
            raise SystemExit, message
        return image.convert_alpha()

    def gforce(self):
        x0 = self.x + 5
        x1 = x0 + 80
        midx = x0 + 40
        min_y = self.screen.get_size()[1]
        min_x = -1
        for x in range(x0, x1):
            y = self.highest_at(x)
            if y < min_y:
                min_y, min_x = y, x
        self.y = self.highest_at(min_x)

    def highest_at(self, x):
        h = self.screen.get_size()[0]
        for y in range(h):
            if self.ground.get_at((x,y)).a != 0:
                return y
        return 0

    def dig(self):
        trans = Color(0,0,0,0)
        if self.bstate == CLOSE and self.ground_y != None:
            for x in range(self.ground_x -10, self.ground_x + 10):
                for y in range(0, self.ground_y + 10):
                    color = self.ground.get_at((x,y))
                    if color.a > 100:
                        self.materials.append(color)
                    self.ground.set_at((x,y), trans)
            
    def drop(self):
        if self.bstate == OPEN and self.t >= 0.6 and len(self.materials) > 0:
            random.shuffle(self.materials)
            size = self.machine.get_size()
            bw = size[0]

            x = self.x + bw/2 + 90 *self.dir
            for pixel in self.materials:
                x_pix = random.randint(x -10, x + 10-1)
                self.ground.set_at((x_pix,self.highest_at(x_pix)-1),pixel)
            self.materials = []

    def draw_machine(self):
        size = self.machine.get_size()

        bw = size[0]
        bh = size[1]

        x = self.x + bw/2 + 90 *self.dir
        bottom = self.y + bh/2
        if self.ground_y != None:
            bottom = self.ground_y
    
        rot = 0 
        if self.bstate == GO_DOWN:
            rot = -90
            y = self.y - bh + bh*3/2*self.t
        elif self.bstate == CLOSE:
            rot = -90 + self.t*180
            y = bottom
        elif self.bstate == GO_UP:
            rot = 90
            y = self.y - bh + (bottom-self.y+bh)*(1-self.t)
        elif self.bstate == OPEN:
            rot = 90 - self.t*180
            y = self.y - bh

        pygame.draw.line(self.screen, Color('yellow'), 
                         (self.x+bw/2,self.y-bh/2), 
                         (x,y), 5)

        self.screen.blit(
            pygame.transform.flip(self.machine, 
                                  self.dir > 0, False), 
            (self.x, self.y-self.machine.get_size()[1]))
        self.screen.blit(
            pygame.transform.flip(pygame.transform.rotate(
                self.bucket, rot), 
                                      self.dir > 0, False), 
            (x, y))

        return (x,y)


    def run(self):
        while True:
            
            for event in pygame.event.get():
                if event.type == QUIT or \
                        (event.type == KEYUP and event.key == K_ESCAPE):
                    return
            pressed = pygame.key.get_pressed()
            flag = False
            if self.ground_y == None:
                if pressed[K_LEFT]:
                    self.x -= 3
                    self.dir = -1
                    self.snd_proom.play()
                if pressed[K_RIGHT]:
                    self.x += 3
                    self.dir = 1
                    self.snd_proom.play()
            else:
                if pressed[K_LEFT] or pressed[K_RIGHT]:
                    flag = True
            if flag or pressed[K_SPACE]:
                self.snd_njiin.play()
                if self.bstate in [GO_DOWN, GO_UP]:
                    self.t += 0.05
                else:
                    self.t += 0.1

                if self.t > 1:
                    self.drive_bstate()

            self.gforce()
            if self.ground_y != None:
                self.dig()
            elif self.bstate == OPEN:
                self.drop()

            self.screen.blit(self.bg, (0,0))
            self.screen.blit(self.ground, (0,0))

            # draw the machine
            x,y = self.draw_machine()
            y += self.bucket.get_size()[1]
            if self.bstate == GO_DOWN and self.highest_at(x) < y:
                self.ground_y = self.highest_at(x)
                self.ground_x = x
                self.drive_bstate()
            pygame.display.flip()



if __name__ == '__main__':
    Game().run()
