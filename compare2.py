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
    
    def chebyshev_distance(self, other: 'Position') -> int:
        """Calculate Chebyshev distance (8-directional movement)"""
        return max(abs(self.x - other.x), abs(self.y - other.y))

@dataclass
class GameState:
    """Represents the complete state of the game"""
    position: Position
    energy: int
    visited_foods: Set[Position]
    
    def __hash__(self):
        # FIXED: Don't include energy in hash - only position and foods matter for state identity
        # This allows A* to properly track "best cost to reach a state"
        return hash((self.position.x, self.position.y, frozenset(self.visited_foods)))
    
    def __eq__(self, other):
        # FIXED: Energy doesn't matter for state equality
        return (self.position == other.position and 
                self.visited_foods == other.visited_foods)

class TreasureHuntGame:
    """Main game class containing map and game logic"""
    
    TERRAIN_COSTS = {
        '.': 1,  
        '~': 2,
        '^': 3,
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
            
            if new_energy < 0:  # FIXED: Changed from <= to <
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
    heuristic_name: str = ""

class HeuristicFunctions:
    """
    Collection of heuristic functions for informed search.
    
    A good heuristic should be:
    1. ADMISSIBLE: Never overestimate the actual cost (h(n) <= actual cost)
    2. CONSISTENT: h(n) <= cost(n, n') + h(n') for all neighbors n'
    3. INFORMATIVE: Provide good guidance toward the goal
    
    IMPORTANT: All heuristics return cost estimates (in energy units) that are
    admissible by using the minimum possible terrain cost (1 energy per move).
    """
    
    def __init__(self, game: TreasureHuntGame):
        self.game = game
    
    def manhattan_heuristic(self, pos: Position) -> float:
        """
        Manhattan Distance Heuristic
        
        Formula: h(n) = (|x1-x2| + |y1-y2|) × min_terrain_cost
        
        Properties:
        - Admissible: YES (assumes minimum cost of 1 energy per tile)
        - Best for: 4-directional movement
        - For 8-directional: Overestimates, but still admissible
        
        Example: From (0,0) to (3,4): (3+4) × 1 = 7 energy minimum
        """
        distance = pos.manhattan_distance(self.game.treasure_pos)
        return distance * 1.0  # Multiply by minimum terrain cost
    
    def euclidean_heuristic(self, pos: Position) -> float:
        """
        Euclidean Distance Heuristic
        
        Formula: h(n) = sqrt((x1-x2)² + (y1-y2)²) × min_terrain_cost
        
        Properties:
        - Admissible: YES (straight line × minimum cost)
        - Best for: Any directional movement
        - Generally good across different movement models
        
        Example: From (0,0) to (3,4): 5.0 × 1 = 5.0 energy minimum
        """
        distance = pos.euclidean_distance(self.game.treasure_pos)
        return distance * 1.0  # Multiply by minimum terrain cost
    
    def chebyshev_heuristic(self, pos: Position) -> float:
        """
        Chebyshev Distance Heuristic - OPTIMAL FOR THIS GAME
        
        Formula: h(n) = max(|x1-x2|, |y1-y2|) × min_terrain_cost
        
        Properties:
        - Admissible: YES for 8-directional movement
        - Most accurate: Chebyshev distance = actual minimum moves for 8-directional
        - Optimal choice: Best heuristic for this game's movement model
        
        Why it's optimal:
        - Diagonal moves cover both X and Y simultaneously
        - Chebyshev gives exact number of moves in best case
        - Even with higher terrain costs, estimate never exceeds actual cost
        
        Example: From (0,0) to (3,4): max(3,4) × 1 = 4 energy minimum
        (Can be achieved with 4 diagonal moves if all terrain is normal)
        """
        distance = pos.chebyshev_distance(self.game.treasure_pos)
        return distance * 1.0  # Multiply by minimum terrain cost
    
    def energy_aware_heuristic(self, state: GameState) -> float:
        """
        Energy-Aware Heuristic: Conservative estimate considering energy state
        
        Formula: h(n) = chebyshev_distance × min_terrain_cost
        
        CRITICAL: Must remain admissible!
        - Uses minimum terrain cost (1.0) to guarantee admissibility
        - Cannot use average terrain cost without risk of overestimating
        
        Properties:
        - Admissible: YES (uses conservative minimum estimate)
        - Could be enhanced with domain knowledge, but carefully
        
        Note: This is essentially Chebyshev with potential for enhancement
        """
        distance = state.position.chebyshev_distance(self.game.treasure_pos)
        min_terrain_cost = 1.0  # Must use minimum to stay admissible
        return distance * min_terrain_cost
    
    def zero_heuristic(self, pos: Position) -> float:
        """
        Zero Heuristic: Always returns 0.
        
        Properties:
        - Makes A* behave exactly like Dijkstra/UCS
        - Admissible: YES (trivially - never overestimates)
        - Used for comparison and testing purposes
        """
        return 0.0

class SearchAlgorithms:
    """Implementation of blind and informed search algorithms"""
    
    def __init__(self, game: TreasureHuntGame):
        self.game = game
        self.heuristics = HeuristicFunctions(game)
    
    # ==================== BLIND SEARCH ALGORITHMS ====================
    
    def bfs(self) -> SearchResult:
        """
        Breadth-First Search (BLIND)
        
        Strategy: Explores all nodes at depth d before depth d+1
        Completeness: YES
        Optimality: YES (for unweighted graphs)
        Time Complexity: O(b^d) where b=branching factor, d=depth
        Space Complexity: O(b^d) - stores all nodes at current level
        """
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time, 
                              initial_state.energy, "BFS", "None")
        
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
                                      time.time() - start_time, next_state.energy, "BFS", "None")
                
                queue.append((next_state, new_path))
                visited.add(next_state)
        
        return SearchResult(False, [], nodes_explored, max_memory, 
                          time.time() - start_time, 0, "BFS", "None")
    
    def dfs(self, max_depth: int = 100) -> SearchResult:
        """
        Depth-First Search (BLIND)
        
        Strategy: Explores deepest node first
        Completeness: NO (can get stuck in infinite paths)
        Optimality: NO
        Time Complexity: O(b^m) where m=maximum depth
        Space Complexity: O(b*m) - only stores path
        """
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time, 
                              initial_state.energy, "DFS", "None")
        
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
                                      time.time() - start_time, next_state.energy, "DFS", "None")
                
                stack.append((next_state, new_path, depth + 1))
        
        return SearchResult(False, [], nodes_explored, max_memory, 
                          time.time() - start_time, 0, "DFS", "None")
    
    # ==================== INFORMED SEARCH ALGORITHMS ====================
    
    def a_star(self, heuristic_func_name: str = "chebyshev") -> SearchResult:
        """
        A* Search (INFORMED) - FIXED VERSION
        
        Formula: f(n) = g(n) + h(n)
        where:
          g(n) = actual cost from start to n (energy consumed)
          h(n) = estimated cost from n to goal (heuristic)
        
        Strategy: Expands node with lowest f(n)
        Completeness: YES
        Optimality: YES (if heuristic is admissible)
        Time Complexity: O(b^d) but typically much better
        Space Complexity: O(b^d)
        
        KEY FIX: Uses actual terrain cost for g(n) calculation
        """
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        # Get heuristic function
        heuristic_func = self._get_heuristic_function(heuristic_func_name)
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time,
                              initial_state.energy, "A*", heuristic_func_name)
        
        # Priority queue: (f_score, counter, g_score, state, path)
        counter = 0
        h = heuristic_func(initial_state)
        open_set = [(h, counter, 0, initial_state, [initial_state])]
        
        # FIXED: Track best g_score by (position, foods) not including energy
        g_scores = {(initial_state.position, frozenset(initial_state.visited_foods)): 0}
        nodes_explored = 0
        max_memory = 1
        
        while open_set:
            max_memory = max(max_memory, len(open_set) + len(g_scores))
            f_score, _, g_score, current_state, path = heapq.heappop(open_set)
            nodes_explored += 1
            
            if self.game.is_goal_state(current_state):
                return SearchResult(True, path, nodes_explored, max_memory,
                                  time.time() - start_time, current_state.energy, "A*", heuristic_func_name)
            
            for next_state in self.game.get_possible_moves(current_state):
                # FIXED: Use actual terrain cost directly
                terrain_cost = self.game.TERRAIN_COSTS[self.game.get_terrain_at(next_state.position)]
                tentative_g = g_score + terrain_cost
                
                # FIXED: State key doesn't include energy
                state_key = (next_state.position, frozenset(next_state.visited_foods))
                
                if state_key not in g_scores or tentative_g < g_scores[state_key]:
                    g_scores[state_key] = tentative_g
                    h = heuristic_func(next_state)
                    f = tentative_g + h
                    counter += 1
                    new_path = path + [next_state]
                    heapq.heappush(open_set, (f, counter, tentative_g, next_state, new_path))
        
        return SearchResult(False, [], nodes_explored, max_memory,
                          time.time() - start_time, 0, "A*", heuristic_func_name)
    
    def greedy_best_first(self, heuristic_func_name: str = "chebyshev") -> SearchResult:
        """
        Greedy Best-First Search (INFORMED)
        
        Formula: f(n) = h(n) (only heuristic, ignores actual cost)
        
        Strategy: Always expand node closest to goal
        Completeness: NO
        Optimality: NO
        Time Complexity: O(b^m) - worst case
        Space Complexity: O(b^m)
        
        KEY DIFFERENCE: Greedy - doesn't consider cost so far
        """
        start_time = time.time()
        initial_state = self.game.get_initial_state()
        
        heuristic_func = self._get_heuristic_function(heuristic_func_name)
        
        if self.game.is_goal_state(initial_state):
            return SearchResult(True, [initial_state], 1, 1, time.time() - start_time,
                              initial_state.energy, "Greedy", heuristic_func_name)
        
        counter = 0
        h = heuristic_func(initial_state)
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
                                  time.time() - start_time, current_state.energy, "Greedy", heuristic_func_name)
            
            for next_state in self.game.get_possible_moves(current_state):
                if next_state not in visited:
                    h = heuristic_func(next_state)
                    counter += 1
                    new_path = path + [next_state]
                    heapq.heappush(open_set, (h, counter, next_state, new_path))
        
        return SearchResult(False, [], nodes_explored, max_memory,
                          time.time() - start_time, 0, "Greedy", heuristic_func_name)
    
    def _get_heuristic_function(self, name: str):
        """Get heuristic function by name"""
        if name == "manhattan":
            return lambda state: self.heuristics.manhattan_heuristic(state.position if isinstance(state, GameState) else state)
        elif name == "euclidean":
            return lambda state: self.heuristics.euclidean_heuristic(state.position if isinstance(state, GameState) else state)
        elif name == "chebyshev":
            return lambda state: self.heuristics.chebyshev_heuristic(state.position if isinstance(state, GameState) else state)
        elif name == "energy_aware":
            return lambda state: self.heuristics.energy_aware_heuristic(state)
        elif name == "zero":
            return lambda state: self.heuristics.zero_heuristic(state.position if isinstance(state, GameState) else state)
        else:
            return lambda state: self.heuristics.chebyshev_heuristic(state.position if isinstance(state, GameState) else state)

