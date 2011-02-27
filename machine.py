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


def load(f):
    try:
        image = pygame.image.load(f)
    except pygame.error, message:
        print 'Cannot load image:', f
        raise SystemExit, message
    return image.convert_alpha()

class Log:
    def __init__(self, game, x=-1):
        if x < 0: 
            x = random.randint(30,600)
        self.x = x
        self.game = game
    def draw(self, screen):
        h = screen.get_size()[0]
        for y in range(h):
            if self.game.ground.get_at((self.x,y)).a > 100:
                break
        pygame.draw.line(screen, Color('brown'), 
                         (self.x,y+4), 
                         (self.x,y+44), 4)


class Tree:
    def __init__(self, game):
        self.x = random.randint(30, 600)
        self.img = load('machines/tree.png')
        self.ground = game.ground
        self.game = game
        self.falling = math.pi/2
        self.d = 1
        self.logs = 0
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
            

            
    def fall(self, angle):
        self.falling = radians(angle)

    def chop(self, d):
        self.d = 1-d

        num = int(d*5)
        if num > self.logs:
            self.game.logs.append(Log(self.game, self.x+10-num*7))
            self.logs = num

class Excavator:
    GO_UP = 'goup'
    GO_DOWN = 'godown'
    CLOSE = 'close'
    OPEN = 'open'

    def __init__(self, game):
        self.img = load('machines/kaivuri.png')
        self.bucket = load('machines/kauha.png')
        self.bstate = Excavator.GO_DOWN
        self.t = 0 # 0..1
        self.ground_y = None
        self.materials = [] # the ground pixels..
        self.game = game

    def is_hit(self):
        return self.ground_y != None

    def drive_bstate(self):
        if self.bstate == Excavator.GO_DOWN:
            self.bstate = Excavator.CLOSE
        elif self.bstate == Excavator.CLOSE:
            self.bstate = Excavator.GO_UP
        elif self.bstate == Excavator.GO_UP:
            self.bstate = Excavator.OPEN
            self.ground_y = None
        elif self.bstate == Excavator.OPEN:
            self.bstate = Excavator.GO_DOWN
        self.t = 0

    def do(self):
        self.game.snd_njiin.play()
        if self.bstate in [Excavator.GO_DOWN, Excavator.GO_UP]:
            self.t += 0.05
        else:
            self.t += 0.1

        if self.t > 1:
            self.drive_bstate()

        if self.ground_y != None:
            self.dig()
        elif self.bstate == Excavator.OPEN:
            self.drop()

    def dig(self):
        trans = Color(0,0,0,0)
        if self.bstate == Excavator.CLOSE and self.ground_y != None:
            for x in range(self.ground_x -10, self.ground_x + 10):
                for y in range(0, self.ground_y + 10):
                    color = self.game.ground.get_at((x,y))
                    if color.a > 100:
                        self.materials.append(color)
                    self.game.ground.set_at((x,y), trans)
            
    def drop(self):
        if self.bstate == Excavator.OPEN and self.t >= 0.6 and len(self.materials) > 0:
            random.shuffle(self.materials)
            size = self.img.get_size()
            bw = size[0]

            x = self.game.x + bw/2 + 90 *self.game.dir
            for pixel in self.materials:
                x_pix = random.randint(x -10, x + 10-1)
                self.game.ground.set_at((x_pix,self.game.highest_at(x_pix)-1),pixel)
            self.materials = []


    def draw(self, screen, direction, xx,yy):
        size = self.img.get_size()

        bw = size[0]
        bh = size[1]

        x = xx + bw/2 + 90 *direction
        bottom = yy + bh/2
        if self.ground_y != None:
            bottom = self.ground_y
    
        rot = 0 
        if self.bstate == Excavator.GO_DOWN:
            rot = -90
            y = yy - bh + bh*3/2*self.t
        elif self.bstate == Excavator.CLOSE:
            rot = -90 + self.t*180
            y = bottom
        elif self.bstate == Excavator.GO_UP:
            rot = 90
            y = yy - bh + (bottom-yy+bh)*(1-self.t)
        elif self.bstate == Excavator.OPEN:
            rot = 90 - self.t*180
            y = yy - bh

        pygame.draw.line(screen, Color('yellow'), 
                         (xx+bw/2,yy-bh/2), 
                         (x,y), 5)

        screen.blit(
            pygame.transform.rotate(
            pygame.transform.flip(self.img, 
                                  direction > 0, False), self.game.rot), 
            (xx, yy-bh))
        screen.blit(
            pygame.transform.flip(pygame.transform.rotate(
                self.bucket, rot), 
                                      direction > 0, False), 
            (x, y))

        y += self.bucket.get_size()[1]
        if self.bstate == Excavator.GO_DOWN and self.game.highest_at(x) < y:
            self.ground_y = self.game.highest_at(x)
            self.ground_x = x
            self.drive_bstate()

        return (x,y)


