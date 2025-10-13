import heapq
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple, Set, Optional
import time
import copy

@dataclass
class Position:
    """Represents a 2D position"""
    x: int
    y: int
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def manhattan_distance(self, other: 'Position') -> int:
        """Calculate Manhattan distance to another position"""
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def euclidean_distance(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position"""
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

@dataclass
class GameState:
    """Represents the complete state of the game"""
    position: Position
    energy: int
    visited_foods: Set[Position]
    
    def __hash__(self):
        return hash((self.position.x, self.position.y, self.energy, frozenset(self.visited_foods)))
    
    def __eq__(self, other):
        return (self.position == other.position and 
                self.energy == other.energy and 
                self.visited_foods == other.visited_foods)

class TreasureHuntGame:
    """Main game class containing map and game logic"""
    
    TERRAIN_COSTS = {
        '.': 1,
        '~': 2,
        '^': 2,
        'S': 1,
        'T': 1,
        'F': 1,
        'X': float('inf')
    }
    
    def __init__(self, game_map: List[str], starting_energy: int = 12, max_energy: int = 20, food_energy: int = 5):
        self.game_map = [list(row) for row in game_map]
        self.height = len(self.game_map)
        self.width = len(self.game_map[0]) if self.height > 0 else 0
        self.starting_energy = starting_energy
        self.max_energy = max_energy
        self.food_energy = food_energy
        
        self.start_pos = self._find_position('S')
        self.treasure_pos = self._find_position('T')
        self.food_positions = self._find_all_positions('F')
        
    def _find_position(self, symbol: str) -> Position:
        for y in range(self.height):
            for x in range(self.width):
                if self.game_map[y][x] == symbol:
                    return Position(x, y)
        raise ValueError(f"Symbol '{symbol}' not found on map")
    
    def _find_all_positions(self, symbol: str) -> List[Position]:
        positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.game_map[y][x] == symbol:
                    positions.append(Position(x, y))
        return positions
    
    def get_initial_state(self) -> GameState:
        return GameState(
            position=self.start_pos,
            energy=self.starting_energy,
            visited_foods=set()
        )
    
    def is_valid_position(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height
    
    def get_terrain_at(self, pos: Position) -> str:
        if not self.is_valid_position(pos):
            return 'X'
        return self.game_map[pos.y][pos.x]
    
    def get_possible_moves(self, state: GameState) -> List[GameState]:
        moves = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for dx, dy in directions:
            new_pos = Position(state.position.x + dx, state.position.y + dy)
            
            if not self.is_valid_position(new_pos):
                continue
                
            terrain = self.get_terrain_at(new_pos)
            if terrain == 'X':
                continue
            
            energy_cost = self.TERRAIN_COSTS.get(terrain, 1)
            new_energy = state.energy - energy_cost
            
            if new_energy <= 0:
                continue
            
            new_visited_foods = state.visited_foods.copy()
            if new_pos in self.food_positions and new_pos not in state.visited_foods:
                new_energy = min(new_energy + self.food_energy, self.max_energy)
                new_visited_foods.add(new_pos)
            
            new_state = GameState(
                position=new_pos,
                energy=new_energy,
                visited_foods=new_visited_foods
            )
            moves.append(new_state)
        
        return moves
    
    def is_goal_state(self, state: GameState) -> bool:
        return state.position == self.treasure_pos
    
    def is_valid_state(self, state: GameState) -> bool:
        return state.energy > 0
    
    def print_map(self, current_state: Optional[GameState] = None):
        print("Game Map:")
        print("Legend: S=Start, T=Treasure, F=Food, X=Obstacle, .=Normal, ~=Swamp, ^=Hills")
        print(f"Terrain Costs: Normal=1, Swamp=2, Hills=2")
        print()
        
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                if current_state and current_state.position.x == x and current_state.position.y == y:
                    row += "P "
                else:
                    row += self.game_map[y][x] + " "
            print(row)
        print()

@dataclass
class SearchResult:
    """Results of a search algorithm execution"""
    success: bool
    path: List[GameState]
    nodes_explored: int
    max_memory_usage: int
    execution_time: float
    final_energy: int = 0
    algorithm_name: str = ""

class SearchAlgorithms:
    """Implementation of blind and informed search algorithms"""
    
    def __init__(self, game: TreasureHuntGame):
        self.game = game
    
    # ==================== BLIND SEARCH ALGORITHMS ====================
    
    def bfs(self) -> SearchResult:
        """Breadth-First Search implementation"""
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time, 
                              initial_state.energy, "BFS")
        
        queue = deque([(initial_state, [initial_state])])
        visited = {initial_state}
        nodes_explored = 0
        max_memory = 1
        
        while queue:
            max_memory = max(max_memory, len(queue) + len(visited))
            current_state, path = queue.popleft()
            nodes_explored += 1
            
            for next_state in self.game.get_possible_moves(current_state):
                if next_state in visited:
                    continue
                    
                new_path = path + [next_state]
                
                if self.game.is_goal_state(next_state):
                    return SearchResult(True, new_path, nodes_explored, max_memory, 
                                      time.time() - start_time, next_state.energy, "BFS")
                
                queue.append((next_state, new_path))
                visited.add(next_state)
        
        return SearchResult(False, [], nodes_explored, max_memory, 
                          time.time() - start_time, 0, "BFS")
    
    def dfs(self, max_depth: int = 100) -> SearchResult:
        """Depth-First Search implementation with depth limit"""
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time, 
                              initial_state.energy, "DFS")
        
        stack = [(initial_state, [initial_state], 0)]
        visited = set()
        nodes_explored = 0
        max_memory = 1
        
        while stack:
            max_memory = max(max_memory, len(stack) + len(visited))
            current_state, path, depth = stack.pop()
            
            if current_state in visited or depth >= max_depth:
                continue
                
            visited.add(current_state)
            nodes_explored += 1
            
            for next_state in self.game.get_possible_moves(current_state):
                if next_state in visited:
                    continue
                    
                new_path = path + [next_state]
                
                if self.game.is_goal_state(next_state):
                    return SearchResult(True, new_path, nodes_explored, max_memory, 
                                      time.time() - start_time, next_state.energy, "DFS")
                
                stack.append((next_state, new_path, depth + 1))
        
        return SearchResult(False, [], nodes_explored, max_memory, 
                          time.time() - start_time, 0, "DFS")
    
    def ids(self, max_depth: int = 50) -> SearchResult:
        """Iterative Deepening Search implementation"""
        start_time = time.time()
        total_nodes_explored = 0
        max_memory = 0
        
        for depth_limit in range(max_depth):
            result = self._depth_limited_search(depth_limit)
            total_nodes_explored += result.nodes_explored
            max_memory = max(max_memory, result.max_memory_usage)
            
            if result.success:
                return SearchResult(True, result.path, total_nodes_explored, max_memory, 
                                  time.time() - start_time, result.final_energy, "IDS")
            
            if result.nodes_explored == 0:
                break
        
        return SearchResult(False, [], total_nodes_explored, max_memory, 
                          time.time() - start_time, 0, "IDS")
    
    def _depth_limited_search(self, depth_limit: int) -> SearchResult:
        """Helper method for IDS"""
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, 0, initial_state.energy, "DLS")
        
        stack = [(initial_state, [initial_state], 0)]
        visited_at_depth = set()
        nodes_explored = 0
        max_memory = 1
        
        while stack:
            max_memory = max(max_memory, len(stack))
            current_state, path, depth = stack.pop()
            
            if depth > depth_limit:
                continue
                
            state_depth_key = (current_state, depth)
            if state_depth_key in visited_at_depth:
                continue
                
            visited_at_depth.add(state_depth_key)
            nodes_explored += 1
            
            if depth < depth_limit:
                for next_state in self.game.get_possible_moves(current_state):
                    new_path = path + [next_state]
                    
                    if self.game.is_goal_state(next_state):
                        return SearchResult(True, new_path, nodes_explored, max_memory, 
                                          0, next_state.energy, "DLS")
                    
                    stack.append((next_state, new_path, depth + 1))
        
        return SearchResult(False, [], nodes_explored, max_memory, 0, 0, "DLS")
    
    # ==================== INFORMED SEARCH ALGORITHMS ====================
    
    def a_star(self, heuristic: str = "manhattan") -> SearchResult:
        """A* Search: f(n) = g(n) + h(n)"""
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time,
                              initial_state.energy, "A*")
        
        # Priority queue: (f_score, counter, g_score, state, path)
        counter = 0
        h = self._heuristic(initial_state.position, heuristic)
        open_set = [(h, counter, 0, initial_state, [initial_state])]
        
        # Track best g_score for each state
        g_scores = {initial_state: 0}
        nodes_explored = 0
        max_memory = 1
        
        while open_set:
            max_memory = max(max_memory, len(open_set) + len(g_scores))
            f_score, _, g_score, current_state, path = heapq.heappop(open_set)
            nodes_explored += 1
            
            if self.game.is_goal_state(current_state):
                return SearchResult(True, path, nodes_explored, max_memory,
                                  time.time() - start_time, current_state.energy, "A*")
            
            for next_state in self.game.get_possible_moves(current_state):
                # g(n) = actual cost from start (energy spent)
                tentative_g = g_score + (current_state.energy - next_state.energy)
                
                if next_state not in g_scores or tentative_g < g_scores[next_state]:
                    g_scores[next_state] = tentative_g
                    h = self._heuristic(next_state.position, heuristic)
                    f = tentative_g + h
                    counter += 1
                    new_path = path + [next_state]
                    heapq.heappush(open_set, (f, counter, tentative_g, next_state, new_path))
        
        return SearchResult(False, [], nodes_explored, max_memory,
                          time.time() - start_time, 0, "A*")
    
    def greedy_best_first(self, heuristic: str = "manhattan") -> SearchResult:
        """Greedy Best-First Search: uses only h(n)"""
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time,
                              initial_state.energy, "Greedy")
        
        # Priority queue: (h_score, counter, state, path)
        counter = 0
        h = self._heuristic(initial_state.position, heuristic)
        open_set = [(h, counter, initial_state, [initial_state])]
        visited = set()
        nodes_explored = 0
        max_memory = 1
        
        while open_set:
            max_memory = max(max_memory, len(open_set) + len(visited))
            h_score, _, current_state, path = heapq.heappop(open_set)
            
            if current_state in visited:
                continue
            
            visited.add(current_state)
            nodes_explored += 1
            
            if self.game.is_goal_state(current_state):
                return SearchResult(True, path, nodes_explored, max_memory,
                                  time.time() - start_time, current_state.energy, "Greedy")
            
            for next_state in self.game.get_possible_moves(current_state):
                if next_state not in visited:
                    h = self._heuristic(next_state.position, heuristic)
                    counter += 1
                    new_path = path + [next_state]
                    heapq.heappush(open_set, (h, counter, next_state, new_path))
        
        return SearchResult(False, [], nodes_explored, max_memory,
                          time.time() - start_time, 0, "Greedy")
    
    def dijkstra(self) -> SearchResult:
        """Dijkstra's Algorithm: uses only g(n)"""
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time,
                              initial_state.energy, "Dijkstra")
        
        # Priority queue: (cost, counter, state, path)
        counter = 0
        open_set = [(0, counter, initial_state, [initial_state])]
        cost_so_far = {initial_state: 0}
        nodes_explored = 0
        max_memory = 1
        
        while open_set:
            max_memory = max(max_memory, len(open_set) + len(cost_so_far))
            current_cost, _, current_state, path = heapq.heappop(open_set)
            nodes_explored += 1
            
            if self.game.is_goal_state(current_state):
                return SearchResult(True, path, nodes_explored, max_memory,
                                  time.time() - start_time, current_state.energy, "Dijkstra")
            
            for next_state in self.game.get_possible_moves(current_state):
                new_cost = current_cost + (current_state.energy - next_state.energy)
                
                if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_cost
                    counter += 1
                    new_path = path + [next_state]
                    heapq.heappush(open_set, (new_cost, counter, next_state, new_path))
        
        return SearchResult(False, [], nodes_explored, max_memory,
                          time.time() - start_time, 0, "Dijkstra")
    
    def weighted_a_star(self, weight: float = 1.5, heuristic: str = "manhattan") -> SearchResult:
        """Weighted A*: f(n) = g(n) + w*h(n) where w > 1"""
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time,
                              initial_state.energy, f"WA*({weight})")
        
        counter = 0
        h = self._heuristic(initial_state.position, heuristic)
        open_set = [(weight * h, counter, 0, initial_state, [initial_state])]
        g_scores = {initial_state: 0}
        nodes_explored = 0
        max_memory = 1
        
        while open_set:
            max_memory = max(max_memory, len(open_set) + len(g_scores))
            f_score, _, g_score, current_state, path = heapq.heappop(open_set)
            nodes_explored += 1
            
            if self.game.is_goal_state(current_state):
                return SearchResult(True, path, nodes_explored, max_memory,
                                  time.time() - start_time, current_state.energy, f"WA*({weight})")
            
            for next_state in self.game.get_possible_moves(current_state):
                tentative_g = g_score + (current_state.energy - next_state.energy)
                
                if next_state not in g_scores or tentative_g < g_scores[next_state]:
                    g_scores[next_state] = tentative_g
                    h = self._heuristic(next_state.position, heuristic)
                    f = tentative_g + weight * h
                    counter += 1
                    new_path = path + [next_state]
                    heapq.heappush(open_set, (f, counter, tentative_g, next_state, new_path))
        
        return SearchResult(False, [], nodes_explored, max_memory,
                          time.time() - start_time, 0, f"WA*({weight})")
    
    def _heuristic(self, pos: Position, heuristic_type: str = "manhattan") -> float:
        """Calculate heuristic distance to treasure"""
        if heuristic_type == "manhattan":
            return pos.manhattan_distance(self.game.treasure_pos)
        elif heuristic_type == "euclidean":
            return pos.euclidean_distance(self.game.treasure_pos)
        elif heuristic_type == "zero":
            return 0  # Makes A* behave like Dijkstra
        else:
            return pos.manhattan_distance(self.game.treasure_pos)

