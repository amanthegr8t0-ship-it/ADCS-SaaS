import numpy as np
import heapq
from math import sqrt

class Grid_Maker():

    def __init__(self, grid_order=20):
        self.grid = np.ones([grid_order, grid_order])
        self.grid_or = grid_order

    def obstacle(self, col, row):
        self.grid[col, row] = 0


    def available_cell(self, col, row):
        return bool(self.grid[col, row])
    

class AStar:

    def __init__(self, grid):
        self.grid = grid

    def available_neighbours(self, col, row):
        all_neighbours = [(col-1, row-1), (col-1, row), (col-1, row+1), (col, row-1), (col, row+1), (col+1, row-1),(col+1, row),(col+1, row+1),]
        valid = []
        for n_col, n_row in all_neighbours:
            if n_row >= 0 and n_col >= 0 and n_row < self.grid.grid_or and n_col < self.grid.grid_or and self.grid.available_cell(n_col, n_row) :
                valid.append((n_col, n_row))

        return valid
    
    def find_path(self, start, goal):
        if start == goal:
            return [start]
        open_set = []
        heapq.heappush(open_set, (0,start))
        closed_set = set()
        came_from = {}
        g_score = {start:0}
        goal_x, goal_y = goal
        while open_set:
            # step 1 - pop lowest f
            f, current = heapq.heappop(open_set)
            # step 2 - if goal, stop
            if current == goal:
                wpath = []
                last_one = goal
                while last_one!= start:
                    wpath.append(last_one)
                    last_one = came_from[last_one]
                wpath.append(start)
                wpath.reverse()
                return wpath

            closed_set.add(current)
            # step 4 - loop through neighbors
            for neighbour in self.available_neighbours(*current):
                # step 5 - skip if in closed_set
                if neighbour in closed_set:
                    continue
                current_x, current_y = current
                neighbour_x, neighbour_y = neighbour
                x_dist = (neighbour_x-current_x)**2
                y_dist = (neighbour_y-current_y)**2
                dist = sqrt(x_dist+y_dist)
                if dist == 1:
                    tentative_g = g_score[current] + 1
                elif dist == sqrt(2):
                    tentative_g = g_score[current]+sqrt(2)

                if tentative_g < g_score.get(neighbour, float('inf')):
                    came_from[neighbour] = current
                    # update came_from
                    g_score[neighbour] = tentative_g
                    # update g_score
                    huretic = sqrt((neighbour_x-goal_x)**2+(neighbour_y-goal_y)**2)

                    f = tentative_g + huretic
                    # calculate h, calculate f, push to open_set
                    heapq.heappush(open_set, (f, neighbour))

        return []

if __name__ == "__main__":
    grid = Grid_Maker()
    for i in range(20):
        grid.obstacle(10, i)  # add some obstacles
    astar = AStar(grid)
    path = astar.find_path((5, 0), (19,19))  # pick start and goal
    print(path)