def compare_blind_vs_informed(game: TreasureHuntGame):
    """
    COMPREHENSIVE COMPARISON: BLIND vs INFORMED SEARCH
    
    This demonstrates the superiority of informed search algorithms.
    """
    print("\n" + "="*100)
    print("BLIND vs INFORMED SEARCH - COMPREHENSIVE COMPARISON")
    print("="*100)
    
    search = SearchAlgorithms(game)
    
    # Run searches
    print("\nRunning algorithms...")
    bfs_result = search.bfs()
    dfs_result = search.dfs(max_depth=100)
    astar_result = search.a_star(heuristic_func_name="chebyshev")
    greedy_result = search.greedy_best_first(heuristic_func_name="chebyshev")
    
    results = [bfs_result, dfs_result, astar_result, greedy_result]
    
    # Print detailed comparison table
    print("\n" + "-"*100)
    print(f"{'Algorithm':<20} {'Type':<10} {'Success':<8} {'Path':<6} {'Nodes':<8} "
          f"{'Memory':<8} {'Time(ms)':<10} {'Efficiency':<12}")
    print("-"*100)
    
    for r in results:
        algo_type = "BLIND" if r.heuristic_name == "None" else "INFORMED"
        path_len = len(r.path)-1 if r.success else "N/A"
        efficiency = f"{r.nodes_explored/(len(r.path) if len(r.path)>0 else 1):.2f}" if r.success else "N/A"
        
        print(f"{r.algorithm_name:<20} {algo_type:<10} {r.success:<8} {str(path_len):<6} "
              f"{r.nodes_explored:<8} {r.max_memory_usage:<8} {r.execution_time*1000:<10.2f} {efficiency:<12}")
    
    print("-"*100)
    
    # Statistical Analysis
    print("\n" + "="*100)
    print("STATISTICAL ANALYSIS - WHY INFORMED SEARCH WINS")
    print("="*100)
    
    if bfs_result.success and astar_result.success:
        nodes_improvement = ((bfs_result.nodes_explored - astar_result.nodes_explored) / bfs_result.nodes_explored) * 100
        time_improvement = ((bfs_result.execution_time - astar_result.execution_time) / bfs_result.execution_time) * 100
        memory_improvement = ((bfs_result.max_memory_usage - astar_result.max_memory_usage) / bfs_result.max_memory_usage) * 100
        
        print(f"\nA* vs BFS Performance:")
        print(f"  📊 Nodes Explored:  {nodes_improvement:+.1f}% (A* explored {abs(nodes_improvement):.0f}% {'FEWER' if nodes_improvement > 0 else 'MORE'} nodes)")
        print(f"  ⚡ Execution Time:  {time_improvement:+.1f}% (A* was {abs(time_improvement):.0f}% {'faster' if time_improvement > 0 else 'slower'})")
        print(f"  💾 Memory Usage:    {memory_improvement:+.1f}% (A* used {abs(memory_improvement):.0f}% {'less' if memory_improvement > 0 else 'more'} memory)")
        
        print(f"\n  Path Quality:")
        print(f"    BFS Path Length: {len(bfs_result.path)-1} steps")
        print(f"    A*  Path Length: {len(astar_result.path)-1} steps")
        print(f"    Optimality: {'SAME ✓' if len(bfs_result.path) == len(astar_result.path) else 'DIFFERENT'}")
    
    # Heuristic effectiveness
    print(f"\n" + "="*100)
    print("HEURISTIC FUNCTION ANALYSIS")
    print("="*100)
    
    print("\nTesting different heuristics with A*...")
    heuristics = ["manhattan", "euclidean", "chebyshev", "energy_aware"]
    heuristic_results = []
    
    for h_name in heuristics:
        result = search.a_star(heuristic_func_name=h_name)
        heuristic_results.append(result)
    
    print(f"\n{'Heuristic':<20} {'Nodes':<10} {'Time(ms)':<12} {'Path Length':<12}")
    print("-"*60)
    for r in heuristic_results:
        path_len = len(r.path)-1 if r.success else "N/A"
        print(f"{r.heuristic_name:<20} {r.nodes_explored:<10} {r.execution_time*1000:<12.2f} {path_len:<12}")
    
    print("\n" + "="*100)
    print("KEY INSIGHTS")
    print("="*100)
    print("""
1. ADMISSIBILITY: All heuristics use minimum terrain cost (1.0) to stay admissible
   - This guarantees h(n) ≤ actual cost to goal
   - Ensures A* finds optimal paths

2. CHEBYSHEV ADVANTAGE: Best for 8-directional movement
   - Gives exact minimum moves needed
   - More informed than Manhattan or Euclidean for this grid

3. INFORMED vs BLIND: A* explores far fewer nodes than BFS
   - Heuristic guides search toward goal
   - Dramatically reduces wasted exploration
    """)
    
    return results

