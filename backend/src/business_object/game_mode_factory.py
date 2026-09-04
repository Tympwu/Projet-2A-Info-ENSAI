from business_object.game_mode.game_mode import GameMode
from business_object.game_mode.coin_flip_mode import CoinFlipMode
from business_object.game_mode.dice_mode import DiceMode


class GameModeFactory:

    @classmethod
    def get_mode(cls, game_mode: str) -> GameMode:
        if game_mode == "coinflip":
            return CoinFlipMode()

        if game_mode == "dice":
            return DiceMode()

        raise ValueError(f"Unsupported game mode: {game_mode}")