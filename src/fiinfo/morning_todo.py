import datetime as dt
from pathlib import Path

DEFAULT_TODO = Path("MORNING_TODO.md")


def add(line: str, todo_path: Path = DEFAULT_TODO) -> None:
    ts = dt.datetime.now().isoformat(timespec="seconds")
    todo_path.touch(exist_ok=True)
    with todo_path.open("a", encoding="utf-8") as f:
        f.write(f"- [ ] {ts} — {line}\n")
