import os

from business_object.CoinFlipMode import CoinFlipMode
from business_object.DiceMode import DiceMode
from business_object.game_mode import GameMode


class GameModFactory:
    """
    Classe permettant de choisir et générer les différentes parties avec les bons modes
    """

    @classmethod
    def get_mode(cls, game_mode: str) -> GameMode:
        """
        Returns the corresponding GameMode object.
        Args:
            game_mode (str): The identifier of the game mode (e.g., 'coinflip', 'dice').
        Returns:
            GameMode: An instance of a class implementing GameMode.
        Raises:
            ValueError: If the requested game_mode is not supported.
        """
        assert game_mode in os.environ["GAME_SUPPORTED"], ValueError
        if game_mode == "coinflip":
            return CoinFlipMode()
        elif game_mode == "dice":
            return DiceMode()
        else:
            raise (ValueError, "How did you get there ?")
