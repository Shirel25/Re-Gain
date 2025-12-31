import pygame
import random
from Classes.Config import GROUND_Y

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, type):
        super().__init__()
        y_pos = 0
        if type == 'fly':
            self.frames = [
                pygame.image.load('Graphics/Fly/Fly1.png').convert_alpha(),
                pygame.image.load('Graphics/Fly/Fly2.png').convert_alpha()
            ]
            y_pos = GROUND_Y - 90
        elif type == 'snail':
            self.frames = [
                pygame.image.load('Graphics/Snail/snail1.png').convert_alpha(),
                pygame.image.load('Graphics/Snail/snail2.png').convert_alpha()
            ]
            y_pos = GROUND_Y
            
        self.animation_index = 0
        self.image = self.frames[self.animation_index]
        self.rect = self.image.get_rect(midbottom = (random.randint(900, 1100), y_pos))

    
    def handle_movement(self):
        self.animation_index += 0.1
        if self.animation_index >= len(self.frames):
            self.animation_index = 0
        self.image = self.frames[int(self.animation_index)]

    
    def update(self):
        self.handle_movement()
        self.rect.x -= 6
        self.destroy()

    def destroy(self):
        if self.rect.x < -100:
            self.kill()
