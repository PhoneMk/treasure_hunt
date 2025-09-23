import pygame
import os


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()

        # --- UI Elements ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(script_dir, "..", "assets", "fonts", "NormalFont.ttf")
        self.title_font = pygame.font.Font(font_path, 60)
        self.button_font = pygame.font.Font(font_path, 40)

        # Colors
        self.BG_COLOR = (10, 10, 25)
        self.TITLE_COLOR = (255, 204, 0)
        self.BUTTON_COLOR = (80, 80, 80)
        self.BUTTON_HOVER_COLOR = (110, 110, 110)
        self.TEXT_COLOR = (255, 255, 255)

        # Button data: (text, action, y_offset)
        button_definitions = [
            ("Start", "START", -40),
            ("Quit", "QUIT", 40)
        ]

        self.buttons = []
        for text, action, y_offset in button_definitions:
            rect = pygame.Rect(0, 0, 200, 60)
            rect.center = (self.screen_rect.centerx, self.screen_rect.centery + y_offset)
            self.buttons.append({"rect": rect, "text": text, "action": action})

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in self.buttons:
                    if button["rect"].collidepoint(event.pos):
                        return button["action"]
        return None

    def draw(self):
        self.screen.fill(self.BG_COLOR)

        # Title
        title_text = self.title_font.render("Treasure Hunter", True, self.TITLE_COLOR)
        title_rect = title_text.get_rect(center=(self.screen_rect.centerx, self.screen_rect.centery - 150))
        self.screen.blit(title_text, title_rect)

        # Draw all buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            self._draw_button(button, mouse_pos)

        pygame.display.flip()

    def _draw_button(self, button, mouse_pos):
        """Helper method to draw a single button."""
        rect = button["rect"]
        color = self.BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else self.BUTTON_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=10)

        text_surf = self.button_font.render(button["text"], True, self.TEXT_COLOR)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)