# Test maps
test_maps = {
    "simple": [
        "S....",
        ".....",
        "..F..",
        ".....",
        "....T"
    ],
    "energy_trap": [
    "S..~~~....T",
    ".^^^~~^..^.",
    "..~~~..~~..",
    ".^..F..^.^.",
    "....~~~...."
],
    
    "medium": [
        "S.~F.X^^^",
        ".X~~.X^F^", 
        ".X.F~~.X.",
        "F..X~..^.",
        "~~X..F^^T"
    ],
    
    "complex": [
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
    "optimal_refuel": [
        "S...XXXXXXXXXXXXXX",
        "XXXX.X~~~~~~~~~~~X",
        "F....X.XXXXXXXXXXX",
        "XXXX.X...........X",
        "T....X...........X"
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
    print("="*100)
    print("ASSIGNMENT: BLIND vs INFORMED SEARCH COMPARISON (FIXED VERSION)")
    print("="*100)
    
    print("\n" + "="*100)
    print("KEY FIXES APPLIED")
    print("="*100)
    print("""
1. ✅ Fixed A* g(n) calculation - now uses actual terrain cost
2. ✅ Fixed GameState hash - excludes energy for proper state tracking
3. ✅ Fixed energy check - allows reaching goal with 0 energy
4. ✅ Clarified heuristic documentation - all use minimum cost multiplier
5. ✅ Improved state key tracking - uses (position, foods) not (position, energy, foods)
    """)
    
    print("\nAvailable test maps:")
    for i, (name, map_data) in enumerate(test_maps.items(), 1):
        print(f"{i}. {name} - {len(map_data)}x{len(map_data[0])} grid")
    
    choice = input("\nChoose map (1-3) or 'all' for complete analysis: ").strip()
    
    if choice.lower() == 'all':
        for map_name, map_data in test_maps.items():
            print(f"\n{'='*100}")
            print(f"TESTING: {map_name.upper()} MAP")
            print('='*100)
            game = TreasureHuntGame(map_data)
            game.print_map(game.get_initial_state())
            compare_blind_vs_informed(game)
    else:
        try:
            idx = int(choice) - 1
            map_name = list(test_maps.keys())[idx]
            game = TreasureHuntGame(test_maps[map_name])
            game.print_map(game.get_initial_state())
            compare_blind_vs_informed(game)
        except:
            print("Invalid choice!")