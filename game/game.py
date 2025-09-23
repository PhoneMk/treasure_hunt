import pygame
import sys
import pytmx
import os

from .player import Player
from .treasure import Treasure
from .pathfinder import Pathfinder
from .hud import HUD
from collections import deque

def load_tmx(path):
    return pytmx.util_pygame.load_pygame(path)
SCREEN_WIDTH = 1000  # Extra width for stats sidebar
SCREEN_HEIGHT = 600
class Game:
    def __init__(self):
        pygame.init()
        print("Pygame initialized successfully")

        self.screen = pygame.display.set_mode((800, 600))

        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.clock = pygame.time.Clock()

        # Load map
        tmx_path = os.path.join(self.script_dir, "assets/maps/treasure.tmx")
        self.tmx_data = load_tmx(tmx_path)
        self.MAP_WIDTH = self.tmx_data.width * self.tmx_data.tilewidth
        self.MAP_HEIGHT = self.tmx_data.height * self.tmx_data.tileheight

        # Screen
        self.screen = pygame.display.set_mode((self.MAP_WIDTH + 200, self.MAP_HEIGHT))
        pygame.display.set_caption("TMX Game Example")

        # Layers
        self.collision_layer = self.tmx_data.get_layer_by_name("Tile Layer 2")
        self.energy_layer = self.tmx_data.get_layer_by_name("Tile Layer 3")
        self.object_layer = self.tmx_data.get_layer_by_name("Object Layer 1")

        # Player
        player_img = os.path.join(self.script_dir, "assets/sprites/tile_0109.png")
        self.player = Player(player_img, 0, 0, self.tmx_data)

        # Treasures
        treasure_img = pygame.image.load(os.path.join(self.script_dir, "assets/sprites/tile_0089.png")).convert_alpha()
        self.treasures = [Treasure(obj, treasure_img, self.tmx_data) 
                          for obj in self.object_layer if obj.properties.get("item_type")=="treasure"]

        # Pathfinder
        self.pathfinder = Pathfinder(self.tmx_data, self.collision_layer)
        self.current_path = None
        self.current_stats = None
        self.stats_memory = {}  # keeps last stats for HUD

        # HUD
        font_path = os.path.join(self.script_dir, "assets", "fonts", "NormalFont.ttf")
        self.font = pygame.font.Font(font_path, 20)
        self.hud = HUD(self.font, 200, self.MAP_HEIGHT)

        # AI
        self.AUTO_MOVE = False
        self.MOVE_DELAY = 500
        self.last_move_time = 0

        # Messages
        self.success_message = ""
        self.message_timer = 0

    def find_nearest_treasure(self):
        nearest_path = None
        nearest_distance = float('inf')
        nearest_stats = None

        for treasure in self.treasures:
            if not treasure.collected:
                goal_tile = (treasure.rect.x // self.tmx_data.tilewidth,
                             treasure.rect.y // self.tmx_data.tileheight)
                start_tile = (self.player.tile_x, self.player.tile_y)
                path = self.pathfinder.bfs(start_tile, goal_tile)
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
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.AUTO_MOVE = not self.AUTO_MOVE
                        if self.AUTO_MOVE:
                            self.current_path, self.current_stats = self.find_nearest_treasure()
                    elif not self.AUTO_MOVE:
                        new_x, new_y = self.player.tile_x, self.player.tile_y
                        if event.key == pygame.K_UP: new_y -= 1
                        if event.key == pygame.K_DOWN: new_y += 1
                        if event.key == pygame.K_LEFT: new_x -= 1
                        if event.key == pygame.K_RIGHT: new_x += 1
                        self.player.move_to_tile(new_x, new_y, self.collision_layer, self.energy_layer)

            # AI movement
            if self.AUTO_MOVE and current_time - self.last_move_time >= self.MOVE_DELAY and self.current_path:
                if len(self.current_path) > 1:
                    next_x, next_y = self.current_path[1]
                    if self.player.move_to_tile(next_x, next_y, self.collision_layer, self.energy_layer):
                        self.last_move_time = current_time
                        self.current_path.pop(0)
                else:
                    self.current_path, self.current_stats = self.find_nearest_treasure()

            # Draw map
            self.screen.fill((0,0,0))
            for layer in self.tmx_data.visible_layers:
                if isinstance(layer, pytmx.TiledTileLayer):
                    for x, y, gid in layer:
                        tile = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            self.screen.blit(tile, (x*self.tmx_data.tilewidth, y*self.tmx_data.tileheight))

            # Draw treasures
            for treasure in self.treasures:
                treasure.draw(self.screen)
                if not treasure.collected and self.player.rect.colliderect(treasure.rect):
                    treasure.collected = True
                    self.success_message = "🎉 Treasure Collected!"
                    self.message_timer = pygame.time.get_ticks()
                    if self.AUTO_MOVE:
                        self.current_path, self.current_stats = self.find_nearest_treasure()

            # Store last stats so HUD can show even after collection
            if self.current_stats:
                self.stats_memory = self.current_stats.copy()

            # Draw path
            if self.current_path:
                path_surface = pygame.Surface((self.MAP_WIDTH, self.MAP_HEIGHT), pygame.SRCALPHA)
                for px, py in self.current_path[1:]:
                    rect = pygame.Rect(px*self.tmx_data.tilewidth, py*self.tmx_data.tileheight,
                                       self.tmx_data.tilewidth, self.tmx_data.tileheight)
                    pygame.draw.rect(path_surface, (0,0,255,128), rect)
                self.screen.blit(path_surface, (0,0))

            # Draw player
            self.player.draw(self.screen)

            # Draw HUD
            elapsed = (pygame.time.get_ticks() - self.message_timer) / 1000
            message = self.success_message if elapsed < 2 else ""
            self.hud.draw(self.screen, self.player, self.AUTO_MOVE, self.stats_memory, message)

            pygame.display.flip()

# import pygame
# import pytmx
# import os

# # ---------------- Helper ----------------
# def load_tmx(path):
#     return pytmx.util_pygame.load_pygame(path)

# # ---------------- Initialization ----------------
# pygame.init()
# print("Pygame initialized successfully")
# screen = pygame.display.set_mode((800, 600))

# # Script directory
# script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# # Load TMX map
# tmx_path = os.path.join(script_dir, "assets/maps/treasure.tmx")
# print(f"Loading TMX map from: {tmx_path}")
# tmx_data = load_tmx(tmx_path)

# MAP_WIDTH = tmx_data.width * tmx_data.tilewidth
# MAP_HEIGHT = tmx_data.height * tmx_data.tileheight

# # Screen
# screen = pygame.display.set_mode((MAP_WIDTH, MAP_HEIGHT))
# pygame.display.set_caption("TMX Map Test")

# # Clock
# clock = pygame.time.Clock()

# # ---------------- Main Loop ----------------
# running = True
# while running:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False

#     # Draw map
#     screen.fill((0, 0, 0))
#     for layer in tmx_data.visible_layers:
#         if isinstance(layer, pytmx.TiledTileLayer):
#             for x, y, gid in layer:
#                 tile = tmx_data.get_tile_image_by_gid(gid)
#                 if tile:
#                     screen.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))

#     pygame.display.flip()
#     clock.tick(60)

# pygame.quit()

# import pygame
# import pytmx
# import os

# # ---------------- Helper ----------------
# def load_tmx(path):
#     return pytmx.util_pygame.load_pygame(path)

# # ---------------- Initialization ----------------
# pygame.init()
# print("Pygame initialized successfully")
# screen = pygame.display.set_mode((800, 600))

# # Script directory
# script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# # Load TMX map
# tmx_path = os.path.join(script_dir, "assets/maps/treasure.tmx")
# print(f"Loading TMX map from: {tmx_path}")
# tmx_data = load_tmx(tmx_path)

# MAP_WIDTH = tmx_data.width * tmx_data.tilewidth
# MAP_HEIGHT = tmx_data.height * tmx_data.tileheight

# # Screen
# screen = pygame.display.set_mode((MAP_WIDTH, MAP_HEIGHT))
# pygame.display.set_caption("TMX Map Test")

# # Clock
# clock = pygame.time.Clock()

# # ---------------- Main Loop ----------------
# running = True
# while running:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False

#     # Draw map
#     screen.fill((0, 0, 0))
#     for layer in tmx_data.visible_layers:
#         if isinstance(layer, pytmx.TiledTileLayer):
#             for x, y, gid in layer:
#                 tile = tmx_data.get_tile_image_by_gid(gid)
#                 if tile:
#                     screen.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))

#     pygame.display.flip()
#     clock.tick(60)

# pygame.quit()

