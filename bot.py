import copy
import random
import math
from collections import Counter
from game_message import *


class Role:
    def __init__(self, base):
        self.position_history = [None, None, None]
        self.base: list[Position] = base

    def action(self, character: Character, state: TeamGameState):
        pass

    def euclidian_distance(self, p1: Position, p2: Position):
        return math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2)

    def find_drop_cells(self, base: list[Position], state: TeamGameState):
        """return available drop cells"""
        drop_cells = copy.deepcopy(base)
        for item in state.items:
            if item.position in base:
                drop_cells.remove(item.position)

        return drop_cells

    def find_shortest_path(self, state: TeamGameState, start: Position, end: Position) -> Optional[list[Position]]:
        from collections import deque

        class PositionWrapper:
            def __init__(self, position: Position):
                self.position = position

            def __eq__(self, other):
                if isinstance(other, PositionWrapper):
                    return self.position.x == other.position.x and self.position.y == other.position.y
                return False

            def __hash__(self):
                return hash((self.position.x, self.position.y))

        def is_within_bounds(pos: Position) -> bool:
            return 0 <= pos.x < state.map.width and 0 <= pos.y < state.map.height

        def is_walkable(pos: Position) -> bool:
            return state.map.tiles[pos.x][pos.y] == TileType.EMPTY

        if not is_within_bounds(start) or not is_within_bounds(end) or not is_walkable(start) or not is_walkable(end):
            return None

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        visited = set()
        queue = deque([(start, [])])

        while queue:
            current, path = queue.popleft()
            wrapped_current = PositionWrapper(current)

            if wrapped_current == PositionWrapper(end):
                return path + [end]

            if wrapped_current in visited:
                continue

            visited.add(wrapped_current)

            for dx, dy in directions:
                new_pos = Position(current.x + dx, current.y + dy)
                if is_within_bounds(new_pos) and is_walkable(new_pos) and PositionWrapper(new_pos) not in visited:
                    queue.append((new_pos, path + [current]))

        return None

    def get_items_on_my_side(self, items, state: TeamGameState):
        items_on_my_side = []

        for i in items:
            if state.teamZoneGrid[i.position.x][i.position.y] == state.currentTeamId:
                items_on_my_side.append(i)

        return items_on_my_side

    def get_items_on_enemy_side(self, items, state: TeamGameState):
        items_on_enemy_side = []

        for i in items:
            if state.teamZoneGrid[i.position.x][i.position.y] != state.currentTeamId:
                items_on_enemy_side.append(i)

        return items_on_enemy_side

    def is_path_safe(self, path: list[Position], state: TeamGameState):
        """Check if the path is safe"""
        if path is None:
            return False
        for pos in path:
            print("pos ", pos)
            for enemy in state.otherCharacters:
                print("enemy ", enemy.position)
                if enemy.alive and enemy.position == pos:
                    print('PATH IS NOT SAFE')
                    return False
        return True


@dataclass_json
@dataclass
class ActionResponse:
    """ActionResponse."""

    action: Action
    """Action."""
    new_role: Role = None
    """New role."""


