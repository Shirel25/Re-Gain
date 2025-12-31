import pygame
from random import randint, choice
from Classes.Player import Player
from Classes.Obstacle import Obstacle
from Classes.Config import WIDTH, HEIGHT, GROUND_Y

def main():
    pygame.init()
    pygame.display.set_caption("Re:Gain")

    clock = pygame.time.Clock() 
    font = pygame.font.Font('Fonts/Pixeltype.ttf', 50)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    running = True
    game_active = False
    start_time = 0
    current_score = 0

    sky_surface = pygame.image.load('Graphics/Sky.png').convert()
    ground_surface = pygame.image.load('Graphics/ground.png').convert()
    game_name_surface = font.render("Re:Gain", False, (111, 196, 169))
    game_name_rect = game_name_surface.get_rect(center = (400, 50))
    
    score_surface = font.render("Score : 0", False, "dark green")
    score_rect = score_surface.get_rect(center = (400, 50))

    replay_instruction_surface = font.render("Press space to replay", False, (111, 196, 169))
    replay_instruction_rect = replay_instruction_surface.get_rect(center = (400, 320))


    player_stand = pygame.image.load('Graphics/Player/player_stand.png').convert_alpha()
    player_stand_scaled = pygame.transform.rotozoom(player_stand, 0, 2)
    player_stand_rect = player_stand_scaled.get_rect(center = (400, 200))
    
    player = pygame.sprite.GroupSingle()
    player.add(Player())

    obstacle_groupe = pygame.sprite.Group()
    obstacle_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(obstacle_timer, 3000) 


    while running: 

        for event in pygame.event.get(): 

            if event.type == pygame.QUIT:
                running = False
                break
            
            if game_active:

                if event.type == pygame.KEYDOWN:
                    game_active = True

                if event.type == obstacle_timer:
                    obstacle_groupe.add(Obstacle(choice(['fly', 'snail', 'snail', 'snail']))) # 25% fly, 75% snail

            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_active = True
                    start_time = pygame.time.get_ticks()
            
        
        if game_active:
            screen.blit(sky_surface, (0,0))
            screen.blit(ground_surface, (0, GROUND_Y))

            current_time = pygame.time.get_ticks() - start_time
            current_score = current_time//1000
            score_surface = font.render(f"Score : {current_score}", False, "dark green")
            score_rect = score_surface.get_rect(center = (400, 50))
            screen.blit(score_surface, score_rect)

            player.draw(screen)
            player.update()

            obstacle_groupe.draw(screen)
            obstacle_groupe.update()

            if pygame.sprite.spritecollide(player.sprite, obstacle_groupe, False): game_active = False
        
        else:
            screen.fill("light blue")
            screen.blit(game_name_surface, game_name_rect)
            screen.blit(player_stand_scaled, player_stand_rect)
            screen.blit(replay_instruction_surface, replay_instruction_rect)  

            score_surface = font.render(f"Score : {current_score}", False, (111, 196, 169))
            score_rect = score_surface.get_rect(center = (400, 90))
            if current_score > 0 : screen.blit(score_surface, score_rect)

            player.empty()
            player.add(Player())
            obstacle_groupe.empty()
            
        pygame.display.flip() 
        clock.tick(60) 

    pygame.quit()

if __name__ == "__main__":
    main()