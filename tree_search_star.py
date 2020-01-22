class SearchNode:
    def __init__(self, pos, parent=None, cost_to_origin=0, cost_to_target=0):
        self.pos = pos  # Might have to change to tuple
        self.parent = parent
        self.neighbours = []

        self.cost_to_origin = cost_to_origin
        self.cost_to_target = cost_to_target

    def get_total_cost(self):
        """
        Function that computes our node's current total cost
        """
        return self.cost_to_origin + self.cost_to_target

    def __str__(self):
        return f"Pos: {self.pos}, Parent: {self.parent.pos}"

    def __repr__(self):
        return str(self)


class SearchTree:
    def __init__(self):
        self.root = None
        self.target_pos = None

        self.mapa = None
        self.objective = None

        self.open_nodes = []
        self.closed_nodes = []
        self.newly_created_nodes = []
        self.limit = 1500   #TODO: TEST WITH DIFFERENT VALUES

    def search_for_path(
        self,
        mapa,
        current_pos,
        target_pos,
        enemies,
        time_to_explode=None,
        objective="FIND_WALL",
        dangerous_tiles=[],
    ):
        """
        Function used to search for the best path between a given position and target
        @param mapa: Our current map
        @param current_pos: Our root node's position
        @param target_pos: Our target's position
        """
        self.mapa = mapa
        self.objective = objective

        self.root = SearchNode(current_pos)
        self.target_pos = target_pos

        self.open_nodes = [self.root]
        self.closed_nodes = []

        self.newly_created_nodes = []

        open_nodes_number = 0

        while self.open_nodes != []:
            # Get the currently open, lowest cost node
            current_node = min(self.open_nodes, key=lambda node: node.get_total_cost())
            
            self.open_nodes.remove(current_node)
            self.closed_nodes.append(current_node)

            # Check if that node is the goal
            if self.check_if_goal_reached(current_node.pos, target_pos, objective):
                return self.get_path(current_node)

            if (
                current_node.neighbours == []
            ):  # Compute the node's neighbours if it has none yet
                self.compute_node_neighbours(
                    current_node, enemies, time_to_explode, dangerous_tiles
                )

            for neighbour_node in current_node.neighbours:
                if neighbour_node in self.closed_nodes:
                    continue

                new_cost_to_neighbour = current_node.cost_to_origin + 1
                if (
                    neighbour_node not in self.open_nodes
                    or new_cost_to_neighbour < neighbour_node.cost_to_origin
                ):
                    neighbour_node.cost_to_origin = new_cost_to_neighbour
                    neighbour_node.parent = current_node

                    if neighbour_node not in self.open_nodes:
                        self.open_nodes.append(neighbour_node)
                        open_nodes_number += 1

            if open_nodes_number > self.limit:
                return None

        return None

    def compute_distance(self, pos_one, pos_two):
        """
        Function that computes the possible shortest distance between 2 positions
        @param pos_one: Starting position
        @param pos_one: Target position
        """
        return abs(pos_two[0] - pos_one[0] + pos_two[1] - pos_one[1])

    def compute_node_neighbours(self, node, enemies, time_to_explode, dangerous_tiles):
        """
        Function that computes all possible moves starting at a given node and adds them to the node's neighbours
        @param node: The node who'se neighbours we want to discover
        """
        for i in ["w", "a", "s", "d"]:
            if self.objective == "POWER_UP" or self.objective == "EXIT":
                cx, cy = node.pos
                if i == "w":
                    next_pos = cx, cy - 1
                if i == "a":
                    next_pos = cx - 1, cy
                if i == "s":
                    next_pos = cx, cy + 1
                if i == "d":
                    next_pos = cx + 1, cy

                if not self.mapa.is_blocked(next_pos) or next_pos == self.target_pos:
                    # If we still haven't created that node, create it
                    if not any(
                        created_node.pos == next_pos
                        for created_node in self.newly_created_nodes
                    ):
                        neighbour = SearchNode(
                            next_pos,
                            node,
                            node.cost_to_origin + 1,
                            self.compute_distance(next_pos, self.target_pos),
                        )
                        node.neighbours.append(neighbour)
                        self.newly_created_nodes.append(neighbour)
                    else:
                        node.neighbours.append(
                            [
                                created_node
                                for created_node in self.newly_created_nodes
                                if created_node.pos == next_pos
                            ][0]
                        )

            else:
                next_pos = self.mapa.calc_pos(node.pos, i)
                if next_pos != node.pos:
                    # If we still haven't created that node, create it
                    if not any(
                        created_node.pos == next_pos
                        for created_node in self.newly_created_nodes
                    ):
                        neighbour = SearchNode(
                            next_pos,
                            node,
                            node.cost_to_origin + 1,
                            self.compute_distance(next_pos, self.target_pos),
                        )
                        node.neighbours.append(neighbour)
                        self.newly_created_nodes.append(neighbour)
                    else:
                        node.neighbours.append(
                            [
                                created_node
                                for created_node in self.newly_created_nodes
                                if created_node.pos == next_pos
                            ][0]
                        )

    def check_if_goal_reached(self, test_pos, target_pos, objective):
        """
        Function used to check if we've reached our goal
        @param node: The node we want to know the path to
        """
        if objective == "FIND_WALL":
            return (
                test_pos == (target_pos[0] - 1, target_pos[1])
                or test_pos == (target_pos[0] + 1, target_pos[1])
                or test_pos == (target_pos[0], target_pos[1] - 1)
                or test_pos == (target_pos[0], target_pos[1] + 1)
            )
        return test_pos == target_pos

    def get_path(self, node):
        """
        Function used to backtrack and return our path
        @param node: The node we want to know the path to
        """
        if node.parent == None:
            return [node.pos]
        path = self.get_path(node.parent)
        path += [node.pos]
        return path

