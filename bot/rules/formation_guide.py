from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class FormationPreset:
    generation: int | str  # 1 to 12, or "Extreme"
    name: str             # e.g. "Full Offensive", "Hybrid", "Full Defensive", "Semi Offensive", "Super Defensive", "Defense Breaker"
    place: str            # e.g. "Player City, Sunfire", "Fortress, Facility, Sunfire", "Tyrant capital", "Anywhere"
    infantry: float
    lancers: float
    marksman: float
    callers: dict[str, str]       # {"infantry": "Jeronimo", "lancer": "Molly", "marksman": "Zinman"}
    joiners: list[str]            # 4 recommended joiners, e.g. ["Jessie", "Seoyoon", "Jasser", "Jessie"]
    notes: str = ""

    def ratio_dict(self) -> dict[str, float]:
        return {
            "infantry": self.infantry,
            "lancers": self.lancers,
            "marksman": self.marksman,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "name": self.name,
            "place": self.place,
            "ratio": self.ratio_dict(),
            "ratio_str": f"{int(self.infantry)}/{int(self.lancers)}/{int(self.marksman)}",
            "callers": self.callers,
            "joiners": self.joiners,
            "notes": self.notes,
        }


# King Shield Ultimate Formation Guide (Generations 1 to 12 + Extreme Defense)
FORMATION_GUIDE_PRESETS: list[FormationPreset] = [
    # Generation 1
    FormationPreset(
        generation=1,
        name="Full Offensive",
        place="Player City",
        infantry=30, lancers=20, marksman=50,
        callers={"infantry": "Jeronimo", "lancer": "Molly", "marksman": "Zinman"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Jessie"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=1,
        name="Hybrid",
        place="Fortress, Facility",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Natalia", "lancer": "Molly", "marksman": "Zinman"},
        joiners=["Jessie", "Seoyoon", "Patrick", "Sergey"],
        notes="No Diminishing effect",
    ),
    FormationPreset(
        generation=1,
        name="Full Defensive",
        place="Anywhere",
        infantry=60, lancers=20, marksman=20,
        callers={"infantry": "Jeronimo", "lancer": "Molly", "marksman": "Zinman"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Patrick"],
        notes="Patrick will give Diminishing effect",
    ),

    # Generation 2
    FormationPreset(
        generation=2,
        name="Full Offensive",
        place="Player City",
        infantry=40, lancers=20, marksman=40,
        callers={"infantry": "Jeronimo", "lancer": "Molly", "marksman": "Alonso"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Jessie"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=2,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Natalia", "lancer": "Philly", "marksman": "Alonso"},
        joiners=["Jessie", "Seoyoon", "Patrick", "Sergey"],
        notes="No Diminishing effect",
    ),
    FormationPreset(
        generation=2,
        name="Full Defensive",
        place="Anywhere",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Flint", "lancer": "Philly", "marksman": "Zinman"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Patrick"],
        notes="Patrick will give Diminishing effect",
    ),

    # Generation 3
    FormationPreset(
        generation=3,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Alonso"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Jessie"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=3,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Natalia", "lancer": "Philly", "marksman": "Greg"},
        joiners=["Jessie", "Seoyoon", "Patrick", "Sergey"],
        notes="No Diminishing effect",
    ),
    FormationPreset(
        generation=3,
        name="Full Defensive",
        place="Anywhere",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Logan", "lancer": "Philly", "marksman": "Greg"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Patrick"],
        notes="Patrick will give Diminishing effect",
    ),

    # Generation 4
    FormationPreset(
        generation=4,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Alonso"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Jessie"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=4,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Natalia", "lancer": "Philly", "marksman": "Lynn"},
        joiners=["Jessie", "Seoyoon", "Patrick", "Sergey"],
        notes="No Diminishing effect",
    ),
    FormationPreset(
        generation=4,
        name="Full Defensive",
        place="Anywhere",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Ahmose", "lancer": "Philly", "marksman": "Greg"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Patrick"],
        notes="Patrick will give Diminishing effect",
    ),
    FormationPreset(
        generation=4,
        name="Semi Offensive",
        place="Player City",
        infantry=30, lancers=20, marksman=50,
        callers={"infantry": "Hector", "lancer": "Reina", "marksman": "Greg"},
        joiners=["Jessie", "Seoyoon", "Alonso", "Jessie"],
        notes="Chance base skills",
    ),

    # Generation 5
    FormationPreset(
        generation=5,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Lynn"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Norah"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=5,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Hector", "lancer": "Norah", "marksman": "Lynn"},
        joiners=["Norah", "Sergey", "Jessie", "Patrick"],
        notes="Norah will give Diminishing effect",
    ),
    FormationPreset(
        generation=5,
        name="Full Defensive",
        place="Anywhere",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Hector", "lancer": "Norah", "marksman": "Greg/Zinman"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Patrick"],
        notes="Patrick will give Diminishing effect",
    ),
    FormationPreset(
        generation=5,
        name="Semi Offensive",
        place="Player City",
        infantry=30, lancers=40, marksman=30,
        callers={"infantry": "Hector", "lancer": "Reina", "marksman": "Gwen"},
        joiners=["Jessie", "Seoyoon", "Alonso", "Norah"],
        notes="Chance base skills",
    ),

    # Generation 6
    FormationPreset(
        generation=6,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Gwen"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Norah"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=6,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Wu Ming", "lancer": "Norah", "marksman": "Wayne"},
        joiners=["Norah", "Sergey", "Jessie", "Patrick"],
        notes="Norah will give Diminishing effect",
    ),
    FormationPreset(
        generation=6,
        name="Full Defensive",
        place="Anywhere",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Wu Ming", "lancer": "Norah", "marksman": "Wayne"},
        joiners=["Patrick", "Sergey", "Patrick", "Renee"],
        notes="Patrick will give Diminishing effect",
    ),
    FormationPreset(
        generation=6,
        name="Semi Offensive",
        place="Player City",
        infantry=40, lancers=10, marksman=50,
        callers={"infantry": "Hector", "lancer": "Renee", "marksman": "Wayne"},
        joiners=["Jessie", "Seoyoon", "Alonso", "Norah"],
        notes="Chance base skills",
    ),

    # Generation 7
    FormationPreset(
        generation=7,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Gwen"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Norah"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=7,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Edith", "lancer": "Gordon", "marksman": "Wayne"},
        joiners=["Norah", "Sergey", "Edith", "Edith"],
        notes="Norah and Edith will give Diminishing effect",
    ),
    FormationPreset(
        generation=7,
        name="Semi Defensive",
        place="Anywhere",
        infantry=70, lancers=10, marksman=20,
        callers={"infantry": "Edith", "lancer": "Gordon", "marksman": "Bradley"},
        joiners=["Norah", "Sergey", "Patrick", "Edith"],
        notes="No diminishing effect",
    ),
    FormationPreset(
        generation=7,
        name="Semi Offensive",
        place="Tyrant capital",
        infantry=40, lancers=60, marksman=0,
        callers={"infantry": "Edith", "lancer": "Gordon", "marksman": "Bradley"},
        joiners=["Jessie", "Jessie", "Alonso", "Edith"],
        notes="Chance base skills + Diminishing effect",
    ),
    FormationPreset(
        generation=7,
        name="Super Defensive",
        place="Tyrant capital",
        infantry=40, lancers=0, marksman=60,
        callers={"infantry": "Edith", "lancer": "Philly", "marksman": "Bradley"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Norah"],
        notes="Weak against 60-40-0 rally, can stop 49-2-49",
    ),
    FormationPreset(
        generation=7,
        name="Defense Breaker",
        place="Tyrant capital or Sunfire",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Jeronimo", "lancer": "Gordon", "marksman": "Bradley"},
        joiners=["Jessie", "Jessie", "Seoyoon", "Seoyoon"],
        notes="Useful only against 40-0-60, other place useless",
    ),

    # Generation 8
    FormationPreset(
        generation=8,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Bradley"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Norah"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=8,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Edith", "lancer": "Gordon", "marksman": "Bradley"},
        joiners=["Norah", "Sergey", "Edith", "Philly"],
        notes="Norah and Edith will give Diminishing effect",
    ),
    FormationPreset(
        generation=8,
        name="Semi Defensive",
        place="Anywhere",
        infantry=70, lancers=10, marksman=20,
        callers={"infantry": "Gatot", "lancer": "Sonya", "marksman": "Bradley"},
        joiners=["Norah", "Sergey", "Patrick", "Edith"],
        notes="No diminishing effect",
    ),
    FormationPreset(
        generation=8,
        name="Semi Offensive",
        place="Tyrant capital",
        infantry=40, lancers=0, marksman=60,
        callers={"infantry": "Gatot", "lancer": "Gordon", "marksman": "Hendrik"},
        joiners=["Jessie", "Jessie", "Alonso", "Norah"],
        notes="Chance base skills + Diminishing effect",
    ),
    FormationPreset(
        generation=8,
        name="Super Defensive",
        place="Tyrant capital",
        infantry=40, lancers=0, marksman=60,
        callers={"infantry": "Gatot", "lancer": "Philly", "marksman": "Bradley"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Edith"],
        notes="Weak against 60-40-0 rally, can stop 49-2-49",
    ),
    FormationPreset(
        generation=8,
        name="Defense Breaker",
        place="Tyrant capital",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Jeronimo", "lancer": "Gordon", "marksman": "Hendrik"},
        joiners=["Jessie", "Jessie", "Seoyoon", "Seoyoon"],
        notes="Useful only against 40-0-60, other place useless",
    ),

    # Generation 9
    FormationPreset(
        generation=9,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Bradley"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Norah"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=9,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Magnus", "lancer": "Gordon", "marksman": "Xura"},
        joiners=["Norah", "Sergey", "Edith", "Philly"],
        notes="No Diminishing effect",
    ),
    FormationPreset(
        generation=9,
        name="Semi Defensive",
        place="Anywhere",
        infantry=70, lancers=10, marksman=20,
        callers={"infantry": "Gatot", "lancer": "Sonya", "marksman": "Xura"},
        joiners=["Norah", "Sergey", "Patrick", "Edith"],
        notes="No diminishing effect",
    ),
    FormationPreset(
        generation=9,
        name="Semi Offensive",
        place="Tyrant capital",
        infantry=40, lancers=60, marksman=0,
        callers={"infantry": "Magnus", "lancer": "Fred", "marksman": "Hendrik"},
        joiners=["Jessie", "Jessie", "Alonso", "Edith"],
        notes="Chance base skills + Diminishing effect",
    ),
    FormationPreset(
        generation=9,
        name="Super Defensive",
        place="Tyrant capital",
        infantry=40, lancers=0, marksman=60,
        callers={"infantry": "Gatot", "lancer": "Sonya", "marksman": "Hendrik"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Norah"],
        notes="Weak against 60-40-0 rally, can stop 49-2-49",
    ),
    FormationPreset(
        generation=9,
        name="Defense Breaker",
        place="Tyrant capital or Sunfire",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Jeronimo", "lancer": "Fred", "marksman": "Hendrik"},
        joiners=["Jessie", "Jessie", "Seoyoon", "Seoyoon"],
        notes="Useful only against 40-0-60, other place useless",
    ),

    # Generation 10
    FormationPreset(
        generation=10,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Blanchette"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Norah"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=10,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Gregory", "lancer": "Freya", "marksman": "Blanchette"},
        joiners=["Norah", "Edith", "Edith", "Philly"],
        notes="Edith will give Diminishing effect",
    ),
    FormationPreset(
        generation=10,
        name="Semi Defensive",
        place="Anywhere",
        infantry=70, lancers=10, marksman=20,
        callers={"infantry": "Gregory", "lancer": "Freya", "marksman": "Xura"},
        joiners=["Norah", "Sergey", "Patrick", "Edith"],
        notes="No diminishing effect",
    ),
    FormationPreset(
        generation=10,
        name="Semi Offensive",
        place="Tyrant capital",
        infantry=40, lancers=60, marksman=0,
        callers={"infantry": "Gregory", "lancer": "Fred", "marksman": "Blanchette"},
        joiners=["Jessie", "Seoyoon", "Hendrik", "Edith"],
        notes="Chance base skills",
    ),
    FormationPreset(
        generation=10,
        name="Super Defensive",
        place="Tyrant capital",
        infantry=40, lancers=0, marksman=60,
        callers={"infantry": "Gregory", "lancer": "Freya", "marksman": "Xura"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Norah"],
        notes="Weak against 60-40-0 rally, can stop 49-2-49",
    ),
    FormationPreset(
        generation=10,
        name="Defense Breaker",
        place="Tyrant capital or Sunfire",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Gregory", "lancer": "Fred", "marksman": "Blanchette"},
        joiners=["Jessie", "Blanchette", "Seoyoon", "Hendrik"],
        notes="Useful only against 40-0-60, other place useless",
    ),

    # Generation 11
    FormationPreset(
        generation=11,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Rufus"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Norah"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=11,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Eleonora", "lancer": "Lloyd", "marksman": "Rufus"},
        joiners=["Norah", "Norah", "Edith", "Edith"],
        notes="Norah and Edith will give Diminishing effect",
    ),
    FormationPreset(
        generation=11,
        name="Semi Defensive",
        place="Anywhere",
        infantry=70, lancers=10, marksman=20,
        callers={"infantry": "Eleonora", "lancer": "Lloyd", "marksman": "Rufus"},
        joiners=["Norah", "Sergey", "Patrick", "Edith"],
        notes="No diminishing effect",
    ),
    FormationPreset(
        generation=11,
        name="Semi Offensive",
        place="Tyrant capital",
        infantry=40, lancers=60, marksman=0,
        callers={"infantry": "Eleonora", "lancer": "Lloyd", "marksman": "Rufus"},
        joiners=["Jessie", "Seoyoon", "Hendrik", "Edith"],
        notes="Chance base skills",
    ),
    FormationPreset(
        generation=11,
        name="Super Defensive",
        place="Tyrant capital",
        infantry=40, lancers=0, marksman=60,
        callers={"infantry": "Eleonora", "lancer": "Lloyd", "marksman": "Rufus"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Norah"],
        notes="Weak against 60-40-0 rally, can stop 49-2-49",
    ),
    FormationPreset(
        generation=11,
        name="Defense Breaker",
        place="Tyrant capital or Sunfire",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Eleonora", "lancer": "Lloyd", "marksman": "Rufus"},
        joiners=["Jessie", "Blanchette", "Seoyoon", "Hendrik"],
        notes="Useful only against 40-0-60, other place useless",
    ),

    # Generation 12
    FormationPreset(
        generation=12,
        name="Full Offensive",
        place="Player City, Sunfire",
        infantry=49, lancers=2, marksman=49,
        callers={"infantry": "Jeronimo", "lancer": "Mia", "marksman": "Rufus"},
        joiners=["Jessie", "Seoyoon", "Jasser", "Norah"],
        notes="Jeronimo, Jessie, Jasser will give Diminishing effect",
    ),
    FormationPreset(
        generation=12,
        name="Hybrid",
        place="Fortress, Facility, Sunfire",
        infantry=50, lancers=20, marksman=30,
        callers={"infantry": "Hervor", "lancer": "Karol", "marksman": "Ligeia"},
        joiners=["Norah", "Norah", "Edith", "Edith"],
        notes="Norah and Edith will give Diminishing effect",
    ),
    FormationPreset(
        generation=12,
        name="Semi Defensive",
        place="Anywhere",
        infantry=70, lancers=10, marksman=20,
        callers={"infantry": "Hervor", "lancer": "Karol", "marksman": "Ligeia"},
        joiners=["Norah", "Sergey", "Patrick", "Edith"],
        notes="No diminishing effect",
    ),
    FormationPreset(
        generation=12,
        name="Semi Offensive",
        place="Tyrant capital",
        infantry=40, lancers=60, marksman=0,
        callers={"infantry": "Hervor", "lancer": "Karol", "marksman": "Rufus"},
        joiners=["Jessie", "Seoyoon", "Hendrik", "Edith"],
        notes="Chance base skills",
    ),
    FormationPreset(
        generation=12,
        name="Super Defensive",
        place="Tyrant capital",
        infantry=40, lancers=0, marksman=60,
        callers={"infantry": "Hervor", "lancer": "Karol", "marksman": "Ligeia"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Norah"],
        notes="Weak against 60-40-0 rally, can stop 49-2-49",
    ),
    FormationPreset(
        generation=12,
        name="Defense Breaker",
        place="Tyrant capital or Sunfire",
        infantry=60, lancers=40, marksman=0,
        callers={"infantry": "Hervor", "lancer": "Karol", "marksman": "Rufus"},
        joiners=["Jessie", "Blanchette", "Seoyoon", "Hendrik"],
        notes="Useful only against 40-0-60, other place useless",
    ),

    # Extreme Defense
    FormationPreset(
        generation="Extreme",
        name="Extreme Defense (Unbreakable)",
        place="Player City, Foundry",
        infantry=34, lancers=33, marksman=33,
        callers={"infantry": "Gatot", "lancer": "Wu Ming", "marksman": "Ahmose"},
        joiners=["Patrick", "Sergey", "Ling Xue", "Ahmose"],
        notes="Even AKB cannot break this defense. Multi-infantry frontline wall with Patrick/Ahmose.",
    ),
]


def list_generations() -> list[int | str]:
    gens = []
    for p in FORMATION_GUIDE_PRESETS:
        if p.generation not in gens:
            gens.append(p.generation)
    return gens


def get_presets_for_generation(gen: int | str) -> list[FormationPreset]:
    return [p for p in FORMATION_GUIDE_PRESETS if str(p.generation).lower() == str(gen).lower()]


def get_all_presets() -> list[FormationPreset]:
    return FORMATION_GUIDE_PRESETS
