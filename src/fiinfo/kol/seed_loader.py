import csv
from pathlib import Path

from fiinfo.models import Kol

SEED_PATH = Path(__file__).resolve().parents[3] / "seeds" / "kol_seed.csv"


def load_seed_kols(path: Path | None = None) -> list[Kol]:
    p = path or SEED_PATH
    out: list[Kol] = []
    with p.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.append(
                Kol(
                    handle=row["handle"],
                    display_name=row["display_name"],
                    followers=int(row["followers"]),
                    category=row["category"],
                )
            )
    return out
