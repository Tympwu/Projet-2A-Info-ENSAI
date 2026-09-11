# uv run --project backend python backend/src/sandbox.py
from time import time

from business_object.game import Game
from business_object.player import Player
from dao.game_dao import GameDao
from dao.player_dao import PlayerDao
from utils.env_variables import load_environment_variables

load_environment_variables()  # Required to load the variables needed (env) to connect to the database

p1 = Player(username="kilian", elo=2000, email="a.a@a.com")
p2 = Player(username="god", elo=3000, email="a.a@god.com")
PlayerDao().create(p1)
PlayerDao().create(p2)
game = Game(p1, p2, game_mode="coin_flip", description="An epic battle", winner=p1, timestamp=time)

id = GameDao().create(game)
print(id)
game2 = GameDao().find_by_id(game.id_game)


"""
from service.game_service import GameService
from utils.env_variables import display_values, load_environment_variables
from utils.log_utils import initialize_logs

# Initialization
initialize_logs("Webservice")

load_environment_variables()
display_values()


g = GameService().play(3, 5, "coinflip", choice="tails")
print(g)

print(f"{g.player1.username} : new elo -> {g.player1.elo}")
print(f"{g.player2.username} : new elo -> {g.player2.elo}")

g2 = GameService().play(3, 5, "dice")
print(g2)

print(f"{g2.player1.username} : new elo -> {g2.player1.elo}")
print(f"{g2.player2.username} : new elo -> {g2.player2.elo}")
"""
