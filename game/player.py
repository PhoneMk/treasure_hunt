import pygame

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
                cost = 1 # Default cost
                gid_energy = energy_layer.data[new_y][new_x]
                # If there's a tile on the energy layer, use its cost property
                if gid_energy != 0:
                    cost = energy_layer.properties.get("energy_cost", 1)

                self.energy -= cost
                self.energy = max(self.energy, 0)
                return True
        return False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
