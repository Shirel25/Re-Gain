import pygame
from Classes.Config import BACKGROUND_COLOR


class Interface():

    def __init__(self, screen, font):
        super().__init__()

        self.font = font
        self.screen = screen 

        self.start_time = 0
        self.current_score = 0

        self.game_name_surface = self.font.render("Re:Gain", False, BACKGROUND_COLOR)
        self.game_name_rect = self.game_name_surface.get_rect(center = (800, 100))

        self.replay_surface = self.font.render("Press space to replay", False, BACKGROUND_COLOR)
        self.replay_rect = self.replay_surface.get_rect(center = (800, 640))

        self.player_stand_scaled = pygame.transform.rotozoom(pygame.image.load('Graphics/Player/player_stand.png').convert_alpha(), 0, 2)
        self.player_stand_rect = self.player_stand_scaled.get_rect(center = (800, 400))


    def restart(self):
        self.start_time = pygame.time.get_ticks()
        self.current_score = 0


    def update(self, game_active):
        if game_active:
            current_time = pygame.time.get_ticks() - self.start_time
            self.current_score = current_time//1000
            score_surface = self.font.render(f"Score : {self.current_score}", False, "dark green")
            score_rect = score_surface.get_rect(center = (800, 100))
            self.screen.blit(score_surface, score_rect)

        else:
            self.screen.fill("light blue")
            self.screen.blit(self.game_name_surface, self.game_name_rect)
            self.screen.blit(self.player_stand_scaled, self.player_stand_rect)
            self.screen.blit(self.replay_surface, self.replay_rect)  

            score_surface = self.font.render(f"Score : {self.current_score}", False, (111, 196, 169))
            score_rect = score_surface.get_rect(center = (800, 180))
            if self.current_score > 0 : self.screen.blit(score_surface, score_rect)

