import pygame
import sys
import pytmx
import os
from collections import deque

# ---------------- Constants ----------------
SCREEN_WIDTH = 1000  # Extra width for stats sidebar
SCREEN_HEIGHT = 600
MAP_OFFSET_X = 0
MAP_OFFSET_Y = 0
SIDEBAR_WIDTH = 200

# ---------------- Helper Functions ----------------
def load_tmx(path):
    return pytmx.util_pygame.load_pygame(path)

# ---------------- Player Class ----------------
class Player:
    def __init__(self, image_path, tile_x, tile_y, tmx_data):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.tmx_data = tmx_data
        self.rect = self.image.get_rect(
            topleft=(tile_x * tmx_data.tilewidth, tile_y * tmx_data.tileheight)
        )
        self.energy = 100

    def move_to_tile(self, new_x, new_y, collision_layer, energy_layer):
        if 0 <= new_x < self.tmx_data.width and 0 <= new_y < self.tmx_data.height:
            gid = collision_layer.data[new_y][new_x]
            if gid == 0:
                self.tile_x = new_x
                self.tile_y = new_y
                self.rect.x = new_x * self.tmx_data.tilewidth
                self.rect.y = new_y * self.tmx_data.tileheight

                # Energy cost
                gid_energy = energy_layer.data[new_y][new_x]
                cost = energy_layer.properties.get("energy_cost", 1) if gid_energy else 1
                self.energy -= cost
                self.energy = max(self.energy, 0)
                return True
        return False

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# ---------------- Treasure Class ----------------
class Treasure:
    def __init__(self, obj, image, tmx_data):
        self.obj = obj
        self.image = image
        self.tmx_data = tmx_data
        self.collected = False
        self.rect = pygame.Rect(
            int(obj.x // tmx_data.tilewidth) * tmx_data.tilewidth,
            int(obj.y // tmx_data.tileheight) * tmx_data.tileheight,
            tmx_data.tilewidth,
            tmx_data.tileheight
        )

    def draw(self, surface):
        if not self.collected:
            surface.blit(self.image, self.rect)

# ---------------- Pathfinder Class ----------------
class Pathfinder:
    def __init__(self, tmx_data, collision_layer):
        self.tmx_data = tmx_data
        self.collision_layer = collision_layer
        self.stats = {
            'nodes_visited': 0,
            'path_length': 0,
            'search_time': 0
        }

    def can_move(self, x, y):
        if not (0 <= x < self.tmx_data.width and 0 <= y < self.tmx_data.height):
            return False
        try:
            gid = self.collision_layer.data[y][x]
            return gid == 0
        except:
            return False

    def bfs(self, start, goal):
        import time
        start_time = pygame.time.get_ticks()
        self.stats['nodes_visited'] = 0

        queue = deque([start])
        visited = {start: None}

        while queue:
            current = queue.popleft()
            self.stats['nodes_visited'] += 1

            if current == goal:
                path = []
                while current is not None:
                    path.append(current)
                    current = visited[current]
                path = path[::-1]
                self.stats['path_length'] = len(path)
                self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
                return path

            x, y = current
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = x+dx, y+dy
                if self.can_move(nx, ny) and (nx, ny) not in visited:
                    visited[(nx, ny)] = current
                    queue.append((nx, ny))

        self.stats['path_length'] = 0
        self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
        return None

# ---------------- HUD Class ----------------
class HUD:
    def __init__(self, font, sidebar_width, screen_height):
        self.font = font
        self.sidebar_width = sidebar_width
        self.screen_height = screen_height

    def draw(self, surface, player, ai_status, stats, message=""):
        # Background
        bg = pygame.Surface((self.sidebar_width, self.screen_height))
        bg.fill((30, 30, 30))
        surface.blit(bg, (MAP_WIDTH, 0))

        # Energy
        energy_text = self.font.render(f"Energy: {int(player.energy)}", True, (255, 255, 0))
        surface.blit(energy_text, (MAP_WIDTH + 10, 10))

        # AI Status
        ai_text = self.font.render(f"AI: {'ON' if ai_status else 'OFF'}", True, (255, 255, 0))
        surface.blit(ai_text, (MAP_WIDTH + 10, 40))

        # Stats
        stat_lines = [
            f"Nodes Visited: {stats.get('nodes_visited',0)}",
            f"Path Length: {stats.get('path_length',0)}",
            f"Search Time: {stats.get('search_time',0):.3f}s"
        ]
        for i, line in enumerate(stat_lines):
            text = self.font.render(line, True, (255, 255, 255))
            surface.blit(text, (MAP_WIDTH + 10, 80 + i*30))

        # Message
        if message:
            msg_text = self.font.render(message, True, (0, 255, 0))
            surface.blit(msg_text, (MAP_WIDTH + 10, 200))

# ---------------- Main Game Class ----------------
# ---------------- Main Game Class ----------------
class Game:
    def __init__(self):
        pygame.init()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("TMX Game Example")
        self.clock = pygame.time.Clock()

        # Load map
        tmx_path = os.path.join(self.script_dir, "assets/maps/treasure.tmx")
        self.tmx_data = load_tmx(tmx_path)
        global MAP_WIDTH, MAP_HEIGHT
        MAP_WIDTH = self.tmx_data.width * self.tmx_data.tilewidth
        MAP_HEIGHT = self.tmx_data.height * self.tmx_data.tileheight
        self.screen = pygame.display.set_mode((MAP_WIDTH + SIDEBAR_WIDTH, MAP_HEIGHT))

        # Layers
        self.collision_layer = self.tmx_data.get_layer_by_name("Tile Layer 2")
        self.energy_layer = self.tmx_data.get_layer_by_name("Tile Layer 3")
        self.object_layer = self.tmx_data.get_layer_by_name("Object Layer 1")

        # Player
        player_img = os.path.join(self.script_dir, "assets/sprites/tile_0109.png")
        self.player = Player(player_img, 0, 0, self.tmx_data)

        # Treasures
        treasure_img = pygame.image.load(os.path.join(self.script_dir, "assets/sprites/tile_0089.png")).convert_alpha()
        self.treasures = [Treasure(obj, treasure_img, self.tmx_data) for obj in self.object_layer if obj.properties.get("item_type")=="treasure"]

        # Pathfinder
        self.pathfinder = Pathfinder(self.tmx_data, self.collision_layer)
        self.current_path = None
        self.current_stats = None
        self.last_stats = {}  # <-- Keep last BFS stats

        # HUD
        self.font = pygame.font.SysFont(None, 24)
        self.hud = HUD(self.font, SIDEBAR_WIDTH, SCREEN_HEIGHT)

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

        # Save stats even if a path is found
        if nearest_stats:
            self.last_stats = nearest_stats

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

            # Draw path
            if self.current_path:
                path_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
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

            # Show current stats if moving, else show last stats
            stats_to_show = self.current_stats if self.current_stats else self.last_stats

            self.hud.draw(self.screen, self.player, self.AUTO_MOVE, stats_to_show or {}, message)

            pygame.display.flip()

# ---------------- Run Game ----------------
if __name__ == "__main__":
    Game().run()