def print_search_results(results: List[SearchResult]):
    """Print comparison of search algorithm results"""
    print("=" * 100)
    print("SEARCH ALGORITHM COMPARISON RESULTS")
    print("=" * 100)
    
    print(f"{'Algorithm':<15} {'Success':<8} {'Path Length':<12} {'Nodes Explored':<15} "
          f"{'Max Memory':<12} {'Time (ms)':<10} {'Final Energy':<12}")
    print("-" * 100)
    
    for result in results:
        path_length = len(result.path) - 1 if result.success else "N/A"
        time_ms = f"{result.execution_time * 1000:.2f}"
        final_energy = result.final_energy if result.success else "N/A"
        
        print(f"{result.algorithm_name:<15} {result.success:<8} {path_length:<12} "
              f"{result.nodes_explored:<15} {result.max_memory_usage:<12} "
              f"{time_ms:<10} {final_energy:<12}")
    
    print("-" * 100)

def visualize_solution(game: TreasureHuntGame, result: SearchResult):
    """Visualize the solution path step by step"""
    if not result.success:
        print(f"{result.algorithm_name} failed to find a solution!")
        return
    
    print(f"\n{result.algorithm_name} Solution Path:")
    print("=" * 50)
    
    for i, state in enumerate(result.path):
        print(f"Step {i}: Position({state.position.x}, {state.position.y}), "
              f"Energy: {state.energy}, Foods eaten: {len(state.visited_foods)}")
        
        if i < len(result.path) - 1:
            current_pos = result.path[i].position
            next_pos = result.path[i + 1].position
            terrain = game.get_terrain_at(next_pos)
            energy_cost = game.TERRAIN_COSTS.get(terrain, 1)
            print(f"  → Moving to terrain '{terrain}' (cost: {energy_cost})")
    
    print(f"\nTotal steps: {len(result.path) - 1}")
    print(f"Final energy: {result.final_energy}")

