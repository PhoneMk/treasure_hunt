import pygame

class Player:
    def __init__(self, image_path, tile_x, tile_y, tmx_data):
        self.spritesheet = pygame.image.load(image_path).convert_alpha()
        # Assuming frame size is 16x16, as in the original code.
        # This might need to be adjusted based on the actual sprite size.
        self.frame_width = 16
        self.frame_height = 16
        self.frames = self.load_frames(self.spritesheet, self.frame_width, self.frame_height)
        self.direction = 'down'
        self.current_frame = 0
        self.image = self.frames[self.direction][self.current_frame]
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.tmx_data = tmx_data
        self.rect = self.image.get_rect(
            topleft=(tile_x * tmx_data.tilewidth, tile_y * tmx_data.tileheight)
        )
        self.energy = 100
        self.is_moving = False
        self.is_dead = False
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100  # milliseconds per frame

    def load_frames(self, spritesheet, frame_width, frame_height):
        frames = {
            'down': [],
            'up': [],
            'left': [],
            'right': []
        }
        # As per user description, spritesheet has 4 rows for animation and 4 columns for direction.
        # Directions are assumed to be: down (straight), up (back), left, right.
        for col, direction in enumerate(['down', 'up', 'left', 'right']):
            for row in range(4): # 4 frames of animation per direction
                x = col * frame_width
                y = row * frame_height
                frame = spritesheet.subsurface(pygame.Rect(x, y, frame_width, frame_height))
                frames[direction].append(frame)
        return frames

    def update_animation(self):
        now = pygame.time.get_ticks()
        if self.is_moving:
            if now - self.last_update > self.animation_speed:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.frames[self.direction])
                self.image = self.frames[self.direction][self.current_frame]
        else:
            # If not moving, show the standing frame (first frame of animation)
            self.current_frame = 0
            self.image = self.frames[self.direction][self.current_frame]


    def move_to_tile(self, new_x, new_y, collision_layer, energy_layer):
        if 0 <= new_x < self.tmx_data.width and 0 <= new_y < self.tmx_data.height:
            gid = collision_layer.data[new_y][new_x]
            if gid == 0:
                if new_x > self.tile_x:
                    self.direction = 'right'
                elif new_x < self.tile_x:
                    self.direction = 'left'
                elif new_y > self.tile_y:
                    self.direction = 'down'
                elif new_y < self.tile_y:
                    self.direction = 'up'

                self.tile_x = new_x
                self.tile_y = new_y
                self.rect.x = new_x * self.tmx_data.tilewidth
                self.rect.y = new_y * self.tmx_data.tileheight
                self.is_moving = True

                # Energy cost
                cost = 1 # Default cost
                gid_energy = energy_layer.data[new_y][new_x]
                # If there's a tile on the energy layer, use its cost property
                if gid_energy != 0:
                    cost = energy_layer.properties.get("energy_cost", 1)

                self.energy -= cost
                self.energy = max(self.energy, 0)
                if self.energy == 0:
                    self.is_dead = True
                return True
        self.is_moving = False
        return False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
