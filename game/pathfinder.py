import pygame
from collections import deque
import heapq

class Pathfinder:
    def __init__(self, tmx_data, collision_layer, energy_layer=None):
        self.tmx_data = tmx_data
        self.collision_layer = collision_layer
        self.energy_layer = energy_layer
        self.stats = {
            'nodes_visited': 0,
            'path_length': 0,
            'search_time': 0,
            'total_energy_cost': 0
        }

    def can_move(self, x, y):
        if not (0 <= x < self.tmx_data.width and 0 <= y < self.tmx_data.height):
            return False
        try:
            gid = self.collision_layer.data[y][x]
            return gid == 0
        except IndexError:
            return False

    def get_tile_cost(self, x, y):
        """Get energy cost for moving to this tile"""
        if self.energy_layer is None:
            return 1
        
        try:
            gid = self.energy_layer.data[y][x]
            if gid == 0:
                return 1  # Normal terrain
            else:
                # Higher terrain costs more energy
                # You can adjust this based on your tile IDs
                return 2  # Or map specific GIDs to costs
        except IndexError:
            return 1

    def heuristic(self, pos, goal):
        """Manhattan distance heuristic (optimistic for grid movement)"""
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def reconstruct_path(self, came_from, current):
        """Helper to reconstruct path from came_from dict"""
        path = []
        while current is not None:
            path.append(current)
            current = came_from[current]
        return path[::-1]

    def calculate_path_cost(self, path):
        """Calculate total energy cost of a path"""
        if not path or len(path) < 2:
            return 0
        total = 0
        for i in range(1, len(path)):
            x, y = path[i]
            total += self.get_tile_cost(x, y)
        return total

    def bfs(self, start, goal):
        """BFS - doesn't consider energy costs (uniform cost)"""
        start_time = pygame.time.get_ticks()
        self.stats['nodes_visited'] = 0

        queue = deque([start])
        visited = {start: None}

        while queue:
            current = queue.popleft()
            self.stats['nodes_visited'] += 1

            if current == goal:
                path = self.reconstruct_path(visited, current)
                self.stats['path_length'] = len(path)
                self.stats['total_energy_cost'] = self.calculate_path_cost(path)
                self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
                return path

            x, y = current
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = x+dx, y+dy
                if self.can_move(nx, ny) and (nx, ny) not in visited:
                    visited[(nx, ny)] = current
                    queue.append((nx, ny))

        self.stats['path_length'] = 0
        self.stats['total_energy_cost'] = 0
        self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
        return None

    def a_star(self, start, goal):
        """A* algorithm: f(n) = g(n) + h(n) - considers actual energy costs"""
        start_time = pygame.time.get_ticks()
        self.stats['nodes_visited'] = 0

        counter = 0
        open_set = [(0, counter, start)]
        came_from = {start: None}
        g_score = {start: 0}  # Actual energy cost from start

        while open_set:
            _, _, current = heapq.heappop(open_set)
            self.stats['nodes_visited'] += 1

            if current == goal:
                path = self.reconstruct_path(came_from, current)
                self.stats['path_length'] = len(path)
                self.stats['total_energy_cost'] = g_score[current]
                self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
                return path

            x, y = current
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = x+dx, y+dy
                neighbor = (nx, ny)
                
                if not self.can_move(nx, ny):
                    continue

                # Energy cost to move to neighbor
                move_cost = self.get_tile_cost(nx, ny)
                tentative_g = g_score[current] + move_cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor, goal)
                    counter += 1
                    heapq.heappush(open_set, (f_score, counter, neighbor))

        self.stats['path_length'] = 0
        self.stats['total_energy_cost'] = 0
        self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
        return None

    def greedy_best_first(self, start, goal):
        """Greedy Best-First Search: only uses h(n) - ignores energy costs"""
        start_time = pygame.time.get_ticks()
        self.stats['nodes_visited'] = 0

        counter = 0
        open_set = [(self.heuristic(start, goal), counter, start)]
        came_from = {start: None}
        visited = set()

        while open_set:
            _, _, current = heapq.heappop(open_set)
            
            if current in visited:
                continue
            
            visited.add(current)
            self.stats['nodes_visited'] += 1

            if current == goal:
                path = self.reconstruct_path(came_from, current)
                self.stats['path_length'] = len(path)
                self.stats['total_energy_cost'] = self.calculate_path_cost(path)
                self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
                return path

            x, y = current
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = x+dx, y+dy
                neighbor = (nx, ny)
                
                if self.can_move(nx, ny) and neighbor not in visited:
                    if neighbor not in came_from:
                        came_from[neighbor] = current
                        h_score = self.heuristic(neighbor, goal)
                        counter += 1
                        heapq.heappush(open_set, (h_score, counter, neighbor))

        self.stats['path_length'] = 0
        self.stats['total_energy_cost'] = 0
        self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
        return None

    def dijkstra(self, start, goal):
        """Dijkstra's algorithm: considers actual energy costs"""
        start_time = pygame.time.get_ticks()
        self.stats['nodes_visited'] = 0

        counter = 0
        open_set = [(0, counter, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}

        while open_set:
            current_cost, _, current = heapq.heappop(open_set)
            self.stats['nodes_visited'] += 1

            if current == goal:
                path = self.reconstruct_path(came_from, current)
                self.stats['path_length'] = len(path)
                self.stats['total_energy_cost'] = cost_so_far[current]
                self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
                return path

            x, y = current
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = x+dx, y+dy
                neighbor = (nx, ny)
                
                if not self.can_move(nx, ny):
                    continue

                move_cost = self.get_tile_cost(nx, ny)
                new_cost = cost_so_far[current] + move_cost

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = current
                    counter += 1
                    heapq.heappush(open_set, (new_cost, counter, neighbor))

        self.stats['path_length'] = 0
        self.stats['total_energy_cost'] = 0
        self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
        return None

    def a_star_with_food(self, start, goal, food_positions, player_energy, max_energy=100, food_energy=5):
        """A* that considers picking up food along the way"""
        start_time = pygame.time.get_ticks()
        self.stats['nodes_visited'] = 0

        counter = 0
        # State: (position, collected_food_set)
        start_state = (start, frozenset())
        open_set = [(0, counter, start_state, player_energy)]
        came_from = {start_state: None}
        g_score = {start_state: 0}

        while open_set:
            _, _, state, energy = heapq.heappop(open_set)
            pos, collected = state
            self.stats['nodes_visited'] += 1

            if pos == goal:
                # Reconstruct path
                path = []
                current_state = state
                while current_state is not None:
                    path.append(current_state[0])
                    current_state = came_from[current_state]
                path = path[::-1]
                self.stats['path_length'] = len(path)
                self.stats['total_energy_cost'] = g_score[state]
                self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
                return path

            x, y = pos
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = x+dx, y+dy
                neighbor_pos = (nx, ny)
                
                if not self.can_move(nx, ny):
                    continue

                move_cost = self.get_tile_cost(nx, ny)
                new_energy = energy - move_cost
                
                # Check if we pick up food at this position
                new_collected = collected
                if neighbor_pos in food_positions and neighbor_pos not in collected:
                    new_collected = collected | {neighbor_pos}
                    new_energy = min(max_energy, new_energy + food_energy)
                
                # Skip if out of energy
                if new_energy <= 0:
                    continue

                neighbor_state = (neighbor_pos, new_collected)
                tentative_g = g_score[state] + move_cost

                if neighbor_state not in g_score or tentative_g < g_score[neighbor_state]:
                    came_from[neighbor_state] = state
                    g_score[neighbor_state] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor_pos, goal)
                    counter += 1
                    heapq.heappush(open_set, (f_score, counter, neighbor_state, new_energy))

        self.stats['path_length'] = 0
        self.stats['total_energy_cost'] = 0
        self.stats['search_time'] = (pygame.time.get_ticks() - start_time) / 1000
        return None