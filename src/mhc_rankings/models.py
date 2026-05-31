from dataclasses import dataclass, field

@dataclass
class TeamRecord:
    team: str
    rating: float = 0.0
    sos: float = 0.0
    w: int = 0
    l: int = 0
    t: int = 0
    gf: int = 0
    ga: int = 0
    rank_change: int = 0
    win_pct: float = field(init=False)
    gd: int = field(init=False)

    def __post_init__(self):
        total = self.w + self.l + self.t
        self.win_pct = (self.w + 0.5 * self.t) / total if total > 0 else 0.0
        self.gd = self.gf - self.ga