# Test maps
test_maps = {
    "original": [
        "S.~F.X^^^",
        ".X~~.X^F^", 
        ".X.F~~.X.",
        "F..X~..^.",
        "~~X..F^^T"
    ],
    
    "maze_like": [
        "S.X.F.X..",
        ".XXXXX.X.",
        ".......X.",
        "XXXX.XXX.",
        "F..X...X.",
        ".X.XXX.X.",
        ".......X.",
        "XXXXX.X..",
        "F.....XFT"
    ],
    
    "energy_crisis": [
        "S~~~~~~~~",
        "~XXXXXXX~",
        "~X.....X~",
        "~X.XXX.X~",
        "~X.XFX.X~",
        "~X.XXX.X~",
        "~X.....X~",
        "~XXXXXXX~",
        "~~~~~~~~T"
    ],
    
    "food_desert": [
        "S........",
        ".........",
        ".........",
        "....F....",
        ".........",
        ".........",
        ".........",
        ".........",
        "........T"
    ],
    
    "swamp_challenge": [
        "S.......F",
        "~~~~~~~~~",
        "~~~~~~~~~", 
        "~~~~~~~~~",
        "F~~~F~~~F",
        "~~~~~~~~~",
        "~~~~~~~~~",
        "~~~~~~~~~",
        "F.......T"
    ],
    
    "hills_and_valleys": [
        "S.F^^^^^^",
        ".^^^^^^^^",
        "F^^^^^^^^",
        "^^^^^F^^^",
        "^^^^...^^",
        "^^^.....^",
        "^^F.....^",
        "^.......^",
        "F.......T"
    ],
    
    "narrow_corridors": [
        "SXXXXXXXXX",
        ".XXXXXXXX.",
        "F.XXXXXX.F",
        "X.XXXXX.XX",
        "XX.XXX.XXX",
        "XXX.X.XXXX",
        "XXXX.XXXXX",
        "XXXF.FFFXX",
        "XXXXXXX..T"
    ],
    
    "optimal_vs_safe": [
        "S.......F.",
        "~~~~~~~~~.",
        "~~~~~~~~~.",
        "~~~~~~~~~.",
        "~~~~~~~~~.",
        "..........",
        "F.........",
        "..........",
        ".........T"
    ],
    
    # Maps designed to make specific algorithms fail
    "dfs_trap": [
        "S.........",
        "XXXXXXXXX.",
        "........X.",
        ".XXXXXXXX.",
        "..........",
        "XXXXXXXXX.",
        "X.........",
        ".XXXXXXXX.",
        "F.......T."
    ],
    
    "bfs_memory_killer": [
        "S..................F",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "....................",
        "...................T"
    ],
    
    "energy_impossible": [
        "S~~~~~~~",
        "~XXXXXXX",
        "~X.....X", 
        "~X.XXX.X",
        "~X.X.X.X",
        "~X.XXX.X",
        "~X.....X",
        "~XXXXXXT"
    ],
    
    "deep_rabbit_hole": [
        "S.X.......",
        "..X.......",
        "..X.......",
        "..X.......",
        "..X.......",
        "..X.......",
        "..X.......",
        "..XXXXXXXX",
        "..........F",
        "XXXXXXXXX.",
        "........X.",
        "XXXXXXX.X.",
        "......X.X.",
        "XXXXX.X.X.",
        "....X.X.X.",
        "XXX.X.X.X.",
        "..X.X.X.X.",
        "X.X.X.X.X.",
        "..X.X.X.X.",
        ".........T"
    ],
        "swampy_path": [
        "S...X...F...X...T",
        "XXXX.X.XXX.X.XXXX",
        ".....X...X.....X.",
        "XXXX.X.XXX.X.XXXX",
        "F...X...F...X...T"
    ]
}

