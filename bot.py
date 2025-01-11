import random
from game_message import *


class Bot:
    def __init__(self):
        print("Initializing your super mega duper bot")


    def get_next_move(self, game_message: TeamGameState):
        """
        Here is where the magic happens, for now the moves are not very good. I bet you can do better ;)
        """
        actions = []

        print(game_message.map)
        print("items",game_message.items,"\n")
        

        
        return actions



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
