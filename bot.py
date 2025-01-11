import copy
import random
import math
from game_message import *


class Role:
    def __init__(self, base):
        self.base: list[Position] = base

    def action(self, character: Character, state: TeamGameState) -> Action:
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


class Collecter(Role):
    def __init__(self, base):
        super().__init__(base)
        self.drop_destination = None

    def closest_lingot(self, character: Character, lingots: list[Item]) -> Item:
        smallest_dist = math.inf
        current_lingot = lingots[0]
        for lingot in lingots:
            dist = self.euclidian_distance(character.position, lingot.position)
            if dist < smallest_dist:
                smallest_dist = dist
                current_lingot = lingot

        return current_lingot

    def action(self, character: Character, state: TeamGameState) -> Action:
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
                        self.drop_destination = random.choice(
                            drop_cells)

                return DropAction(characterId=character.id)
            else:
                return MoveToAction(characterId=character.id, position=self.drop_destination)

        if character.numberOfCarriedItems == state.constants.maxNumberOfItemsCarriedPerCharacter:
            # return to base
            self.drop_destination = random.choice(
                self.find_drop_cells(self.base, state))
            return MoveToAction(characterId=character.id, position=self.drop_destination)

        lingots = []
        for item in state.items:
            if item.value > 0 and item not in character.carriedItems and item.position not in self.base:
                lingots.append(item)
        if lingots == []:
            # todo: change Role to protecter
            # right now we just go to base
            move_to = random.choice(self.base)
            return MoveToAction(characterId=character.id, position=move_to)

        move_to = self.closest_lingot(character, lingots).position

        if character.position == move_to:
            action = GrabAction(characterId=character.id)
        else:
            action = MoveToAction(characterId=character.id, position=move_to)

        return action


class Protecter(Role):
    def action(self, character: Character, state: TeamGameState):
        intruders = self.find_intruders(state)
        if intruders == []:
            move_to = random.choice(self.base)
            return MoveToAction(characterId=character.id, position=move_to)
        else:
            move_to = self.closest_intruders(intruders, character).position
            return MoveToAction(characterId=character.id, position=move_to)

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
    def __init__(self, game_message, character_id):
        self.game_message = game_message
        self.character_id = character_id
        self.radiant_items_on_my_side = []
        self.enemy_base_positions = []
        self.radiant_object_reached = False

    def calculate_enemy_base(self, state: TeamGameState) -> list[Position]:
        enemy_base = []
        for x, col in enumerate(state.teamZoneGrid):
            for y, row in enumerate(col):
                if row != state.currentTeamId and state.map.tiles[x][y] == TileType.EMPTY:
                    enemy_base.append(Position(x, y))
        return enemy_base

    def collect_data(self):
        radiant_type = ["radiant_slag", "radiant_core"]
        radiant_items = [i for i in self.game_message.items if i.type in radiant_type]
        self.radiant_items_on_my_side = get_items_on_my_side(
            radiant_items, self.game_message.currentTeamId, self.game_message
        )
        self.enemy_base_positions = self.calculate_enemy_base(self.game_message)

    def make_move(self, character: Character, state: TeamGameState) -> Action:
        if not self.radiant_items_on_my_side:
            return None  # No action if no items on your side
        
        target_item = self.radiant_items_on_my_side[0]

        if character.position == target_item.position:
            return GrabAction(characterId=self.character_id)

        if character.numberOfCarriedItems < state.constants.maxNumberOfItemsCarriedPerCharacter:
            return MoveToAction(characterId=self.character_id, position=target_item.position)

        closest_enemy_tile = self.get_closest_enemy_tile(character)
        if closest_enemy_tile and character.position == closest_enemy_tile:
            return DropAction(characterId=self.character_id)

        return MoveToAction(characterId=self.character_id, position=closest_enemy_tile)

    def get_closest_enemy_tile(self, character: Character) -> Position:
        closest_tile = min(
            self.enemy_base_positions,
            key=lambda tile: self.euclidian_distance(character.position, tile),
            default=None
        )
        return closest_tile

    def action(self, character: Character, state: TeamGameState) -> Action:
        self.collect_data()
        return self.make_move(character, state)


class Enemy(Role):

    def action(self):
        pass


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

    def dispatch(self, character: Character, yourCharacters: list[Character]) -> Role:
        """Role dispatching algorithm"""
        if len(yourCharacters) <= 2:
            return Collecter(self.base)

        else:
            return Collecter(self.base)

    def get_next_move(self, game_message: TeamGameState):
        """
        Here is where the magic happens, for now the moves are not very good. I bet you can do better ;)
        """
        actions = []

        for character in game_message.yourCharacters:
            # initialize characters at first tick
            if game_message.tick == 1:
                self.base = self.find_base(game_message)
                self.character_roles[character.id] = self.dispatch(
                    character, game_message.yourCharacters)

            character_role = self.character_roles[character.id]
            actions.append(character_role.action(
                character, game_message))

        # You can clearly do better than the random actions above! Have fun!
        return actions
