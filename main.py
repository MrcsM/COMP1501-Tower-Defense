#### ====================================================================================================================== ####
#############                                           IMPORTS                                                    #############
#### ====================================================================================================================== ####

from helper_functions import *
from settings import *
from shop import *
from tower import *
from enemy import *
from map import *
import pygame
import sys
import random
import math

#### ====================================================================================================================== ####
#############                                         INITIALIZE                                                   #############
#### ====================================================================================================================== ####

def initialize():
    ''' Initialization function - initializes various aspects of the game including settings, shop, and more.
    Input: None
    Output: game_data dictionary
    '''
    # Initialize Pygame
    pygame.init()
    pygame.display.set_caption("COMP 1501 - Tutorial 7: Tower Defense (TD) Base Code")

    # Initialize the Settings Object
    settings = Settings()

    # Initialize game_data and return it
    game_data = { "screen": pygame.display.set_mode(settings.window_size),
                  "current_currency": settings.starting_currency,
                  "current_wave": 0,
                  "stay_open": True,
                  "selected_tower": None,
                  "clicked": False,
                  "settings": settings,
                  "towers": [],
                  "enemies": [],
                  "bullets": [],
                  "shop": Shop("Space", settings),
                  "map": Map(settings),
                  "clock": 0, 
                  "health": 1000}

    set_map(game_data["map"])

    return game_data

#### ====================================================================================================================== ####
#############                                           PROCESS                                                    #############
#### ====================================================================================================================== ####

def process(game_data):
    ''' Processing function - handles all form of user input. Raises flags to trigger certain actions in Update().
    Input: game_data dictionary
    Output: None
    '''
    for event in pygame.event.get():

        # Handle [X] press
        if event.type == pygame.QUIT:
            game_data["stay_open"] = False

        # Handle Mouse Button Down
        if event.type == pygame.MOUSEBUTTONDOWN:
            game_data["clicked"] = True

        # Handle Mouse Button Up
        if event.type == pygame.MOUSEBUTTONUP:
            game_data["clicked"] = False


#### ====================================================================================================================== ####
#############                                            UPDATE                                                    #############
#### ====================================================================================================================== ####

def update(game_data):
    ''' Updating function - handles all the modifications to the game_data objects (other than boolean flags).
    Input: game_data
    Output: None
    '''
    update_shop(game_data["shop"], game_data["current_currency"], game_data["settings"])

    if game_data["shop"].clicked_item:
        if not game_data["clicked"]:
            x, y = pygame.mouse.get_pos()
            if check_location(game_data["map"], game_data["settings"], (x, y)):
                if x < 800:
                    tower = Tower(game_data["shop"].clicked_item, (x, y), None)
                    game_data["towers"].append(tower)
                    game_data["current_currency"] -= game_data["shop"].shop_data[game_data["shop"].clicked_item]["cost"]
                    game_data["shop"].clicked_item = None

    if not random.randrange(60):
        types = list(Enemy.enemy_data.keys())
        chosen = random.choice(types)
        enemy = Enemy(chosen, (60, 20))
        game_data["enemies"].append(enemy)
        
    for e in game_data["enemies"]:
        update_enemy(e, game_data["map"])
        if e.health <= 0:
            game_data["enemies"].remove(e)
            game_data["current_currency"] += e.enemy_data[e.name]["worth"]
        x, y, val = tileLoc(e.location)
        #print(val)
        if val == "E":
            game_data["enemies"].remove(e)
            game_data["health"] -= 10

    ## Replace this with code to update the Towers ##
    for tower in game_data["towers"]:
        update_tower(tower, game_data["map"])
        tower.last_fire += game_data["clock"].tick()

    for bullet in game_data["bullets"]:
        update_bullet(bullet)

        (x, y) = bullet.location
        (velx, vely) = bullet.velocity

        x += 1 - velx * 10

        if (x < 0) or (x > pygame.display.get_surface().get_width()):
            game_data["bullets"].remove(bullet)
            
        y += 0.5 - vely * 10

        if (y < 0) or (y > pygame.display.get_surface().get_height()):
            game_data["bullets"].remove(bullet)

        bullet.location = (x, y)

        enemy = bullet.goingFor
        (ball_x, ball_y) = bullet.location
        (target_x, target_y) = enemy.location[0] - enemy.size, enemy.location[1] - enemy.size # top left
        (target_brx, target_bry) = enemy.location[0] + enemy.size, enemy.location[1] + enemy.size #bottom right

        if (ball_x > target_x) and (ball_x < target_brx):
            if (ball_y > target_y) and (ball_y < target_bry):
                game_data["bullets"].remove(bullet)
                update_enemy(enemy, game_data["map"], None, bullet.bullet_data["bullet"]["damage"])

    pass # Remove this once you've implemented 'update()'

#### ====================================================================================================================== ####
#############                                            RENDER                                                    #############
#### ====================================================================================================================== ####

def DrawHealthBar(game_data, screen, pos, size):
    if game_data["health"] > 0:
        pygame.draw.rect(screen, (255, 255, 255), (*pos, *size), 1)
        innerPos = (pos[0]+3, pos[1]+3)
        progress = game_data["health"]/100
        innerSize = ((size[0]-6) * progress, size[1]-6)
        pygame.draw.rect(screen, (255, 0, 0), (*innerPos, *innerSize))

        interest_text = pygame.font.SysFont("Arial", 25).render("Health", True, (0, 0, 0))
        text_img = interest_text

        screen.blit(text_img, (280, 710))
    else:
        pygame.draw.rect(screen, (0, 0, 0), (*pos, *size), 1)

def render(game_data):
    ''' Rendering function - displays all objects to screen.
    Input: game_data
    Output: None
    '''
    render_map(game_data["map"], game_data["screen"], game_data["settings"])
    render_shop(game_data["shop"], game_data["screen"], game_data["settings"], game_data["current_currency"])
    for enemy in game_data["enemies"]:
        render_enemy(enemy, game_data["screen"], game_data["settings"])
    for tower in game_data["towers"]:
        render_tower(tower, game_data["screen"], game_data["settings"])
    for bullet in game_data["bullets"]:
        render_bullet(bullet, game_data["screen"])

    for tower in game_data["towers"]:
        for enemy in game_data["enemies"]:
            delta = (tower.location[0] - enemy.location[0], tower.location[1] - enemy.location[1])
            norm = math.sqrt(delta[0] ** 2 + delta[1] ** 2)
            if norm < tower.radius:
                tower.attacking = enemy
                loc = (tower.location[0] + 10, tower.location[1] + 10)
                new_bullet = Bullet(loc, tower)
                if tower.last_fire > 1000:
                    game_data["bullets"].append(new_bullet)
                    tower.last_fire = 0

                rads = math.atan2(delta[1], delta[0])
                degs = abs(((rads * 180) / math.pi)) + 90
                tower.rotation = degs

                break

    DrawHealthBar(game_data, game_data["screen"], (100, 700), (50, 40))
    pygame.display.update()

#### ====================================================================================================================== ####
#############                                             MAIN                                                     #############
#### ====================================================================================================================== ####

def main():
    ''' Main function - initializes everything and then enters the primary game loop.
    Input: None
    Output: None
    '''
    # Initialize all required variables and objects
    game_data = initialize()
    game_data["clock"] = pygame.time.Clock()

    # Begin Central Game Loop
    while game_data["stay_open"]:
        process(game_data)
        update(game_data)
        render(game_data)


    # Exit pygame and Python
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()