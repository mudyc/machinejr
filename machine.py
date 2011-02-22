# (c) Matti Katila, 2011

# Machine Jr is a game to drive a big machine.
# It's controls are designed to fit for a young children.

import os, sys
import pygame
from pygame.locals import *
from pygame import Color



class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption('Machine Jr')
        #pygame.mouse.set_visible(0)

        background = pygame.Surface(self.screen.get_size())
        self.bg = background.convert()
        self.bg.fill((200, 220, 250))

        self.ground = self.load('tausta.png')
        self.machine = self.load('kaivuri.png')
        self.x = 30
        self.dir = 1

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

    def run(self):
        while True:
            
            for event in pygame.event.get():
                if event.type == QUIT or \
                        (event.type == KEYUP and event.key == K_ESCAPE):
                    return
            pressed = pygame.key.get_pressed()
            if pressed[K_LEFT]:
                self.x -= 3
                self.dir = -1
            if pressed[K_RIGHT]:
                self.x += 3
                self.dir = 1
            if pressed[K_SPACE]:
                print '..'

            self.gforce()


            self.screen.blit(self.bg, (0,0))
            self.screen.blit(self.ground, (0,0))
            self.screen.blit(
                pygame.transform.flip(self.machine, self.dir > 0, False), 
                (self.x, self.y-self.machine.get_size()[1]))

            #pygame.draw.line(self.screen, Color('black'), (self.x,self.y), (self.x+80, self.y), 3)
            pygame.display.flip()



if __name__ == '__main__':
    Game().run()