class Forwarder:
    FORW = 1
    CLOSE = 2
    BACK = 3
    OPEN = 4

    def __init__(self, game):
        self.img = load('machines/forwarder.png')
        self.game = game
        self.log = None
        self.logs = []
        self.state = Forwarder.FORW
        self.t = 0
        self.grop_x = -1

    def is_hit(self):
        return self.state == Forwarder.CLOSE

    def drive_state(self):
        if self.state == Forwarder.FORW:
            self.state = Forwarder.CLOSE
        elif self.state == Forwarder.CLOSE:
            self.state = Forwarder.BACK
        elif self.state == Forwarder.BACK:
            self.state = Forwarder.OPEN
        elif self.state == Forwarder.OPEN:
            if self.log != None:
                self.logs.append(self.log)
            self.log = None
            self.state = Forwarder.FORW
        self.t = 0

    def do(self):
        self.t += 0.05
        if self.state in [Forwarder.CLOSE, Forwarder.OPEN]:
            self.t += 0.05
        self.game.snd_njiin.play()

        if self.log == None and self.state == Forwarder.CLOSE:
            for l in self.game.logs:
                if l.x -4 <= self.grop_x <= l.x + 4:
                    self.log = l
                    self.game.logs.remove(l)

        if self.t > 1:
            self.drive_state()

    def draw(self, screen, direction, x,y):
        size = self.img.get_size()
        bw = size[0]
        bh = size[1]

        x0 = x+bw/2

        if self.state == Forwarder.FORW:
            x1 = x0+direction*bw/3 + direction*cos((math.pi*4./5.)*(1-self.t))*bw*2/3
            y1 = y - sin(math.pi*4./5.*(1-self.t))*bh
            a = 0
        elif self.state == Forwarder.OPEN:
            x1 = x0+direction*bw/3 + direction*cos(math.pi*4./5.)*bw*2/3
            y1 = y - sin(math.pi*4./5)*bh
            a = 1-self.t
        elif self.state == Forwarder.BACK:
            x1 = x0+direction*bw/3 + direction*cos((math.pi*4./5.)*self.t)*bw*2/3
            y1 = y - sin(math.pi*4/5.*self.t)*bh
            a = 1
        elif self.state == Forwarder.CLOSE:
            x1 = x0+direction*bw/3 + direction*cos(0)*bw*2/3
            y1 = y - sin(0)*bh
            a = self.t
        self.grop_x = x1

 
        pygame.draw.line(screen, Color('black'), 
                         (x0, y-bh*2/3), 
                         (x1, y1), 6)

        r = Rect(x1-7,y1+1, 15,12)
        pygame.draw.arc(screen, Color('red'), r, math.pi/2., 
                        math.pi+a*math.pi/2, 2)
        if self.log != None:
            pygame.draw.line(screen, Color('brown'), 
                         (x1-20,y1+5), 
                         (x1+20,y1+5), 4)
        pygame.draw.arc(screen, Color('red'), r, 
                        -math.pi/2+(1-a)*math.pi/2, 
                        math.pi/2, 2)

        for i in range(len(self.logs)):
            pygame.draw.line(screen, Color('brown'), 
                         (x0-direction*10,y-27-4*i), 
                         (x0-direction*50,y-27-4*i), 3)
            
        screen.blit(
            pygame.transform.flip(self.img, 
                                  direction > 0, False), 
            (x, y-bh))

        return (x,y)
        

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
        self.state = Harvester.SEND
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
        
        self.dir = 1
        self.rot = 0

        self.logs = []
        self.trees = []

        self.level = 0
        self.next_level()

    def next_level(self):
        self.level += 1
        if self.level == 4: 
            self.level = 1
            self.logs = []

        self.x = 30

        if self.level == 1:
            self.bg = load('bg/mountain.jpg')
            self.ground = load('tausta.png')
            self.machine = Excavator(self)
            dumper = load('machines/dumper.png')
            ys = []
            x0 = self.screen.get_size()[0]-dumper.get_size()[0]
            x1 = self.screen.get_size()[0]
            trans = Color(0,0,0,0)
            for x in range(x0, x1):
                ys.append(self.highest_at(x))
            def check():
                idx=0
                for x in range(x0, x1):
                    for i in range(10):
                        self.ground.set_at((x,ys[idx]-1-i), trans)
                    idx += 1
                                           

                self.screen.blit(dumper, (x0, ys[0]-96))
                return False
            self.check_level = check

        elif self.level == 2:
            self.bg = load('bg/forest.jpg')
            self.ground = load('bg/forest_ground.png')
            self.machine = Harvester(self)

            self.trees = []
            for i in range(random.randint(3,9)):
                self.trees.append(Tree(self))
            def check():
                for t in self.trees: 
                    if t.d > 0.1: return False
                return True
            self.check_level = check
        else:
            self.bg = load('bg/forest.jpg')
            self.ground = load('bg/forest_ground.png')
            self.machine = Forwarder(self)

            if len(self.logs) == 0:
                for i in range(random.randint(10,30)):
                    self.logs.append(Log(self))
        
            def check():
                return len(self.logs) == 0
            self.check_level = check



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



    def run(self):
        while True:
            
            for event in pygame.event.get():
                if event.type == QUIT or \
                        (event.type == KEYUP and event.key == K_ESCAPE):
                    return
            pressed = pygame.key.get_pressed()
            flag = False

            if pressed[K_F2]:
                self.next_level()

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

            self.gforce()

            if flag or pressed[K_SPACE]:
                self.machine.do()

            self.screen.blit(self.bg, (0,0))
            self.screen.blit(self.ground, (0,0))

            for t in self.trees: 
                t.blit(self.screen)
            for l in self.logs:
                l.draw(self.screen)

            # draw the machine
            x,y = self.machine.draw(self.screen, self.dir, self.x, self.y)
            #x,y = self.draw_machine()
            if self.check_level():
                self.next_level()

            pygame.display.flip()



if __name__ == '__main__':
    print 'Contains images from www.freeimages.co.uk'
    #while True:
    #    try:
    Game().run()
    #        break
    #    except:
    #        pass
