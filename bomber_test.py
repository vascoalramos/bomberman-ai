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

        self.level = 1
        self.lives = lives
        self.bombs = None
        self.enemies = None
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
        self.balloom_kill_attempt_counter = 0

        self.resting = False

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

    def get_key_to_position(self, curr_pos, next_pos):
        """
        Method that converts an intended position to a key stroke

        @param curr_pos: initial postion
        @param next_pos: intended position
        @rtype: string
        @returns: key stroke to get to the intended position
        """
        if (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1]) in [(0, 1), (0, 2)]:
            return "s"
        elif (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1]) in [
            (0, -1),
            (0, -2),
        ]:
            return "w"
        elif (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1]) in [(1, 0), (2, 0)]:
            return "d"
        elif (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1]) in [
            (-1, 0),
            (-2, 0),
        ]:
            return "a"
        else:
            return ""

    def get_starting_running_direction(self):
        """
        Method that picks a safe starting position for the bomberman to run in.
        Changes the self.running_direction variable to the direction bomberman should run to
        Possibly changes the variable self.running to the 3 (indicating running state 3)
        """
        possible_directions = []

        if self.check_if_wall_is_not_blocked_or_enemy((self.pos[0] - 1, self.pos[1])):
            possible_directions.append("LEFT")
        if self.check_if_wall_is_not_blocked_or_enemy((self.pos[0] + 1, self.pos[1])):
            possible_directions.append("RIGHT")
        if self.check_if_wall_is_not_blocked_or_enemy((self.pos[0], self.pos[1] - 1)):
            possible_directions.append("UP")
        if self.check_if_wall_is_not_blocked_or_enemy((self.pos[0], self.pos[1] + 1)):
            possible_directions.append("DOWN")

        logger.debug("POSSIBLE DIRECTIONS " + str(possible_directions))

        # If we have more than one possible running path, let's check which of those have a safe spot (i.e different row and col than the bomb)
        if len(possible_directions) > 1:
            possible_directions = self.check_if_safe_is_blocked(
                possible_directions)
            self.running = 3

        if len(possible_directions) != 0:
            self.running_direction = possible_directions[0]
        else:  # Used for the case where we screwed ourselves and there are no safe places to run to..just run to our last position and pray
            if self.last_pos[0] > self.pos[0]:
                self.running_direction = "RIGHT"
            elif self.last_pos[0] < self.pos[0]:
                self.running_direction = "LEFT"
            elif self.last_pos[1] > self.pos[0]:
                self.running_direction = "DOWN"
            else:
                self.running_direction = "UP"

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

        for starting_direction in possible_directions:
            logger.debug(
                "CHECKING IF SAFE POSITION IS CLEAR - " + starting_direction)

            # Check if safe positions are reachable
            if self.check_if_path_is_clear(starting_direction, no_of_moves):
                for safe_position in safe_positions[starting_direction]:
                    if self.check_if_wall_is_not_blocked_or_enemy(safe_position):
                        return [starting_direction]

            # Just in case let's see if we can run in that direction for longer than the bomb's radius
            if self.bombs != []:
                no_of_moves = self.my_powerups.count("Flames") + 4

            # And remove it if it's not
            if not self.check_if_path_is_clear(starting_direction, no_of_moves):
                possible_directions.remove(starting_direction)

        return possible_directions

    def check_if_path_is_clear(self, direction, no_of_moves):
        """
        Method that checks if a path is safe, i.e if we can move no_of_moves in a
        path without encountering a wall or an enemy

        @param direction: the direction we want to be moving in
        @param no_of_moves: how many moves we want to move in that direction
        @rtype: bool
        @returns: Whether the path is safe or not
        """

        positions = {  # All possibly safe positions from the bomb
            "UP": [
                (self.pos[1] - no_of_moves - 1),
                (self.pos[1] - 1),
            ],
            "DOWN": [
                (self.pos[1] + 1),
                (self.pos[1] + no_of_moves + 1),
            ],
            "LEFT": [
                (self.pos[0] - no_of_moves - 1),
                (self.pos[0] - 1),

            ],
            "RIGHT": [
                (self.pos[0] + 1),
                (self.pos[0] + no_of_moves + 1),
            ],
        }

        logger.info("CHECKING IF PATH IS CLEAR - " + direction)
        for pos_inc in range(positions[direction][0], positions[direction][1]):
            test_pos = (self.pos[0], pos_inc) if direction == 'UP' or direction == 'DOWN' else (
                pos_inc, self.pos[1])

            logger.info("       CHECKING POSITION - " + str(test_pos))

            if not self.check_if_wall_is_not_blocked_or_enemy(test_pos):
                return False

        return True

    def check_if_wall_is_not_blocked_or_enemy(self, position, enemy_safety = True):
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
            self.manhattan_distance(position, enemy["pos"]) <= 2
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
                    self.pos, self.up
                )
            elif self.running_direction == "DOWN":
                key = self.get_key_to_position(
                    self.pos, self.down
                )
            elif self.running_direction == "LEFT":
                key = self.get_key_to_position(
                    self.pos, self.left
                )
            elif self.running_direction == "RIGHT":
                key = self.get_key_to_position(
                    self.pos, self.right
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
                    self.pos, self.left
                )
                self.running = 2

            # RIGHT
            elif self.check_if_wall_is_not_blocked_or_enemy(
                self.right
            ):
                key = self.get_key_to_position(
                    self.pos, self.right
                )
                self.running = 2

            else:  # In case we cant move to a safe position yet keep moving in our direction
                if self.running_direction == "UP":
                    key = self.get_key_to_position(
                        self.pos, self.up
                    )

                else:  # Down
                    key = self.get_key_to_position(
                        self.pos, self.down
                    )
        else:
            # UP
            if self.check_if_wall_is_not_blocked_or_enemy(
                self.up
            ):
                key = self.get_key_to_position(
                    self.pos, self.up
                )
                self.running = 2

            # DOWN
            elif self.check_if_wall_is_not_blocked_or_enemy(
                self.down
            ):
                key = self.get_key_to_position(
                    self.pos, self.down
                )
                self.running = 2

            else:  # In case we cant move to a safe position yet keep moving in our direction
                if self.running_direction == "RIGHT":
                    key = self.get_key_to_position(
                        self.pos, self.right
                    )

                else:
                    key = self.get_key_to_position(
                        self.pos, self.left
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

        
        return self.go_to_target(self.powerups[0][0],"POWER_UP")


    def go_to_enemy(self, distance_to_nearest_wall, nearest_wall, nearest_enemy, nearest_enemy_id, nearest_enemy_type, distance_to_enemy):
        """
        Method that returns the key we should press to get and try to kill an enemy

        @returns: The key
        """
        
        logger.debug(
           "CHASING NEAREST ENEMY - KILLCOUNTER: " +
            str(self.kill_attempt_counter)
        )
        logger.info("KILL COUNTER IS AT - " + str(self.kill_attempt_counter))

        # Reset the kill counter if we're going after a new enemy
        if self.kill_target == None or self.kill_target != nearest_enemy_id:
            self.kill_target = nearest_enemy_id
            self.kill_target_type = nearest_enemy_type
            
            self.kill_attempt_counter = 0

        
        if self.kill_attempt_counter > 2 or self.level == 1:
            logger.info("KILL COUNTER EXCEEDED!")
            # If we try to kill enemies 3 times in a row, its better to just take a break and take a hike
            
            if nearest_enemy_type == "Balloom": #If all there's left are ballooms
                logger.info("CHASING BALLOOM")
                return self.kill_balloom(distance_to_enemy,nearest_enemy,distance_to_nearest_wall,nearest_wall)
            
            elif self.walls != []:  # If there are still walls, go blow one up
                logger.debug("GOING TO NEAREST WALL")
                if distance_to_nearest_wall == 1:
                    self.kill_attempt_counter = 0
                    self.kill_target = None
                    self.kill_target_type = None
                    return "B"
                
                return self.go_to_target(nearest_wall,"FIND_WALL")
            
            else:  # Else, take a break, hopefully this breaks the loop
                logger.info("OTHER ENEMY")
                if distance_to_enemy <= 1:
                    return "B"
                else:
                    if not self.resting:
                        logger.info("STARTING TO REST")
                        self.resting == True
                        self.kill_attempt_counter = 5
                    else:
                        logger.info("STOPPING REST")
                        if self.kill_attempt_counter == 2:
                            self.resting = False
                    logger.info("RESTING")
                    self.kill_attempt_counter -= 1
                    return ""

        if distance_to_enemy <= 2:
            self.kill_attempt_counter += 1
            return "B"

        key = self.go_to_target(nearest_enemy, "KILL")
        if key == "B":
            self.kill_attempt_counter += 1

        return key
        

    def kill_balloom(self, distance_to_enemy,nearest_enemy, distance_to_nearest_wall, nearest_wall):
        """
        Method that returns the best key if you want to kill a balloom

        @returns: The key
        """
        logger.info(
                "BALLOOM KILL ATTEMPT - " + str(self.balloom_kill_attempt_counter))
        if self.balloom_kill_attempt_counter < -4:   #After destroying 5 walls lets go and try to kill a guy
            logger.info("TRYING AGAIN ")
            if distance_to_enemy <= 1:
                logger.info("OOOOOOOOOOOOOOOOOOOOOOOF")
                self.balloom_kill_attempt_counter = 0
                return "B"

            key = self.go_to_target(nearest_enemy, "KILL")
            if key == "B":
                logger.info("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOFY")
                self.balloom_kill_attempt_counter = 0
            return key
            
        if self.walls != []:
            logger.info("GOING TO NEAREST WALL")
            if distance_to_nearest_wall == 1:
                logger.info("   DESTROYED WALL - " + str(self.balloom_kill_attempt_counter))
                self.balloom_kill_attempt_counter -= 1
                return "B"

            return self.go_to_target(nearest_wall,"FIND_WALL")

        # Pick best Corner (closest non-blocked)
        # UPPER LEFT
            # 1,1 ; 2,1 ; 1,2
        # UPPER RIGHT
            # self.map.hor_tiles-2,1 ; self.map.hor_tiles -3,1 ; self.map.hor_tiles-2, 2
        # LOWER LEFT
            # 1, self.map.ver_tiles-2 ; 1,self.map.ver_tiles-3 ; 2,self.map.ver_tiles-2
        # LOWER RIGHT
            # self.map.hor_tiles-2, self.map.ver_tiles-2 ; self.map.hor_tiles-3, self.map.ver_tiles-2
        possible_corners = [
            (1, 2), (2, 1), (1, 1),  # Upper Left Corner
            (self.map.hor_tiles-2,1), (self.map.hor_tiles -3,1), (self.map.hor_tiles-2, 2),  # Upper Right Corner
            (1, self.map.ver_tiles-2), (1,self.map.ver_tiles-3), (2,self.map.ver_tiles-2),  # Lower Left Corner
            (self.map.hor_tiles-2, self.map.ver_tiles-2), (self.map.hor_tiles-3, self.map.ver_tiles-2), (self.map.hor_tiles-2, self.map.ver_tiles-3),  # Lower Right Corner
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
                return "B"
            return ""
        else:
            logger.debug(
                "GOING TO KILLING FLOOR - " + str(corner))

            return self.go_to_target(corner,"")

        return ""

    def go_to_target(self,target,strategy,enemy_safety = True):
        """
        Method that returns the best key if you want to go to a target

        @returns: The key
        """
        path = self.tree.search_for_path(
            self.map,
            self.pos,
            tuple(target),
            self.enemies,
            objective=strategy,
        )

        if path is None:
            key = None
        else:
            if len(path) == 1:
                if self.check_if_wall_is_not_blocked_or_enemy(path[0],enemy_safety):
                    key = self.get_key_to_position(self.pos, path[0])
                else:
                    key = "B"
            else:
                if self.check_if_wall_is_not_blocked_or_enemy(path[1],enemy_safety):
                    key = self.get_key_to_position(self.pos, path[1])
                else:
                    key = "B"

        return key

    def next_move(self):
        """
        Method that decides our Bombermans's next move

        @rtype: string
        @returns: string with the key stroke to the next move. If no path is find returns None
        """

        # If there is a bomb on the map
        if self.bombs != []:
            logger.debug("RUNNING FROM BOMB - STAGE: " + str(self.running))
            return self.run_from_bomb()

        # Reset our running variables
        elif self.running == 1 or self.running == 2:
            self.running=0

        # If there is a powerup on the map
        if self.powerups != []:
            logger.debug("PICKING UP POWERUP")
            return self.get_powerup()

        # If there are still walls on the map check which one's the closest
        if self.walls != []:
            nearest_wall=self.find_nearest_wall()
            distance_to_nearest_wall=self.manhattan_distance(
                self.pos, nearest_wall)
        else:
            distance_to_nearest_wall=None
            nearest_wall=None

        # If there are enemies alive
        if self.enemies != []:
            (
                nearest_enemy,
                nearest_enemy_id,
                nearest_enemy_type,
            )=self.find_nearest_enemy()
            

            distance_to_enemy=self.manhattan_distance(
                self.pos, nearest_enemy)

            # Pick our Strategy
            if self.level == 1:
                strategy="KILL"
            else:
                if (
                    distance_to_nearest_wall is None
                    or distance_to_enemy <= distance_to_nearest_wall
                ):
                    strategy="KILL"
                else:
                    strategy="FIND_WALL"

            # Execute our Strategy
            if strategy == "KILL":  #Go kill an enemy
                return self.go_to_enemy(distance_to_nearest_wall,nearest_wall,nearest_enemy,nearest_enemy_id,nearest_enemy_type,distance_to_enemy)

            elif self.walls != []:  #Go destroy a wall (if there are any)
                logger.debug("GOING TO NEAREST WALL")

                # Reset our kill control variables
                self.kill_attempt_counter=0
                self.kill_target=None
                self.kill_target_type=None

                if distance_to_nearest_wall == 1:
                    return "B"

                return self.go_to_target(nearest_wall,strategy)

        # If the exit is available and we've completed all other conditions
        if self.exit != [] and len(self.my_powerups) == self.level and self.enemies == []:
            logger.debug("GOING TO EXIT")
            return self.go_to_target(tuple(self.exit), "EXIT")

        elif self.walls != []:
            logger.debug("GOING TO NEAREST WALL")

            if distance_to_nearest_wall == 1:
                return "B"

            return self.go_to_target(nearest_wall, "FIND_WALL")

        return ""
