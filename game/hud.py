import pygame
import os

class HUD:
    def __init__(self, font, sidebar_width, screen_height):
        self.font = font
        self.sidebar_width = sidebar_width
        self.screen_height = screen_height

        # --- Thematic Colors ---
        self.TEXT_COLOR = (80, 40, 0)  # Dark brown for text
        self.VALUE_COLOR = (255, 204, 0)
        self.SUCCESS_COLOR = (50, 255, 50)
        self.AI_ON_COLOR = (0, 180, 0)
        self.AI_OFF_COLOR = (200, 0, 0)

        # --- 9-Patch Panel Assets ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        panel_path = os.path.join(script_dir, "..", "assets", "ui", "nine_path_panel.png")
        self.panel_image = pygame.image.load(panel_path).convert_alpha()
        self.border = 6 # The width of the border in the 9-patch image

        # Pre-slice the 9-patch image
        w, h = self.panel_image.get_size()
        b = self.border
        self.panel_slices = {
            'top_left': self.panel_image.subsurface(0, 0, b, b),
            'top': self.panel_image.subsurface(b, 0, w - 2 * b, b),
            'top_right': self.panel_image.subsurface(w - b, 0, b, b),
            'left': self.panel_image.subsurface(0, b, b, h - 2 * b),
            'center': self.panel_image.subsurface(b, b, w - 2 * b, h - 2 * b),
            'right': self.panel_image.subsurface(w - b, b, b, h - 2 * b),
            'bottom_left': self.panel_image.subsurface(0, h - b, b, b),
            'bottom': self.panel_image.subsurface(b, h - b, w - 2 * b, b),
            'bottom_right': self.panel_image.subsurface(w - b, h - b, b, b),
        }

    def _draw_nine_patch(self, surface, rect):
        b = self.border
        # Corners
        surface.blit(self.panel_slices['top_left'], (rect.left, rect.top))
        surface.blit(self.panel_slices['top_right'], (rect.right - b, rect.top))
        surface.blit(self.panel_slices['bottom_left'], (rect.left, rect.bottom - b))
        surface.blit(self.panel_slices['bottom_right'], (rect.right - b, rect.bottom - b))

        # Edges
        top_edge = pygame.transform.scale(self.panel_slices['top'], (rect.width - 2 * b, b))
        surface.blit(top_edge, (rect.left + b, rect.top))
        bottom_edge = pygame.transform.scale(self.panel_slices['bottom'], (rect.width - 2 * b, b))
        surface.blit(bottom_edge, (rect.left + b, rect.bottom - b))
        left_edge = pygame.transform.scale(self.panel_slices['left'], (b, rect.height - 2 * b))
        surface.blit(left_edge, (rect.left, rect.top + b))
        right_edge = pygame.transform.scale(self.panel_slices['right'], (b, rect.height - 2 * b))
        surface.blit(right_edge, (rect.right - b, rect.top + b))

        # Center
        center = pygame.transform.scale(self.panel_slices['center'], (rect.width - 2 * b, rect.height - 2 * b))
        surface.blit(center, (rect.left + b, rect.top + b))

    def draw(self, surface, player, ai_status, stats, food_collected, message=""):
        sidebar_x = surface.get_width() - self.sidebar_width

        # Background
        bg_rect = pygame.Rect(sidebar_x, 0, self.sidebar_width, self.screen_height)
        self._draw_nine_patch(surface, bg_rect)

        y_offset = 30
        x_pos = sidebar_x + 35  # Increased padding

        # --- Player Stats ---
        energy_label = self.font.render("Energy:", True, self.TEXT_COLOR)
        energy_value = self.font.render(f"{int(player.energy)}", True, self.TEXT_COLOR) # Changed color
        value_rect = energy_value.get_rect(topright=(sidebar_x + self.sidebar_width - 35, y_offset)) # Increased padding
        surface.blit(energy_label, (x_pos, y_offset))
        surface.blit(energy_value, value_rect)
        y_offset += 40

        food_label = self.font.render("Food:", True, self.TEXT_COLOR)
        food_value = self.font.render(f"{food_collected}", True, self.TEXT_COLOR)
        value_rect = food_value.get_rect(topright=(sidebar_x + self.sidebar_width - 35, y_offset))
        surface.blit(food_label, (x_pos, y_offset))
        surface.blit(food_value, value_rect)
        y_offset += 40

        # --- AI Status ---
        ai_label = self.font.render("AI:", True, self.TEXT_COLOR)
        ai_status_text, ai_status_color = ("ON", self.AI_ON_COLOR) if ai_status else ("OFF", self.AI_OFF_COLOR)
        ai_value = self.font.render(ai_status_text, True, ai_status_color)
        value_rect = ai_value.get_rect(topright=(sidebar_x + self.sidebar_width - 35, y_offset)) # Increased padding
        surface.blit(ai_label, (x_pos, y_offset))
        surface.blit(ai_value, value_rect)
        y_offset += 60

        # --- Pathfinding Stats ---
        stats_label = self.font.render("Pathfinder:", True, self.TEXT_COLOR)
        surface.blit(stats_label, (x_pos, y_offset))
        y_offset += 35

        stat_lines = [
            ("Visited", f"{stats.get('nodes_visited', 0)}"),
            ("Length", f"{stats.get('path_length', 0)}"),
            ("Time", f"{stats.get('search_time', 0):.3f}s")
        ]
        for label, value in stat_lines:
            label_text = self.font.render(label, True, self.TEXT_COLOR)
            value_text = self.font.render(value, True, self.TEXT_COLOR) # Changed color
            value_rect = value_text.get_rect(topright=(sidebar_x + self.sidebar_width - 35, y_offset)) # Increased padding
            surface.blit(label_text, (x_pos + 5, y_offset))
            surface.blit(value_text, value_rect)
            y_offset += 30

        # --- Message Log ---
        if message:
            msg_text = self.font.render(message, True, self.SUCCESS_COLOR)
            surface.blit(msg_text, (x_pos, self.screen_height - 40))