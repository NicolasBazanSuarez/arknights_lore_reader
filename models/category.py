from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    enabled: bool
    folder_name: str


CATEGORIES = {
    "side": Category(False, "Side Story"),
    "extra": Category(False, "Side Content"),
    "sandbox": Category(False, "Reclamation"),
    "mini": Category(False, "Vignettes"),
    "main": Category(True, "Main Story"),
    "rogue": Category(False, "Integrated Strategies"),
}