if __name__ == "__main__":
    print("Available maps:")
    for i, name in enumerate(test_maps.keys()):
        print(f"{i+1}. {name}")
    
    choice = input("Choose a map number (or 'all' for comparison): ").strip()
    
    if choice.lower() == 'all':
        # Run all algorithms on first map
        map_name = list(test_maps.keys())[0]
        game = TreasureHuntGame(test_maps[map_name])
        search_algorithms = SearchAlgorithms(game)
        
        print(f"\nRunning comprehensive algorithm comparison on '{map_name}' map")
        game.print_map(game.get_initial_state())
        
        results = []
        
        # Blind search
        print("\n=== BLIND SEARCH ALGORITHMS ===")
        print("Running BFS...", end=" ")
        results.append(search_algorithms.bfs())
        print("✓")
        
        print("Running DFS...", end=" ")
        results.append(search_algorithms.dfs(max_depth=100))
        print("✓")
        
        print("Running IDS...", end=" ")
        results.append(search_algorithms.ids(max_depth=50))
        print("✓")
        
        # Informed search
        print("\n=== INFORMED SEARCH ALGORITHMS ===")
        print("Running A* (Manhattan)...", end=" ")
        results.append(search_algorithms.a_star(heuristic="manhattan"))
        print("✓")
        
        print("Running Greedy Best-First...", end=" ")
        results.append(search_algorithms.greedy_best_first(heuristic="manhattan"))
        print("✓")
        
        print("Running Dijkstra...", end=" ")
        results.append(search_algorithms.dijkstra())
        print("✓")
        
        print("Running Weighted A* (1.5)...", end=" ")
        results.append(search_algorithms.weighted_a_star(weight=1.5))
        print("✓")
        
        print_search_results(results)
        
        # Show best solution
        successful_results = [r for r in results if r.success]
        if successful_results:
            best_result = min(successful_results, key=lambda r: len(r.path))
            print(f"\nBest solution: {best_result.algorithm_name} with {len(best_result.path)-1} steps")
            
            # Efficiency comparison
            print("\n=== EFFICIENCY METRICS ===")
            for result in results:
                if result.success:
                    efficiency = result.nodes_explored / len(result.path) if len(result.path) > 0 else 0
                    print(f"{result.algorithm_name}: {len(result.path)-1} steps, "
                          f"{result.nodes_explored} nodes explored, "
                          f"efficiency: {efficiency:.1f} nodes/step")
    
    elif choice.isdigit():
        choice_int = int(choice)
        if 1 <= choice_int <= len(test_maps):
            map_name = list(test_maps.keys())[choice_int-1]
            game = TreasureHuntGame(test_maps[map_name])
            search_algorithms = SearchAlgorithms(game)
            
            print(f"\nRunning on '{map_name}' map")
            game.print_map(game.get_initial_state())
            
            print("\nChoose algorithm:")
            print("1. BFS")
            print("2. DFS")
            print("3. IDS")
            print("4. A*")
            print("5. Greedy Best-First")
            print("6. Dijkstra")
            print("7. Weighted A*")
            print("8. Compare All")
            
            algo_choice = input("Enter choice: ").strip()
            
            if algo_choice == "1":
                result = search_algorithms.bfs()
            elif algo_choice == "2":
                result = search_algorithms.dfs()
            elif algo_choice == "3":
                result = search_algorithms.ids()
            elif algo_choice == "4":
                result = search_algorithms.a_star()
            elif algo_choice == "5":
                result = search_algorithms.greedy_best_first()
            elif algo_choice == "6":
                result = search_algorithms.dijkstra()
            elif algo_choice == "7":
                result = search_algorithms.weighted_a_star()
            elif algo_choice == "8":
                results = [
                    search_algorithms.bfs(),
                    search_algorithms.dfs(),
                    search_algorithms.ids(),
                    search_algorithms.a_star(),
                    search_algorithms.greedy_best_first(),
                    search_algorithms.dijkstra(),
                    search_algorithms.weighted_a_star()
                ]
                print_search_results(results)
                result = None
            else:
                print("Invalid choice")
                result = None
            
            if result:
                print_search_results([result])
                visualize_solution(game, result)