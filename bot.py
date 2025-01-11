import random
from game_message import *


class Bot:
    def __init__(self):
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


class Dumper():
    def __init__(self, game_message):
        self.game_message = game_message
        self.radiant_items_on_my_side = []
        # caracter id of the dumper
        self.character_id = None
        self.radiant_object_reached = False

    def collect_data(self):
        radiant_type = ["radiant_slag", "radiant_core"]
        radiant_items = []

        for i in self.game_message.items:
            if i.type in radiant_type:
                print("items radiant", i)
                radiant_items.append(i)

        #check if radiant items are on my side
        self.radiant_items_on_my_side = get_items_on_my_side(radiant_items, self.game_message.currentTeamId, self.game_message)

    def goto_radiant(self):

        self.game_message.actions.append(MoveToAction(characterId=self.character_id, target=self.radiant_items_on_my_side[0].position))
        
        # Check item reached
        if self.game_message.characters[self.character_id].position == self.radiant_items_on_my_side[0].position:
            self.radiant_object_reached = True

    def pick_up(self):
        self.game_message.actions.append(GrabAction(self.character_id))

    def goto_enemy(self):

        # get the map tiles
        self.game_message.map.tiles

    def dump(self):
        self.game_message.actions.append(DropAction(self.character_id))


# fonction that take a list of items and the team Id and return a list of items on the team side
def get_items_on_my_side(items, teamId, game_message):
    items_on_my_side = []

    for i in items:
        if game_message.teamZoneGrid[i.position.y][i.position.x] == game_message.currentTeamId:
            items_on_my_side.append(i)
        
    return items_on_my_side


class Collecter(Role):
    def __init__(self):
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

    def action(self, character: Character, base: list[Position], state: TeamGameState) -> Action:
        if self.drop_destination is not None:
            if character.position == self.drop_destination:
                # arrived to destination, drop item
                self.drop_destination = None
                return DropAction(characterId=character.id)
            else:
                return MoveToAction(characterId=character.id, position=self.drop_destination)

        if character.numberOfCarriedItems == state.constants.maxNumberOfItemsCarriedPerCharacter:
            # return to base
            self.drop_destination = random.choice(base)
            return MoveToAction(characterId=character.id, position=self.drop_destination)

        lingots = []
        for item in state.items:
            if item.value > 0 and item not in character.carriedItems and item.position not in base:
                lingots.append(item)

        move_to = self.closest_lingot(character, lingots).position

        if character.position == move_to:
            action = GrabAction(characterId=character.id)
        else:
            action = MoveToAction(characterId=character.id, position=move_to)

        return action


class Enemy(Role):

    def action(self):
        pass
