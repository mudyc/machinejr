# (c) Matti Katila, 2011, Licenced in GPL

# Machine Jr is a game to drive a big machine.
# It's controls are designed to fit for a young children.

import os, sys
import math
import random
import pygame
from pygame.locals import *
from pygame import Color
from math import radians, degrees, sin, cos

GO_UP = 'goup'
GO_DOWN = 'godown'
CLOSE = 'close'
OPEN = 'open'

def load(f):
    try:
        image = pygame.image.load(f)
    except pygame.error, message:
        print 'Cannot load image:', f
        raise SystemExit, message
    return image.convert_alpha()


class Tree:
    def __init__(self, ground):
        self.x = random.randint(30, 600)
        self.img = load('machines/tree.png')
        self.ground = ground
        self.falling = math.pi/2
        self.d = 1
    def falled(self): return self.d < 1.0

    def blit(self, screen):
        h = screen.get_size()[0]
        for y in range(h):
            if self.ground.get_at((self.x,y)).a > 100:
                break
        s = self.img.get_size()
        mul = (96*3-s[1])*self.d
        pygame.draw.line(screen, Color('brown'), 
                         (self.x,y), 
                         (self.x+cos(self.falling)*mul,y-sin(self.falling)*mul), 4)
        for i in range(s[1]+5, int(96*3*self.d), s[1]/2):
            screen.blit(pygame.transform.rotate(self.img, degrees(-math.pi/2 +self.falling)), 
                        (self.x-s[0]/2+cos(self.falling)*i, 
                         y - s[1]/2 - sin(self.falling)*i))
        for i in range(int((1-self.d)*5)):
            pygame.draw.line(screen, Color('brown'), 
                         (self.x-i*7,y+4), 
                         (self.x-i*7,y+44), 4)
            

            
    def fall(self, angle):
        self.falling = radians(angle)

    def chop(self, d):
        self.d = 1-d
        

class Excavator:
    pass

class Harvester(object):
    SEND = 1
    SAW = 2
    CHOP = 3
    BACK = 4
    
    def __init__(self, game):
        self.img = load('machines/harvester.png')
        self.snd_saw = pygame.mixer.Sound('snd/saw.ogg')
        self.game = game
        self.dist_min = 15
        self.dist = -1
        self.dist_max = 45
        self.state = self.__class__.SEND
        self.t = 0

    def is_hit(self):
        return self.state in [Harvester.SAW, Harvester.CHOP]

    def drive_state(self):
        if self.state == Harvester.SEND:
            if self.dist > 0:
                self.state = Harvester.SAW
            else:
                self.state = Harvester.BACK
        elif self.state == Harvester.SAW:
            self.state = Harvester.CHOP
        elif self.state == Harvester.CHOP:
            self.state = Harvester.BACK
        elif self.state == Harvester.BACK:
            self.dist = -1
            self.state = Harvester.SEND
        self.t = 0

    def do(self):
        self.t += 0.05
        if self.state == Harvester.SEND:
            self.game.snd_njiin.play()
            if self.game.dir > 0:
                x1 = self.game.x+self.img.get_size()[0]
            else:
                x1 = self.game.x
            x2 = x1 + self.game.dir*(self.dist_min+self.t*self.dist_max)
            for t in self.game.trees:
                if not t.falled() and t.x -2 <= x2 <= t.x + 2:
                    self.dist = abs(x2-x1)
                    self.tree = t
                    self.drive_state()
                    break
        if self.state == Harvester.SAW:
            self.snd_saw.play()
            self.tree.fall(90-self.game.dir*90*self.t)
        if self.state == Harvester.CHOP:
            self.tree.chop(self.t)
        if self.state == Harvester.BACK:
            self.game.snd_njiin.play()
        if self.t > 1:
            self.drive_state()

    def draw(self, screen, direction, x,y):
        size = self.img.get_size()
        bw = size[0]
        bh = size[1]

        if direction > 0:
            x0 = x+bw-25
            x1 = x+bw
        else:
            x0 = x+25
            x1 = x
        x2 = x1 + direction*self.dist
 
        pygame.draw.line(screen, Color('black'), 
                         (x0, y-25), (x1,y-bh), 6)

        if self.state == Harvester.SEND:
            x2 = x1 + direction*(self.dist_min+self.t*self.dist_max)
        elif self.state == Harvester.SAW:
            x2 = x1 + direction*self.dist
        elif self.state == Harvester.CHOP:
            x2 = x1 + direction*self.dist
        elif self.state == Harvester.BACK:
            if self.dist > 0:
                x2 = x1 + direction*(self.dist_min + (1-self.t)*(self.dist-self.dist_min))
            else:
                x2 = x1 + direction*(self.dist_min+(1-self.t)*self.dist_max)
        

        pygame.draw.line(screen, Color('black'), 
                         (x2, y-5), (x1,y-bh), 5)

        screen.blit(
            pygame.transform.flip(self.img, 
                                  direction > 0, False), 
            (x, y-bh))

        return (x,y)


