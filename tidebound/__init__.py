__all__ = ["Game"]


def __getattr__(name):
    if name == "Game":
        from .game import Game
        return Game
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
