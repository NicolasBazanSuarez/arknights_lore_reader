from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    enabled: bool
    folder_name: str
    selectable: bool = True


CATEGORIES = {
    "side": Category(
        False,
        "Side Story"
    ),

    "extra": Category(
        False,
        "Side Content",
        selectable=False
    ),

    "sandbox": Category(
        False,
        "Reclamation",
        selectable=False
    ),

    "mini": Category(
        False,
        "Vignettes"
    ),

    "main": Category(
        False,
        "Main Story"
    ),

    "rogue": Category(
        False,
        "Integrated Strategies"
    ),

    "operators": Category(
        False,
        "Operators"
    ),
}