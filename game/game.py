import pygame
import sys
import pytmx
import os

from .player import Player
from .treasure import Treasure
from .food import Food
from .pathfinder import Pathfinder
from .hud import HUD
from .communication import SerialComm
from collections import deque



def load_tmx(path):
    return pytmx.util_pygame.load_pygame(path)
SCREEN_WIDTH = 1000  # Extra width for stats sidebar
SCREEN_HEIGHT = 1600
class Game:
    def __init__(self, level=1, pathfinding_algorithm='a_star'):
        pygame.init()
        print("Pygame initialized successfully")

        self.screen = pygame.display.set_mode((1080, 1600))
        
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.clock = pygame.time.Clock()
        # Serial Communication
        self.serial = SerialComm(port='COM5', baudrate=115200, on_message=self.handle_message)
        self.serial.connect()
        # Joystick input queue
        self.joystick_queue = deque()
        
        # Load map
        self.game_level = level
        if self.game_level == 1:
            tmx_path = os.path.join(self.script_dir, "assets/maps/treasure.tmx")
        elif self.game_level == 2:
            tmx_path = os.path.join(self.script_dir, "assets/maps/forestmaze.tmx")
        self.tmx_data = load_tmx(tmx_path)
        self.MAP_WIDTH = self.tmx_data.width * self.tmx_data.tilewidth
        self.MAP_HEIGHT = self.tmx_data.height * self.tmx_data.tileheight

        # Screen
        self.screen = pygame.display.set_mode((self.MAP_WIDTH + 225, self.MAP_HEIGHT + 200))
        pygame.display.set_caption("TMX Game Example")

        # Layers
        self.collision_layer = self.tmx_data.get_layer_by_name("Tile Layer 2")
        self.energy_layer = self.tmx_data.get_layer_by_name("Tile Layer 3")
        self.object_layer = self.tmx_data.get_layer_by_name("Object Layer 1")

        # Player
        player_img = os.path.join(self.script_dir, "assets/sprites/Inspector/SeparateAnim/Walk.png")
        if self.game_level == 1:
            self.player = Player(player_img, 1, 1, self.tmx_data)
        elif self.game_level == 2:
            self.player = Player(player_img, 13, 29, self.tmx_data)

        # Treasures
        treasure_img = pygame.image.load(os.path.join(self.script_dir, "assets/sprites/tile_0089.png")).convert_alpha()
        self.treasures = [Treasure(obj, treasure_img, self.tmx_data) 
                          for obj in self.object_layer if obj.properties.get("item_type")=="treasure"]

        # Food
        food_img_path = os.path.join(self.script_dir, os.pardir, "Ninja Adventure - Asset Pack", "Ninja Adventure - Asset Pack", "Items", "Food", "Meat.png")
        food_img = pygame.image.load(food_img_path).convert_alpha()
        self.foods = [Food(obj, food_img, self.tmx_data)
                      for obj in self.object_layer if obj.properties.get("item_type")=="food"]

        # Pathfinder
        self.pathfinder = Pathfinder(self.tmx_data, self.collision_layer, self.energy_layer)
        self.pathfinding_algorithms = ['bfs', 'a_star', 'greedy_best_first', 'dijkstra', 'a_star_with_food']
        self.pathfinding_algorithm_index = 1  # Default to a_star
        self.pathfinding_algorithm = self.pathfinding_algorithms[self.pathfinding_algorithm_index]
        self.current_path = None
        self.current_stats = None
        self.stats_memory = {}  # keeps last stats for HUD

        # HUD
        font_path = os.path.join(self.script_dir, "assets", "fonts", "NormalFont.ttf")
        self.font = pygame.font.Font(font_path, 20)
        self.hud = HUD(self.font, 200, self.MAP_HEIGHT, self.MAP_WIDTH)

        # AI
        self.AUTO_MOVE = False
        self.MOVE_DELAY = 500
        self.last_move_time = 0

        # Messages
        self.success_message = ""
        self.message_timer = 0
        self.game_over = False
        self.won = False
        self.food_collected = 0


    def handle_message(self, msg):
        """Handles joystick and other STM32 messages."""
        if len(msg) == 1 and msg in "UDLRB":  # Single char joystick
            self.joystick_queue.append(msg)
            print(f"🕹️ Joystick: {msg}")
        elif msg.startswith("F:"):
            food_value = msg.split(":")[1]
            print(f"📥 STM32 echoed - Food: {food_value}")
        elif msg.startswith("S:"):
            status = msg.split(":")[1]
            print(f"📥 STM32 echoed - Status: {status}")
        else:
            print(f"📥 STM32: {msg}")
    def find_nearest_treasure(self):
        nearest_path = None
        nearest_distance = float('inf')
        nearest_stats = None

        # Get the actual pathfinding method from the pathfinder object
        pathfinding_method = getattr(self.pathfinder, self.pathfinding_algorithm)

        for treasure in self.treasures:
            if not treasure.collected:
                goal_tile = (treasure.rect.x // self.tmx_data.tilewidth,
                             treasure.rect.y // self.tmx_data.tileheight)
                start_tile = (self.player.tile_x, self.player.tile_y)

                # Prepare arguments for the pathfinding call
                args = [start_tile, goal_tile]
                if self.pathfinding_algorithm == 'a_star_with_food':
                    food_positions = {
                        (f.rect.x // self.tmx_data.tilewidth, f.rect.y // self.tmx_data.tileheight)
                        for f in self.foods if not f.collected
                    }
                    args.extend([food_positions, self.player.energy])

                path = pathfinding_method(*args)
                
                if path and len(path) < nearest_distance:
                    nearest_path = path
                    nearest_stats = self.pathfinder.stats.copy()
                    nearest_distance = len(path)
        return nearest_path, nearest_stats

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.serial.close()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.__init__()
                    if event.key == pygame.K_n and self.won:
                
                        self.__init__(level=self.game_level)
                    if not self.game_over:
                        if event.key == pygame.K_a:
                            # Cycle to next algorithm
                            self.pathfinding_algorithm_index = (self.pathfinding_algorithm_index + 1) % len(self.pathfinding_algorithms)
                            self.pathfinding_algorithm = self.pathfinding_algorithms[self.pathfinding_algorithm_index]
                            print(f"Pathfinding Algorithm switched to: {self.pathfinding_algorithm}")

                            if self.AUTO_MOVE:
                                self.current_path, self.current_stats = self.find_nearest_treasure()

                        elif event.key == pygame.K_SPACE:
                            self.AUTO_MOVE = not self.AUTO_MOVE
                            if self.AUTO_MOVE:
                                self.current_path, self.current_stats = self.find_nearest_treasure()
                                self.serial.send(f"E:{int(self.player.energy)}")

                        elif not self.AUTO_MOVE:
                            new_x, new_y = self.player.tile_x, self.player.tile_y
                            moved = False

                            if event.key == pygame.K_UP:
                                new_y -= 1
                                moved = True
                            elif event.key == pygame.K_DOWN:
                                new_y += 1
                                moved = True
                            elif event.key == pygame.K_LEFT:
                                new_x -= 1
                                moved = True
                            elif event.key == pygame.K_RIGHT:
                                new_x += 1
                                moved = True

                            if moved:
                                self.player.move_to_tile(new_x, new_y, self.collision_layer, self.energy_layer)
                                self.serial.send(f"E:{int(self.player.energy)}")

            if not self.game_over and self.joystick_queue:
                move = self.joystick_queue.popleft() if self.joystick_queue else None
                if move == 'B':
                    self.AUTO_MOVE = not self.AUTO_MOVE
                    if self.AUTO_MOVE:
                        self.current_path, self.current_stats = self.find_nearest_treasure()
                        self.serial.send(f"E:{int(self.player.energy)}")  
                else:  
                    if not self.AUTO_MOVE:
                        new_x, new_y = self.player.tile_x, self.player.tile_y
                        if move == 'U': new_y -= 1
                        elif move == 'D': new_y += 1
                        elif move == 'L': new_x -= 1
                        elif move == 'R': new_x += 1
                        self.player.move_to_tile(new_x, new_y, self.collision_layer, self.energy_layer)
                        self.serial.send(f"E:{int(self.player.energy)}")

            if not self.game_over:
                self.player.is_moving = False

                # AI movement
                if self.AUTO_MOVE and current_time - self.last_move_time >= self.MOVE_DELAY and self.current_path:
                    if len(self.current_path) > 1:
                        next_x, next_y = self.current_path[1]
                        if self.player.move_to_tile(next_x, next_y, self.collision_layer, self.energy_layer):
                            self.last_move_time = current_time
                            self.current_path.pop(0)
                            self.serial.send(f"E:{int(self.player.energy)}")
                    else:
                        self.current_path, self.current_stats = self.find_nearest_treasure()

                # Update player animation
                self.player.update_animation()

                if self.player.is_dead:
                    self.game_over = True

            # Drawing
            self.screen.fill((0, 0, 0))
            for layer in self.tmx_data.visible_layers:
                if isinstance(layer, pytmx.TiledTileLayer):
                    for x, y, gid in layer:
                        tile = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            self.screen.blit(tile, (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight))

            if not self.game_over:
                for treasure in self.treasures:
                    treasure.draw(self.screen)
                    if not treasure.collected and self.player.rect.colliderect(treasure.rect):
                        treasure.collected = True
                        self.success_message = "Treasure Collected!"
                        self.message_timer = pygame.time.get_ticks()
                        self.serial.send("S:Treasure Found")
                        if self.AUTO_MOVE:
                            self.current_path, self.current_stats = self.find_nearest_treasure()
                        if all(t.collected for t in self.treasures):
                            self.won = True
                            self.success_message = "All Treasures Collected! You Win!"
                            self.serial.send("S:All Treasures Collected")
                            self.game_level += 1

                for food in self.foods:
                    food.draw(self.screen)
                    if not food.collected and self.player.rect.colliderect(food.rect):
                        food.collected = True
                        self.food_collected += 1
                        self.player.energy = min(100, self.player.energy + 4)
                        self.success_message = "Food Collected!"
                        self.message_timer = pygame.time.get_ticks()

                        self.serial.send(f"F:{self.food_collected}")
                        self.serial.send(f"E:{int(self.player.energy)}")

                if self.current_stats:
                    self.stats_memory = self.current_stats.copy()

                if self.current_path:
                    path_surface = pygame.Surface((self.MAP_WIDTH, self.MAP_HEIGHT), pygame.SRCALPHA)
                    for px, py in self.current_path[1:]:
                        rect = pygame.Rect(px * self.tmx_data.tilewidth, py * self.tmx_data.tileheight,
                                           self.tmx_data.tilewidth, self.tmx_data.tileheight)
                        pygame.draw.rect(path_surface, (0, 0, 255, 128), rect)
                    self.screen.blit(path_surface, (0, 0))

                self.player.draw(self.screen)

            elapsed = (pygame.time.get_ticks() - self.message_timer) / 1000
            message = self.success_message if elapsed < 2 else ""
            self.hud.draw(self.screen, self.player, self.AUTO_MOVE, self.stats_memory, self.food_collected, message, self.pathfinding_algorithm)
            # self.hud.draw_sidebar(self.screen, self.player, self.AUTO_MOVE,  self.food_collected)
            # self.hud.draw_bottom_bar(self.screen, self.stats_memory, self.pathfinding_algorithm, message)
            if self.game_over:
                font = pygame.font.Font(None, 74)
                text = font.render("GAME OVER", True, (255, 0, 0))
                text_rect = text.get_rect(center=(self.MAP_WIDTH / 2, self.MAP_HEIGHT / 2))
                self.screen.blit(text, text_rect)
                font = pygame.font.Font(None, 36)
                text = font.render("Press 'R' to restart", True, (255, 255, 255))
                text_rect = text.get_rect(center=(self.MAP_WIDTH / 2, self.MAP_HEIGHT / 2 + 50))
                self.screen.blit(text, text_rect)

            if self.won:
                font = pygame.font.Font(None, 74)
                text = font.render("YOU WIN!", True, (0, 255, 0))
                text_rect = text.get_rect(center=(self.MAP_WIDTH / 2, self.MAP_HEIGHT / 2))
                self.screen.blit(text, text_rect)
                font = pygame.font.Font(None, 36)
                text = font.render("Press 'N' to next level", True, (255, 255, 255))
                text_rect = text.get_rect(center=(self.MAP_WIDTH / 2, self.MAP_HEIGHT / 2 + 50))
                self.screen.blit(text, text_rect)
            pygame.display.flip()