class Game:

    def __init__(self):
        pygame.init()
        if '-fs' in sys.argv:
            self.screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption('Machine Jr')
        #pygame.mouse.set_visible(0)

        #background = pygame.Surface(self.screen.get_size())
        #self.bg = background.convert()
        #self.bg.fill((200, 220, 250))

        self.snd_proom = pygame.mixer.Sound('snd/proom.ogg')
        self.snd_njiin = pygame.mixer.Sound('snd/njiin.ogg')
        

        if False:
            self.bg = load('bg/mountain.jpg')
            self.ground = load('tausta.png')
            self.machine = load('kaivuri.png')
        else:
            self.bg = load('bg/forest.jpg')
            self.ground = load('bg/forest_ground.png')
            self.machine = Harvester(self)
            #self.machine = load('machines/harvester.png')

            self.trees = []
            for i in range(random.randint(3,9)):
                self.trees.append(Tree(self.ground))

        self.bucket = load('kauha.png')
        self.x = 30
        self.dir = 1
        self.bstate = GO_DOWN
        self.t = 0 # 0..1
        self.ground_y = None
        self.materials = [] # the ground pixels..
        self.rot = 0

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


    def gforce(self):
        x0 = self.x + 5
        x1 = x0 + 80
        mid_x = x0 + 40
        h = self.machine.img.get_size()[1]
        min_y = self.screen.get_size()[1]
        min_x = -1
        y_highs = {}
        for x in range(x0, x1+1):
            y = self.highest_at(x)
            y_highs[x] = y
            if y < min_y:
                min_y, min_x = y, x

        #self.y = self.set_rot(x0,mid_x, x1, min_y, min_x, y_highs)
        self.y = self.highest_at(min_x)

    def set_rot(self, x0,mid_x, x1, min_y, min_x, y_highs):
        hit = False
        if x0 <= min_x < mid_x:
            print "'-_"
            for ang in range(0,-90, -1):
                length = x1-min_x
                for steps in range(1, length-1):
                    x = min_x + cos(radians(ang))*steps
                    y = min_y - sin(radians(ang))*steps
                    if y_highs[int(x)] < y:
                        if x0 < x < mid_x: 
                            min_x = x
                            min_y = y_highs[int(x)]
                        elif mid_x < x <= x1:
                            hit = True
                            self.rot = ang
                        break
                if hit: 
                    return min_y + sin(radians(ang))*length /2

        elif mid_x < min_x <= x1:
            print "_-'"
            for ang in range(0,-90, -1):
                hit = False
                length = min_x-x0
                for steps in range(1, length-1):
                    x = min_x - cos(radians(ang))*steps
                    y = min_y - sin(radians(ang))*steps
                    if y_highs[int(x)] < y:
                        if mid_x < x < x1: 
                            min_x = x
                            min_y = y_highs[int(x)]
                        elif x0 <= x < mid_x:
                            hit = True
                            self.rot = -ang
                        break
                if hit:
                    return min_y - sin(radians(ang))*length /2
        else:
            self.rot = 0
            return min_y


    def highest_at(self, x):
        h = self.screen.get_size()[0]
        for y in range(h):
            if self.ground.get_at((x,y)).a > 100:
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
            pygame.transform.rotate(
            pygame.transform.flip(self.machine, 
                                  self.dir > 0, False), self.rot), 
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
            #if self.ground_y == None:
            if not self.machine.is_hit():
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
                self.machine.do()
                # self.snd_njiin.play()
                # if self.bstate in [GO_DOWN, GO_UP]:
                #     self.t += 0.05
                # else:
                #     self.t += 0.1

                # if self.t > 1:
                #     self.drive_bstate()

            self.gforce()
            if self.ground_y != None:
                self.dig()
            elif self.bstate == OPEN:
                self.drop()

            self.screen.blit(self.bg, (0,0))
            self.screen.blit(self.ground, (0,0))

            for t in self.trees: 
                t.blit(self.screen)


            # draw the machine
            x,y = self.machine.draw(self.screen, self.dir, self.x, self.y)
            #x,y = self.draw_machine()
            y += self.bucket.get_size()[1]
            if self.bstate == GO_DOWN and self.highest_at(x) < y:
                self.ground_y = self.highest_at(x)
                self.ground_x = x
                self.drive_bstate()
            pygame.display.flip()



if __name__ == '__main__':
    Game().run()