class Collecter(Role):
    def __init__(self, base):
        super().__init__(base)
        self.drop_destination = None

    def closest_lingot(self, character: Character, lingots: list[Item]) -> Item:
        smallest_dist = math.inf
        current_lingot = lingots[0]
        for lingot in lingots:
            dist = self.euclidian_distance(
                character.position, lingot.position) - lingot.value
            if dist < smallest_dist:
                smallest_dist = dist
                current_lingot = lingot

        return current_lingot

    def action(self, character: Character, state: TeamGameState) -> ActionResponse:

        if self.drop_destination is not None:  # is going to drop
            if character.position == self.drop_destination:
                # arrived to destination, drop item
                if character.numberOfCarriedItems <= 1:
                    self.drop_destination = None
                else:
                    # after dropping, check if we can drop in the closest drop cell
                    drop_cells = self.find_drop_cells(self.base, state)
                    has_close_drop = False
                    for i in range(character.position.x-1, character.position.x+2):
                        for j in range(character.position.y-1, character.position.y+2):
                            if Position(i, j) in drop_cells:
                                has_close_drop = True
                                self.drop_destination = Position(i, j)
                    if has_close_drop == False:
                        for i in range(0, 10):
                            self.drop_destination = random.choice(
                                drop_cells)
                            # check if the path is safe
                            path = self.find_shortest_path(
                                state, character.position, self.drop_destination)
                            if self.is_path_safe(path, state):
                                break

                return ActionResponse(DropAction(characterId=character.id))
            else:
                return ActionResponse(MoveToAction(characterId=character.id, position=self.drop_destination))

        if character.numberOfCarriedItems == state.constants.maxNumberOfItemsCarriedPerCharacter:
            # return to base to drop
            self.drop_destination = random.choice(
                self.find_drop_cells(self.base, state))
            return ActionResponse(MoveToAction(characterId=character.id, position=self.drop_destination))

        lingots = []
        my_characters_items = []
        for char in state.yourCharacters:
            for carriedItem in char.carriedItems:
                my_characters_items.append(carriedItem)

        for item in state.items:
            if item.value > 0 and item not in my_characters_items and item.position not in self.base:
                lingots.append(item)
        if lingots == []:
            # change role to Dumper or Protecter
            radiant_type = ["radiant_slag", "radiant_core"]
            radiant_items = [i for i in state.items if i.type in radiant_type]
            self.radiant_items_on_my_side = self.get_items_on_my_side(
                radiant_items, state)
            # if len(self.radiant_items_on_my_side) > 0:
            #     new_role = Dumper(self.base)
            # else:
            #     new_role = Protecter(self.base)
            new_role = Dumper(self.base)

            move_to = random.choice(self.base)
            return ActionResponse(MoveToAction(characterId=character.id, position=move_to), new_role)

        move_to = self.closest_lingot(character, lingots).position
        if character.position == move_to:
            return ActionResponse(GrabAction(characterId=character.id))

        path = self.find_path(move_to, state, lingots, character)

        if len(path) < 3:
            if not self.is_path_safe(path, state):
                move_to = random.choice(lingots).position

        return ActionResponse(MoveToAction(characterId=character.id,
                                           position=move_to))

    def find_path(self, move_to, state: TeamGameState, lingots: list[Item], character: Character) -> Optional[list[Position]]:
        i = 0
        path = self.find_shortest_path(state, character.position, move_to)
        while path is None and i < 15:
            temp_list = copy.deepcopy(lingots)
            for lingot in temp_list:
                if lingot.position == move_to:
                    lingots.remove(lingot)
            move_to = self.closest_lingot(
                character, lingots).position
            path = self.find_shortest_path(state, character.position, move_to)

            print(path)

            i += 1
        return path

    def find_path_no_cars(self, move_to, state: TeamGameState, lingots: list[Item], character: Character) -> Optional[list[Position]]:
        i = 15
        path = self.find_shortest_path(state, character.position, move_to)
        print("IS SAFE? ", self.is_path_safe(path, state))
        while self.is_path_safe(path, state) is False and i < 15:
            temp_list = copy.deepcopy(lingots)
            for lingot in temp_list:
                if lingot.position == move_to:
                    lingots.remove(lingot)
            move_to = self.closest_lingot(
                character, lingots).position
            path = self.find_shortest_path(state, character.position, move_to)

            print("TEST PATH: ", path)

            i += 1
        return path


class Protecter(Role):
    def action(self, character: Character, state: TeamGameState) -> ActionResponse:
        intruders = self.find_intruders(state)
        if intruders == []:
            move_to = random.choice(self.base)
            return ActionResponse(MoveToAction(characterId=character.id, position=move_to))
        else:
            move_to = self.closest_intruders(intruders, character).position
            return ActionResponse(MoveToAction(characterId=character.id, position=move_to))

    def find_intruders(self, state: TeamGameState):
        """Find enemies in our base"""
        intruders = []
        for enemy in state.otherCharacters:
            if enemy.alive and enemy.position in self.base:
                intruders.append(enemy)
        return intruders

    def closest_intruders(self, intruders: list[Character], character: Character):
        smallest_dist = math.inf
        closest = intruders[0]
        for intruder in intruders:
            dist = self.euclidian_distance(
                intruder.position, character.position)
            if dist < smallest_dist:
                smallest_dist = dist
                closest = intruder
        return closest


