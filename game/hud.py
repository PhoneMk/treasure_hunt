import pygame
import os

class HUD:
    def __init__(self, font, sidebar_width, screen_height, screen_width=800):
        self.font = font
        self.sidebar_width = sidebar_width + 25
        self.screen_height = screen_height + 200
        self.screen_width = screen_width

        # --- Thematic Colors ---
        self.TEXT_COLOR = (80, 40, 0)      # Dark brown for labels
        self.VALUE_COLOR = (60, 30, 0)       # A slightly lighter brown for values
        self.SUCCESS_COLOR = (50, 255, 50)
        self.AI_ON_COLOR = (0, 180, 0)
        self.AI_OFF_COLOR = (200, 0, 0)
        self.DIVIDER_COLOR = (100, 50, 0)  # Color for separator lines

        # --- Layout Constants ---
        self.PADDING = 25                  # Padding from the panel's edges
        self.LINE_SPACING = 35             # Vertical space between lines in a section
        self.SECTION_SPACING = 25          # Extra space between sections

        # --- 9-Patch Panel Assets ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        panel_path = os.path.join(script_dir, "..", "assets", "ui", "nine_path_panel.png")
        try:
            self.panel_image = pygame.image.load(panel_path).convert_alpha()
            self.border = 6 # The width of the border in the 9-patch image
            self._slice_panel()
            self.panel_loaded = True
        except pygame.error:
            self.panel_loaded = False
            print(f"Warning: Could not load panel image at {panel_path}")


    def _slice_panel(self):
        """Pre-slices the 9-patch image for efficient rendering."""
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
        """Draws the 9-patch panel to fit the given rect."""
        if not self.panel_loaded: return # Don't draw if the image failed to load

        b = self.border
        # Corners
        surface.blit(self.panel_slices['top_left'], (rect.left, rect.top))
        surface.blit(self.panel_slices['top_right'], (rect.right - b, rect.top))
        surface.blit(self.panel_slices['bottom_left'], (rect.left, rect.bottom - b))
        surface.blit(self.panel_slices['bottom_right'], (rect.right - b, rect.bottom - b))

        # Edges (scaled)
        surface.blit(pygame.transform.scale(self.panel_slices['top'], (rect.width - 2 * b, b)), (rect.left + b, rect.top))
        surface.blit(pygame.transform.scale(self.panel_slices['bottom'], (rect.width - 2 * b, b)), (rect.left + b, rect.bottom - b))
        surface.blit(pygame.transform.scale(self.panel_slices['left'], (b, rect.height - 2 * b)), (rect.left, rect.top + b))
        surface.blit(pygame.transform.scale(self.panel_slices['right'], (b, rect.height - 2 * b)), (rect.right - b, rect.top + b))

        # Center (scaled)
        surface.blit(pygame.transform.scale(self.panel_slices['center'], (rect.width - 2 * b, rect.height - 2 * b)), (rect.left + b, rect.top + b))

    def _draw_stat_line(self, surface, y_offset, label, value,label_color=None, value_color=None):
        """Helper to draw a single line of a label and its value, perfectly aligned."""
        if value_color is None:
            value_color = self.VALUE_COLOR
        if label_color is None:
            label_color = self.TEXT_COLOR

        sidebar_x = surface.get_width() - self.sidebar_width
        left_pos = sidebar_x + self.PADDING
        right_pos = sidebar_x + self.sidebar_width - self.PADDING

        label_surf = self.font.render(label, True, label_color)
        value_surf = self.font.render(str(value), True, value_color)
        
        surface.blit(label_surf, (left_pos, y_offset))
        surface.blit(value_surf, value_surf.get_rect(topright=(right_pos, y_offset)))
        

    def _draw_divider(self, surface, y_offset):
        """Draws a horizontal line to separate sections."""
        sidebar_x = surface.get_width() - self.sidebar_width
        start_pos = (sidebar_x + self.PADDING, y_offset)
        end_pos = (sidebar_x + self.sidebar_width - self.PADDING, y_offset)
        pygame.draw.line(surface, self.DIVIDER_COLOR, start_pos, end_pos, 2)


    def draw(self, surface, player, ai_status, stats, food_collected, message="", algorithm=""):
        sidebar_x = surface.get_width() - self.sidebar_width
        
        # 1. Draw Background Panel
        bg_rect = pygame.Rect(sidebar_x, 0, self.sidebar_width, self.screen_height)
        bottom_height = 250
        bottom_rect = pygame.Rect(0, self.screen_height - 200, surface.get_width(), bottom_height)
        self._draw_nine_patch(surface, bottom_rect)
        self._draw_nine_patch(surface, bg_rect)
        y_offset = self.PADDING

        # 2. Player Stats Section
        self._draw_stat_line(surface, y_offset, "Energy:", f"{int(player.energy)}")
        y_offset += self.LINE_SPACING
        self._draw_stat_line(surface, y_offset, "Food:", f"{food_collected}")
        y_offset += self.LINE_SPACING

        # 3. AI Status Section
        y_offset += self.SECTION_SPACING
        self._draw_divider(surface, y_offset)
        y_offset += self.SECTION_SPACING

        ai_text, ai_color = ("ON", self.AI_ON_COLOR) if ai_status else ("OFF", self.AI_OFF_COLOR)
        self._draw_stat_line(surface, y_offset, "AI:", ai_text, ai_color)
        y_offset += self.LINE_SPACING

        self._draw_stat_line(surface, y_offset, "  Algorithm:", 0)
        y_offset += self.LINE_SPACING

        formatted_algo = algorithm.replace('_', ' ').title()
        self._draw_stat_line(surface, y_offset, formatted_algo, "", label_color=(255, 0, 0))
        y_offset += self.LINE_SPACING

        # 4. Pathfinder Stats Section
        y_offset += self.SECTION_SPACING
        self._draw_divider(surface, y_offset)
        y_offset += self.SECTION_SPACING
    
        
        pathfinder_label = self.font.render("Pathfinder", True, self.TEXT_COLOR)
        surface.blit(pathfinder_label, (sidebar_x + self.PADDING, y_offset))
        y_offset += self.LINE_SPACING

        # Format algorithm name to be more readable


        self._draw_stat_line(surface, y_offset, "  Visited:", f"{stats.get('nodes_visited', 0)}")
        y_offset += self.LINE_SPACING
        self._draw_stat_line(surface, y_offset, "  Length:", f"{stats.get('path_length', 0)}")
        y_offset += self.LINE_SPACING
        self._draw_stat_line(surface, y_offset, "  Time:", f"{stats.get('search_time', 0):.3f}s")
        y_offset += self.LINE_SPACING

        # 5. Message Log
        if message:
            msg_surf = self.font.render(message, True, self.SUCCESS_COLOR)
            msg_rect = msg_surf.get_rect(bottomleft=(sidebar_x + self.PADDING, self.screen_height - self.PADDING))
            surface.blit(msg_surf, msg_rect)