import logging

from tree_search_star import SearchTree

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("Bomberman")
logger.setLevel(logging.INFO)


class Bomberman:
    """
    Class that implements an intelligent agent that plays the role of Bomberman.
    """

    def __init__(self, lives=3, pos=(1, 1)):
        """
        Bomberman constructor

        @param lives: bomberman number of lives [default value: 3]
        @param pos: bomberman initial postion [default value: (1,1)]
        """
        self.pos = pos
        self.last_pos = pos

        self.map = None

        self.powerup = None

        self.level = 0
        self.lives = lives
        self.bombs = None
        self.enemies = []
        self.walls = None
        self.my_powerups = []
        self.exit = None

        self.possible_steps = None

        self.tree = SearchTree()

        self.right = None
        self.left = None
        self.up = None
        self.down = None

        self.running = 0
        self.running_direction = None

        self.kill_attempt_counter = 0
        self.kill_target = None
        self.kill_target_type = None
        self.nearest_enemy = None

        self.walls_destroyed = 5

        self.resting = 0

        self.border_thiccness = 0

        self.last_four_pos = []
        self.looping = 0
        self.cant_reach_enemy = 0
        self.nearest_wall_to_enemy = None
        self.caught_powerup = False

        logger.debug("Bomberman created successfully!")

    def update_state(self, state, mapa):
        """
        Method that updates our bomberman's state

        @param state: current state of the game
        @param mapa: current state of the game's map
        """
        self.last_pos = self.pos
        self.pos = tuple(state["bomberman"])

        self.map = mapa

        # Calculate the border's thickness
        # When we level up, calculate the border's T H I C C ness:
        if self.level != state["level"]:
            self.caught_powerup = False
            self.cant_reach_enemy = 0
            self.looping = 0
            self.nearest_wall_to_enemy = None
            self.last_four_pos = []
            test_pos = (0, 0)
            thickness = 0
            while True:
                logger.debug("THICC: " + str(self.border_thiccness))

                if self.check_if_wall_is_not_blocked_or_enemy((test_pos[0]+thickness, test_pos[1]+thickness)):
                    self.border_thiccness = thickness
                    break
                thickness += 1

        self.level = state["level"]
        self.lives = state["lives"]
        self.bombs = state["bombs"]
        self.enemies = state["enemies"]
        self.walls = state["walls"]
        self.powerups = state["powerups"]
        self.exit = state["exit"]

        self.right = (self.pos[0] + 1, self.pos[1])
        self.left = (self.pos[0] - 1, self.pos[1])
        self.up = (self.pos[0], self.pos[1] - 1)
        self.down = (self.pos[0], self.pos[1] + 1)

        logger.debug("Updated Bomberman state successfully!")

    def find_nearest_wall(self):
        """
        Method that computes the Manhattan distance between the Bomberman and all the walls on the map

        @rtpye: tuple
        @returns: a tuple with the coordinates of the nearest wall to the Bomberman
        """
        x, y, distance = min(
            [
                (wall[0], wall[1], self.manhattan_distance(self.pos, wall))
                for wall in self.walls
            ],
            key=lambda e: e[2],
        )
        return (x, y)

    def find_nearest_wall_to_target(self, target, visited_walls):
        """
        Method that computes the Manhattan distance between the Nearest Enemy and all the walls on the map

        @rtpye: tuple
        @returns: a tuple with the coordinates of the nearest wall to the Bomberman
        """
        x, y, distance = min(
            [(wall[0], wall[1], self.manhattan_distance(target, wall)) for wall in self.walls if wall not in visited_walls
             ],
            key=lambda e: e[2],
        )

        return (x, y)

    def find_nearest_enemy(self):
        """
        Method that computes the Manhattan distance between the Bomberman and all the enemies on the map

        @rtpye: tuple
        @eturns: a tuple with the coordinates of the nearest enemy to the Bomberman
        """
        x, y, distance, enemy_id, enemy_type = min(
            [
                (
                    enemy["pos"][0],
                    enemy["pos"][1],
                    self.manhattan_distance(self.pos, tuple(enemy["pos"])),
                    enemy["id"],
                    enemy["name"],
                )
                for enemy in self.enemies
            ],
            key=lambda e: e[2],
        )
        return (x, y), enemy_id, enemy_type

    def manhattan_distance(self, p1, p2):
        """
        Method that computes the Manhattan distance between two positions in a grid.

        @param p1: first position
        @param p2: second position
        @rtype: int
        @returns: Manhattan distance between the 2 given positions
        """
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def get_key_to_position(self, next_pos):
        """
        Method that converts an intended position to a key stroke

        @param curr_pos: initial postion
        @param next_pos: intended position
        @rtype: string
        @returns: key stroke to get to the intended position
        """
        if self.down == next_pos:
            return "s"
        elif self.up == next_pos:
            return "w"
        elif self.right == next_pos:
            return "d"
        elif self.left == next_pos:
            return "a"
        else:
            return ""

    def get_starting_running_direction(self):
        # TODO: FIX THAT GODDAMNED BUG
        """
        Method that picks a safe starting position for the bomberman to run in.
        Changes the self.running_direction variable to the direction bomberman should run to
        Possibly changes the variable self.running to the 3 (indicating running state 3)
        """
        possible_directions = []

        if self.check_if_wall_is_not_blocked_or_enemy(self.left):
            possible_directions.append("LEFT")
        if self.check_if_wall_is_not_blocked_or_enemy(self.right):
            possible_directions.append("RIGHT")
        if self.check_if_wall_is_not_blocked_or_enemy(self.up):
            possible_directions.append("UP")
        if self.check_if_wall_is_not_blocked_or_enemy(self.down):
            possible_directions.append("DOWN")

        logger.debug("POSSIBLE DIRECTIONS " + str(possible_directions))

        # Prioritize last pos
        last_pos_dir = None
        if len(self.last_four_pos) > 0:
            if self.up in self.last_four_pos:
                last_pos_dir = "UP"
            elif self.down in self.last_four_pos:
                last_pos_dir = "DOWN"
            elif self.left in self.last_four_pos:
                last_pos_dir = "LEFT"
            elif self.left in self.last_four_pos:
                last_pos_dir = "RIGHT"
        logger.debug("LAST RUNNING DIR: " + str(last_pos_dir))


        # If we have more than one possible running path, let's check which of those have a safe spot (i.e different row and col than the bomb)
        safe_possible_directions = []
        if len(possible_directions) > 1:
            logger.debug("   MULTIPLE DIRECTIONS")
            self.running = 3
            safe_possible_directions = self.check_if_safe_is_blocked(
                possible_directions)
            logger.debug("   OUT OF MULITPLE DIRECTIONS - " + str(possible_directions) + " -  PICKED: " + str(safe_possible_directions))

        # Set our running direction
        if len(possible_directions) == 1:
            logger.debug("   DIRECTION PICKED (ONLY ONE)")
            self.running_direction = possible_directions[0]

        elif len(safe_possible_directions) != 0:
            logger.debug("   DIRECTION PICKED WITH SAFE SPOT")
            self.running_direction = safe_possible_directions[0]
        
        else:  # Used for the case where we screwed ourselves and there are no safe places to run to..just run to our last position and pray
            logger.debug("   NO DIRECTIONS WITH SAFE POSITIONS AVAILABLE CHECKING IN WHICH DIRECTION WE CAN RUN IN")

            #if last_pos_dir in possible_directions:
            #    logger.debug("   RUNNING BACK THROUGH WHERE WE CAME FROM")
            #    self.running_direction = last_pos_dir
            #else:

            runnable_directions = []
            for direction in possible_directions:
                # Just in case let's see if we can run in that direction for longer than the bomb's radius
                no_of_moves = self.my_powerups.count("Flames") + 4
                logger.debug("       CHECKING STRAIGHT DIRECTION - " + direction + " FOR " + str(no_of_moves) + " MOVES")
                # And remove it if it's not

                if self.check_if_path_is_clear(direction, no_of_moves):
                    logger.debug("      DIRECTION - " + direction + " - IS SAFE TO BE RUN IN!" )
                    runnable_directions.append(direction)
        
            if runnable_directions != []:
                logger.debug("   DIRECTION PICKED STRAIGHT LINE RUNNING - " + str(runnable_directions[0]))
                self.running_direction = runnable_directions[0]
            else:
                logger.debug("   DIRECTION PICKED - OMEGA F")
                if last_pos_dir is not None:
                    self.running_direction = last_pos_dir
                else:
                    self.running_direction = possible_directions[0]

    def check_if_safe_is_blocked(self, possible_directions):
        """
        Method that checks for safe spots given a list of possible running directions

        @param possible_directions: possible running directions
        @rtype: list
        @returns: all directions that lead to a safe spot
        """
        safe_positions = {  # All possibly safe positions from the bomb
            "UP": [
                (self.pos[0] - 1, self.pos[1] - 2),
                (self.pos[0] + 1, self.pos[1] - 2),
            ],
            "DOWN": [
                (self.pos[0] - 1, self.pos[1] + 2),
                (self.pos[0] + 1, self.pos[1] + 2),
            ],
            "LEFT": [
                (self.pos[0] - 2, self.pos[1] - 1),
                (self.pos[0] - 2, self.pos[1] + 1),
            ],
            "RIGHT": [
                (self.pos[0] + 2, self.pos[1] - 1),
                (self.pos[0] + 2, self.pos[1] + 1),
            ],
        }

        no_of_moves = 2

        if "Detonator" not in self.my_powerups:  # TODO: TEST FOR DIFFERENT VALUES
            no_of_moves_for_enemies = 5
        else:
            no_of_moves_for_enemies = 2

        for starting_direction in possible_directions:
            logger.debug(
                "   CHECKING IF SAFE POSITION IS CLEAR - " + str(starting_direction))

            # Check if safe positions are reachable
            if self.check_if_path_is_clear(starting_direction, no_of_moves):
                logger.debug(
                    "       PATH TO SAFE POSITIONS IS FREE")

                for safe_position in safe_positions[starting_direction]:
                    if self.check_if_wall_is_not_blocked_or_enemy(safe_position):
                        logger.debug(
                                    "       SAFE POSITION IS NOT BLOCKED")
                        if starting_direction == "UP" or starting_direction == "DOWN":
                            if self.check_if_path_is_clear("LEFT", no_of_moves_for_enemies, safe_position) and self.check_if_path_is_clear("RIGHT", no_of_moves_for_enemies, safe_position):
                                logger.debug(
                                    "       NO ENEMY NEARBY, WE'RE SAFE!")
                                return [starting_direction]
                            logger.debug(
                                    "       ENEMY NEARBY, TOO DANGEROUS!")
                        if starting_direction == "LEFT" or starting_direction == "RIGHT":
                            if self.check_if_path_is_clear("UP", no_of_moves_for_enemies, safe_position) and self.check_if_path_is_clear("DOWN", no_of_moves_for_enemies, safe_position):
                                logger.debug(
                                    "       NO ENEMY NEARBY, WE'RE SAFE!")
                                return [starting_direction]
                            logger.debug(
                                    "       ENEMY NEARBY, TOO DANGEROUS!")
                        return [starting_direction]
                
            logger.debug("   DIRECTION - " + starting_direction + " - ISN'T POSSIBLE")
                            
        return []

    def check_if_path_is_clear(self, direction, no_of_moves, starting_position=None):
        """
        Method that checks if a path is safe, i.e if we can move no_of_moves in a
        path without encountering a wall or an enemy

        @param direction: the direction we want to be moving in
        @param no_of_moves: how many moves we want to move in that direction
        @rtype: bool
        @returns: Whether the path is safe or not
        """

        if starting_position == None:
            starting_position = self.pos

        if direction == "UP":
            test_pos = (starting_position[0], starting_position[1] - 1)
            inc_type = (0, -1)
        elif direction == "DOWN":
            test_pos = (starting_position[0], starting_position[1] + 1)
            inc_type = (0, 1)
        elif direction == "LEFT":
            test_pos = (starting_position[0] - 1, starting_position[1])
            inc_type = (-1, 0)
        else:
            test_pos = (starting_position[0] + 1, starting_position[1])
            inc_type = (1, 0)

        logger.debug("           CHECKING IF PATH IS CLEAR - " +
                     direction + " STARTING AT " + str(starting_position))
        
        for increment in range(no_of_moves):
            pos_inc = tuple([increment*coord for coord in inc_type])
            next_pos = (test_pos[0] + pos_inc[0], test_pos[1] + pos_inc[1])

            logger.debug("               CHECKING POSITION - " + str(next_pos) + " : " +
                         str(self.check_if_wall_is_not_blocked_or_enemy(next_pos)))
            if not self.check_if_wall_is_not_blocked_or_enemy(next_pos):
                logger.debug("                   NOT AVAILABLE RETURNING FALSE")
                return False

        logger.debug("           WE CAN RUN THIS PATH")
        return True

    def check_if_wall_is_not_blocked_or_enemy(self, position, enemy_safety=True):
        """
        Method that checks if a given position is blocked by a wall or an enemy

        @param position: The position we want to check
        @param enemy_safety: Wether we want to be careful about enemies or not

        @rtype: bool
        @returns: True if its not blocked, False if its blocked
        """
        logger.debug("   CHECKING POS - " + str(position))

        wallpass = False
        if "Wallpass" in self.my_powerups:
            wallpass = True

        if not self.map.is_blocked(position, wallpass) and (not enemy_safety or not any(
            self.manhattan_distance(position, enemy["pos"]) <= 1
            for enemy in self.enemies
        )):
            return True
        return False

    def run_from_bomb(self):
        """
        Method that returns the key we should press to run from the bomb

        @returns: The key
        """
        if self.running == 0:  # If we haven't started running yet
            self.running = 1
            self.get_starting_running_direction()  # Get our starting running direction
        elif self.running == 2:  # We've reached a safe position
            if "Detonator" in self.my_powerups:
                return "A"
            return ""

        if (
            self.running == 3
        ):  # In case we have multiple run paths, make it so Erman runs one house away
            if self.running_direction == "UP":
                key = self.get_key_to_position(
                    self.up
                )
            elif self.running_direction == "DOWN":
                key = self.get_key_to_position(
                    self.down
                )
            elif self.running_direction == "LEFT":
                key = self.get_key_to_position(
                    self.left
                )
            elif self.running_direction == "RIGHT":
                key = self.get_key_to_position(
                    self.right
                )

            self.running = 1

            return key

        # Check if we can run to our safe scenarios
        if self.running_direction == "UP" or self.running_direction == "DOWN":
            # LEFT
            if self.check_if_wall_is_not_blocked_or_enemy(
                self.left
            ):
                key = self.get_key_to_position(
                    self.left
                )
                self.running = 2

            # RIGHT
            elif self.check_if_wall_is_not_blocked_or_enemy(
                self.right
            ):
                key = self.get_key_to_position(
                    self.right
                )
                self.running = 2

            else:  # In case we cant move to a safe position yet keep moving in our direction
                if self.running_direction == "UP":
                    key = self.get_key_to_position(
                        self.up
                    )

                else:  # Down
                    key = self.get_key_to_position(
                        self.down
                    )
        else:
            # UP
            if self.check_if_wall_is_not_blocked_or_enemy(
                self.up
            ):
                key = self.get_key_to_position(
                    self.up
                )
                self.running = 2

            # DOWN
            elif self.check_if_wall_is_not_blocked_or_enemy(
                self.down
            ):
                key = self.get_key_to_position(
                    self.down
                )
                self.running = 2

            else:  # In case we cant move to a safe position yet keep moving in our direction
                if self.running_direction == "RIGHT":
                    key = self.get_key_to_position(
                        self.right
                    )

                else:
                    key = self.get_key_to_position(
                        self.left
                    )
        return key

    def get_powerup(self):
        """
        Method that returns the key we should press to get to a powerup

        @returns: The key
        """

        distance = self.manhattan_distance(self.pos, self.powerups[0][0])
        # when distance equals to 1, it means that the next move will put the agent on the power up
        if distance == 1:
            self.my_powerups.append(self.powerups[0][1])
            self.caught_powerup = True

        return self.go_to_target(self.powerups[0][0], "POWER_UP", explode_col_row=True)

    def kill_balloom(self, distance_to_enemy):
        """
        Method that returns the best key if you want to kill a balloom.
        Strategy involves picking the closest corner and going to wait to wait for the enemy to come to us

        @returns: The key
        """

        if distance_to_enemy <= 1 and (self.pos[0] == self.nearest_enemy[0] or self.pos[1] == self.nearest_enemy[1]):
            self.kill_attempt_counter += 1
            return "B"

        possible_corners = [
            (self.border_thiccness, self.border_thiccness+1),
            (self.border_thiccness+1, self.border_thiccness),
            (self.border_thiccness, self.border_thiccness),  # Upper Left Corner

            (self.map.hor_tiles-self.border_thiccness-1, self.border_thiccness),
            (self.map.hor_tiles - self.border_thiccness - 2, self.border_thiccness),
            (self.map.hor_tiles-self.border_thiccness-1,
             self.border_thiccness+1),  # Upper Right Corner

            (self.border_thiccness, self.map.ver_tiles-self.border_thiccness-1),
            (self.border_thiccness+1, self.map.ver_tiles-self.border_thiccness-1),
            (self.border_thiccness, self.map.ver_tiles - \
             self.border_thiccness-2),  # Lower Left Corner

            (self.map.hor_tiles-self.border_thiccness-1,
             self.map.ver_tiles-self.border_thiccness-1),
            (self.map.hor_tiles-self.border_thiccness-2,
             self.map.ver_tiles-self.border_thiccness-1),
            (self.map.hor_tiles-self.border_thiccness-1, self.map.ver_tiles - \
             self.border_thiccness-2),  # Lower Right Corner
        ]

        # First remove the blocked corners
        for corner in possible_corners:
            if not self.check_if_wall_is_not_blocked_or_enemy(corner):
                possible_corners.remove(corner)

        # Now get the one with the smallest distance to us
        corner = min(possible_corners, key=lambda possible_corner: self.manhattan_distance(
            self.pos, possible_corner))

        if self.pos == (corner[0] - 1, corner[1]) or self.pos == (corner[0] + 1, corner[1]) or self.pos == (corner[0], corner[1] - 1) or self.pos == (corner[0], corner[1] + 1):
            logger.debug("DISTANCE TO ENEMY: " + str(distance_to_enemy))
            if distance_to_enemy < 4:
                self.kill_attempt_counter += 1
                return "B"
            return ""
        else:
            logger.debug(
                "GOING TO KILLING FLOOR - " + str(corner))

            return self.go_to_target(corner, "", explode_col_row=True)

        return ""

    def kill_enemy(self, nearest_enemy_id, nearest_enemy_type, distance_to_enemy, nearest_wall, distance_to_nearest_wall, path_to_enemy=None):
        """
        Method that returns the best key to press to go to an enemy and kill it

        @returns: The key
        """

        # Reset the kill counter if we're going after a new enemy
        if self.kill_target == None or self.kill_target != nearest_enemy_id:
            self.kill_target = nearest_enemy_id
            self.kill_target_type = nearest_enemy_type
            self.kill_attempt_counter = 0
        logger.debug(
            "CHASING NEAREST ENEMY - KILLCOUNTER: "
            + str(self.kill_attempt_counter)
        )
        are_all_enemies_balloms = len(
            [enemy for enemy in self.enemies if enemy["name"] == "Balloom"]) == len(self.enemies)
        if (
            self.kill_attempt_counter > 5 or are_all_enemies_balloms
        ):  # If we try to kill enemies 3 times in a row or the majority of enemies are ballooms, its better to just take a break and take a hike
            logger.debug("GODDAMNED BALLOOMS EVERY IMMA GO KILL A WALL")

            # For the first level destroy 5 walls and then try to kill a balloom
            if self.walls != [] and self.walls_destroyed > 6 and are_all_enemies_balloms:  # If all enemies are ballooms
                if distance_to_enemy <= 1:
                    self.walls_destroyed = 0
                    return "B"

                key = self.go_to_target(self.nearest_enemy, "KILL")
                if key == "B":
                    self.walls_destroyed = 0
                return key

            # Go to a wall
            if self.walls != []:  # If there are still walls, go blow one up
                logger.debug("NEVERMIND IMMA GO KILL A WALL")

                if distance_to_nearest_wall == 1:
                    self.kill_attempt_counter = 0
                    self.kill_target = None
                    self.kill_target_type = None
                    self.walls_destroyed += 1
                    return "B"

                key = self.go_to_target(nearest_wall, "FIND_WALL")
                if key == "B":
                    self.kill_attempt_counter = 0
                    self.kill_target = None
                    self.kill_target_type = None
                    self.walls_destroyed += 1

                return key

            # Go to an enemy
            elif self.kill_target_type == "Balloom":
                logger.debug("BLOW THAT Balloom")
                return self.kill_balloom(distance_to_enemy)
            elif (
                self.kill_target_type == "Oneal"
            ):  # For Oneals the best way to kill them is to be more agressive
                logger.debug("BLOW THAT Oneal")
                if distance_to_enemy < 1 and (self.pos[0] == self.nearest_enemy[0] or self.pos[1] == self.nearest_enemy[1]):
                    self.kill_attempt_counter += 1
                    return "B"
                else:
                    logger.debug("TAKING A BREAK FROM Oneals")
                    self.kill_attempt_counter = 0
                    return (
                        ""
                    )
            else:  # Else, take a break, hopefully this breaks the loop
                logger.debug("TAKING A BREAK")
                self.kill_attempt_counter = 0
                return ""
        if distance_to_enemy <= 2 and (self.pos[0] == self.nearest_enemy[0] or self.pos[1] == self.nearest_enemy[1]):   #TODO SE AQUELES GAJOS Q FOGEM FOREM MT RAPIDOS, MUDAR ISTO PARA 3?
            logger.debug("BLOW THAT MOTHERFUCKER")
            self.kill_attempt_counter += 1
            return "B"

        if path_to_enemy == None:
            return self.go_to_target(self.nearest_enemy, "KILL", explode_col_row=True)
        else:
            return path_to_enemy

    def go_to_target(self, target, strategy, bomb=True, ignore_safety=False, explode_col_row=True):
        """
        Method that returns the key to go to a specific target. Uses our A* Searching algorithm

        @returns: The key
        """

        path = self.tree.search_for_path(
            self.map,
            self.pos,
            tuple(target),
            self.enemies,
            objective=strategy,
        )

        key = ""

        if path is None:
            logger.debug("CANT FIND PATH TO " + str(target) +
                         " WITH STRATEGY " + strategy)
            key = None

        else:
            if len(path) == 1:
                if ignore_safety or self.check_if_wall_is_not_blocked_or_enemy(path[0]):
                    key = self.get_key_to_position(path[0])
                elif bomb:
                    if not explode_col_row or (self.pos[0] == self.nearest_enemy[0] or self.pos[1] == self.nearest_enemy[1]):
                        logger.debug("OH SHIT A WILD BOI APPEARED")
                        key = "B"
            else:
                if ignore_safety or self.check_if_wall_is_not_blocked_or_enemy(path[1]):
                    key = self.get_key_to_position(path[1])
                elif bomb:
                    if not explode_col_row or (self.pos[0] == self.nearest_enemy[0] or self.pos[1] == self.nearest_enemy[1]):
                        logger.debug("OH SHIT A WILD BOI APPEARED")
                        key = "B"

        logger.debug("NEXT KEY IS: " + str(key) + " Strat: " + strategy)
        if key != "" and key is not None:
            self.resting = 0

        return key

    def next_move(self):
        """
        Method that decides our Bombermans's next move

        @rtype: string
        @returns: string with the key stroke to the next move. If no path is find returns None
        """
        # If the exit is available and we've completed all other conditions
        if self.exit != [] and (self.caught_powerup or self.level > 10) and self.enemies == []:
            logger.debug("GOING TO EXIT")
            return self.go_to_target(self.exit, "EXIT", False, True)

        # Make it so he doesn't sit still for too long:
        if self.last_pos == self.pos:
            self.resting += 1

        if self.resting > 20:
            self.resting -= 5
            if self.bombs != []:
                return "A"
            if self.exit != [] and len(self.my_powerups) == self.level and self.enemies == []:
                return self.go_to_target(self.exit, "EXIT", False, True)
            if self.walls != []:
                nearest_wall = self.find_nearest_wall()
                distance_to_nearest_wall = self.manhattan_distance(
                    self.pos, nearest_wall)
                if distance_to_nearest_wall == 1:
                    return "B"

                return self.go_to_target(nearest_wall, "FIND_WALL", explode_col_row=True)

        # If there is a bomb on the map
        if self.bombs != []:
            logger.debug("RUNNING FROM BOMB - STAGE: " + str(self.running))
            return self.run_from_bomb()

        # Reset our running variables
        elif self.running == 1 or self.running == 2:
            self.running = 0

        # if there is a powerup on the map
        if self.powerups != []:
            logger.debug("PICKING UP POWERUP")
            return self.get_powerup()

        # If there are still walls on the map check which one's the closest
        if self.walls != []:
            nearest_wall = self.find_nearest_wall()
            distance_to_nearest_wall = self.manhattan_distance(
                self.pos, nearest_wall)
        else:
            distance_to_nearest_wall = None
            nearest_wall = None


        # If there are enemies alive
        if self.enemies != []:
            (
                self.nearest_enemy,
                nearest_enemy_id,
                nearest_enemy_type,
            ) = self.find_nearest_enemy()
            distance_to_enemy = self.manhattan_distance(
                self.pos, self.nearest_enemy)

            # Check if we're in a loop
            logger.debug("CHECKING FOR LOOPS")
            if self.last_pos in self.last_four_pos:
                logger.debug("THIS MIGHT BE A LOOP: " + str(self.looping))
                if self.looping < 11:
                    self.looping += 3
            else:
                if self.looping > 0:
                    logger.debug("PROBABLY A FALSE ALARM: " +
                                str(self.looping))
                    self.looping -= 1

            if len(self.last_four_pos) < 4:
                    self.last_four_pos.append(self.last_pos)
            else:
                self.last_four_pos = self.last_four_pos[1:]
                self.last_four_pos.append(self.last_pos)

            if self.looping > 10:
                logger.debug("WE'RE IN A LOOP")
                if self.walls != []:
                    if distance_to_nearest_wall == 1:
                        self.looping = 0
                        return "B"
                    return self.go_to_target(nearest_wall, "FIND_WALL",bomb=False)

            # Can I reach the enemy or should I go to a wall?
            path_to_enemy = None
            if self.level == 1:
                return self.kill_enemy(nearest_enemy_id, nearest_enemy_type, distance_to_enemy, nearest_wall, distance_to_nearest_wall)
            else:
                # Check if we can reach enemy
                if self.cant_reach_enemy:
                    logger.debug("CHECK IF WE CAN REACH ENEMY!")

                    # if self.kill_target != nearest_enemy_id:
                    #    logger.debug("CHANGING ENEMY SO WE GUCCI!")
                    #    self.cant_reach_enemy = 0
                    #    self.nearest_wall_to_enemy = None

                    if self.walls != []:  # Pick the wall closest to the enemy
                        logger.debug("GOING TO NEAREST WALL TO ENEMY - " +
                                    str(self.nearest_wall_to_enemy))
                        wall_array = []

                        if self.nearest_wall_to_enemy is None:
                            target = self.nearest_enemy
                            while True:
                                self.nearest_wall_to_enemy = self.find_nearest_wall_to_target(
                                    target, wall_array)
                                logger.debug("   TRYING WALL: " + str(target))
                                path = self.go_to_target(
                                    self.nearest_wall_to_enemy, "FIND_WALL", bomb=False)

                                if path is not None:
                                    break
                                target = self.nearest_wall_to_enemy
                                wall_array.append(
                                    list(self.nearest_wall_to_enemy))
                                logger.debug("       WALLS: " + str(wall_array))

                        distance_to_nearest_wall = self.manhattan_distance(
                            self.pos, self.nearest_wall_to_enemy)
                        if distance_to_nearest_wall == 1:
                            self.cant_reach_enemy = 0
                            self.nearest_wall_to_enemy = None

                            self.kill_attempt_counter = 0
                            self.kill_target = None
                            self.kill_target_type = None
                            return "B"

                        return self.go_to_target(self.nearest_wall_to_enemy, "FIND_WALL", bomb=False)
                    else:
                        return None

                else:
                    path_to_enemy = self.go_to_target(
                        self.nearest_enemy, "KILL")

                    if path_to_enemy == None:
                        self.cant_reach_enemy = 1
                        return ""
                    else:
                        logger.debug("GOING TO ENEMY")
                        return self.kill_enemy(nearest_enemy_id, nearest_enemy_type, distance_to_enemy, nearest_wall, distance_to_nearest_wall)

        elif self.walls != []:
            logger.debug("GOING TO NEAREST WALL")

            if distance_to_nearest_wall == 1:
                return "B"

            return self.go_to_target(nearest_wall, "FIND_WALL", explode_col_row=True)

        return ""
