import random
import math
from game_message import *


class Bot:
    def __init__(self):
        self.charecter_roles = {}
        print("Initializing your super mega duper bot")

    def find_base(self, state: TeamGameState) -> list[Position]:
        base = []
        for x, col in enumerate(state.teamZoneGrid):
            for y, row in enumerate(col):
                if row == state.currentTeamId and state.map.tiles[x][y] == TileType.EMPTY:
                    base.append(Position(x, y))

        return base

    def get_next_move(self, game_message: TeamGameState):
        """
        Here is where the magic happens, for now the moves are not very good. I bet you can do better ;)
        """
        actions = []

        for character in game_message.yourCharacters:
            # initialize characters at first tick
            if game_message.tick == 1:
                self.base = self.find_base(game_message)
                self.charecter_roles[character.id] = Collecter()

            character_role = self.charecter_roles[character.id]
            actions.append(character_role.action(
                character, self.base, game_message))

        # You can clearly do better than the random actions above! Have fun!
        return actions


class Role:

    def action(self, character: Character, state: TeamGameState) -> Action:
        pass

    def euclidian_distance(self, p1: Position, p2: Position):
        return math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2)


class Collecter(Role):
    def __init__(self):
        self.is_returning_to_base = False
        self.destination = None

    def closest_lingot(self, character: Character, lingots: list[Item]) -> Item:
        smallest_dist = math.inf
        current_lingot = lingots[0]
        for lingot in lingots:
            dist = self.euclidian_distance(character.position, lingot.position)
            if dist < smallest_dist:
                smallest_dist = dist
                current_lingot = lingot

        return current_lingot

    def action(self, character: Character, base: list[Position], state: TeamGameState) -> Action:
        if character.numberOfCarriedItems == state.constants.maxNumberOfItemsCarriedPerCharacter:  # return to base
            move_to = random.choice(base)
            if character.position == move_to:
                return DropAction(characterId=character.id)
            return MoveToAction(characterId=character.id, position=move_to)

        lingots = []
        for item in state.items:
            if item.value > 0 and item.position:
                lingots.append(item)

        move_to = self.closest_lingot(character, lingots).position

        if character.position == move_to:
            action = GrabAction(characterId=character.id)
        else:
            action = MoveToAction(characterId=character.id, position=move_to)

        return action


class Dumper(Role):
    def action(self):
        pass


class Enemy(Role):

    def action(self):
        pass
