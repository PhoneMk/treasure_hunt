import pygame

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
