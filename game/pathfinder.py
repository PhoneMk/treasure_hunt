import pygame
from collections import deque

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
