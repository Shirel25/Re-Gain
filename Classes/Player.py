import pygame
from Classes.Config import Y_GROUND, WIDTH, JUMP_STRENGTH


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x=160, pos_y=Y_GROUND):
        super().__init__()

        # walk mechanisms
        self.walk = [
            pygame.transform.rotozoom(pygame.image.load('Graphics/Player/player_walk_1.png').convert_alpha(), 0, 1.5),  
            pygame.transform.rotozoom(pygame.image.load('Graphics/Player/player_walk_2.png').convert_alpha(), 0, 1.5)
        ]
        self.walk_index = 0
        self.moving = False
        
        # starting point : standing position
        self.stand = pygame.transform.rotozoom(pygame.image.load('Graphics/Player/player_stand.png').convert_alpha(), 0, 1.5)
        self.image = self.stand
        self.rect = self.image.get_rect(midbottom=(pos_x, pos_y))

        # jump mechanisms
        self.jump = pygame.transform.rotozoom(pygame.image.load('Graphics/Player/jump.png').convert_alpha(), 0, 1.5)
        self.gravity = 0
        self.hitbox = self.rect.inflate(-26, -18)


    def player_input(self):
        keys = pygame.key.get_pressed()
        self.moving = False

        if keys[pygame.K_RIGHT]:
            if self.rect.right <= WIDTH:
                self.moving = True 

        if keys[pygame.K_SPACE]:
            if self.rect.bottom == Y_GROUND:
                self.gravity = -JUMP_STRENGTH


    def handle_movement(self):
        self.image = self.stand

        # Gravity for jumping
        if self.rect.bottom < Y_GROUND:
            self.gravity += 1
            self.rect.y += self.gravity
            self.image = self.jump

        elif self.rect.bottom == Y_GROUND:
            if self.gravity < 0: # first frame of jump
                self.gravity += 1
                self.rect.y += self.gravity
                self.image = self.jump

            if self.moving: # walking animation
                self.walk_index += 0.1
                if self.walk_index >= len(self.walk):
                    self.walk_index = 0
                self.image = self.walk[int(self.walk_index)]

        # Neutral position
        else:  
            self.rect.bottom = Y_GROUND

        self.hitbox.midbottom = self.rect.midbottom


    def update(self):
        self.player_input()
        self.handle_movement()