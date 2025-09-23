import pygame
import traceback
import sys
from game.game import Game
from game.menu import Menu

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Treasure Hunter")
    menu = Menu(screen)

    while True:
        menu.draw()
        action = menu.handle_events()

        if action == "START":
            try:
                game = Game()
                game.run()
            except Exception as e:
                print(f"Error: {e}")
                print(traceback.format_exc())
                input("Press Enter to exit...")
            break
        elif action == "QUIT":
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()