class Dumper(Role):

    def __init__(self, base):
        super().__init__(base)

        self.radiant_items_on_my_side = []
        self.enemy_base_positions = []
        self.radiant_object_reached = False
        self.flag_dumper_on_mission = False

    def calculate_enemy_base(self, state: TeamGameState) -> list[Position]:
        enemy_base = []
        for x, col in enumerate(state.teamZoneGrid):
            for y, row in enumerate(col):
                if row != state.currentTeamId and state.map.tiles[x][y] == TileType.EMPTY:
                    enemy_base.append(Position(x, y))
        return enemy_base

    def collect_data(self, state: TeamGameState):
        radiant_type = ["radiant_slag", "radiant_core"]
        radiant_items = [i for i in state.items if i.type in radiant_type]
        self.radiant_items_on_my_side = self.get_items_on_my_side(
            radiant_items, state)
        self.enemy_base_positions = self.calculate_enemy_base(state)

        # remove from enemy base position the position of the radiant items on enemy side
        for i in state.items:
            if i.position in self.enemy_base_positions:
                self.enemy_base_positions.remove(i.position)

        # print("self.enemy_base_positions before", self.enemy_base_positions, "\n")

        # Remove the neutral zone from the enemy base positions
        # the neutral zone is the zone where the teamZoneGrid is empty string ""
        for x, col in enumerate(state.teamZoneGrid):
            for y, row in enumerate(col):
                if row == "":
                    if Position(x, y) in self.enemy_base_positions:
                        self.enemy_base_positions.remove(Position(x, y))

        # print("self.enemy_base_positions AFTER", self.enemy_base_positions, "\n")

    def make_move(self, character: Character, state: TeamGameState) -> Action:

        if not self.radiant_items_on_my_side:

            if character.numberOfCarriedItems == 0:

                our_zone_positions = []
                for x, col in enumerate(state.teamZoneGrid):
                    for y, row in enumerate(col):
                        if row == state.currentTeamId:
                            our_zone_positions.append(Position(x, y))
                return ActionResponse(MoveToAction(characterId=character.id, position=our_zone_positions[0]))

            else:
                self.flag_dumper_on_mission = True

        elif self.flag_dumper_on_mission == False:

            target_item = self.radiant_items_on_my_side[0]
            if character.position == target_item.position:

                return ActionResponse(GrabAction(characterId=character.id))

            if character.numberOfCarriedItems < state.constants.maxNumberOfItemsCarriedPerCharacter:

                return ActionResponse(MoveToAction(characterId=character.id, position=target_item.position))
            else:
                self.flag_dumper_on_mission = True

        closest_enemy_tile = self.get_closest_enemy_tile(character)
        if closest_enemy_tile and character.position == closest_enemy_tile:
            if character.numberOfCarriedItems <= 1:
                self.flag_dumper_on_mission = False

            return ActionResponse(DropAction(characterId=character.id))
        return ActionResponse(MoveToAction(characterId=character.id, position=closest_enemy_tile))

    def get_closest_enemy_tile(self, character: Character) -> Position:
        closest_tile = min(
            self.enemy_base_positions,
            key=lambda tile: self.euclidian_distance(character.position, tile),
            default=None
        )
        return closest_tile

    def action(self, character: Character, state: TeamGameState) -> ActionResponse:

        self.collect_data(state)
        return self.make_move(character, state)


class Bot:
    def __init__(self):
        self.character_roles = {}
        print("Initializing your super mega duper bot")

    def find_base(self, state: TeamGameState) -> list[Position]:
        base = []
        for x, col in enumerate(state.teamZoneGrid):
            for y, row in enumerate(col):
                if row == state.currentTeamId and state.map.tiles[x][y] == TileType.EMPTY:
                    base.append(Position(x, y))

        return base

    def initialize(self, character: Character, yourCharacters: list[Character]) -> Role:
        """Role dispatching algorithm"""
        if len(yourCharacters) <= 2:
            return Collecter(self.base)

        else:
            count = Counter(type(role)
                            for role in self.character_roles.values())

            if count[Dumper] < 1:
                return Dumper(self.base)

            return Collecter(self.base)

    def get_radiant(self, state: TeamGameState):
        radiant_type = ["radiant_slag", "radiant_core"]
        radiant_items = [i for i in state.items if i.type in radiant_type]
        return Role.get_items_on_my_side(None, radiant_items, state)

    def dispatch(self, state: TeamGameState):

        count = Counter(type(role)
                        for role in self.character_roles.values())
        if len(self.get_radiant(state)) > 0 and count[Dumper] == 0:
            for k, v in self.character_roles.items():
                if type(v) != Dumper:
                    self.character_roles[k] = Dumper(self.base)
                    break

        if len(self.get_radiant(state)) == 0 and count[Dumper] > 0:
            for k, v in self.character_roles.items():
                if type(v) == Dumper:
                    self.character_roles[k] = Collecter(self.base)
                    break

    def emergency(self, state: TeamGameState):
        pass

    def get_next_move(self, game_message: TeamGameState):
        """
        Here is where the magic happens, for now the moves are not very good. I bet you can do better ;)
        """
        actions = []

        if game_message.tick % 200 == 0:
            self.dispatch(game_message)
        for character in game_message.yourCharacters:
            # initialize characters at first tick
            if game_message.tick == 1:
                self.base = self.find_base(game_message)
                self.character_roles[character.id] = self.initialize(
                    character, game_message.yourCharacters)

            character_role = self.character_roles[character.id]
            action_response: ActionResponse = character_role.action(
                character, game_message)
            actions.append(action_response.action)
            if action_response.new_role is not None:
                print(f"{character.id} changed role to {
                      action_response.new_role}")
                self.character_roles[character.id] = action_response.new_role

        # You can clearly do better than the random actions above! Have fun!
        return actions
