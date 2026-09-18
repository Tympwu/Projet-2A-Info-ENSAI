import requests

from business_object.game import Game
from service.player_service import PlayerService


class GameClient:
    def get_games(self) -> list[Game]:
        # Interrogation de l'API
        r = requests.get(url="http://localhost:5555/")
        # Vérification que la demande a bien réussie
        if r.status_code != 200:
            raise Exception(f"Cannot reach (HTTP {r.status_code}): {r.text}")
        else:
            r_python = r.json()

        # Conversion en list[Game]
        result = []
        list_player = PlayerService().find_all()
        for element in r_python:
            for player in list_player:
                if player.username == element["players_list"][0]:
                    p1 = player
                elif player.username == element["players_list"][1]:
                    p2 = player
            result.append(
                Game(
                    player1=p1,
                    player2=p2,
                    game_mode=element["mode_type"],
                    winner=p1 if p1.username == element["winner_name"] else p2,
                    description=element["details"],
                    timestamp=element["duration_seconds"],
                    id_game=element["id"],
                )
            )
        return result
