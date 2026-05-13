"""30 秒超时询问;超时返回默认值并把问题写入 MORNING_TODO.md。"""
import datetime as dt
import select
import sys
from pathlib import Path

TODO_PATH = Path(__file__).resolve().parents[1] / "MORNING_TODO.md"


def ask(question: str, default: str, timeout: int = 30) -> str:
    print(f"\n[ASK {timeout}s] {question}\n[default if no answer]: {default!r}\n> ", end="", flush=True)
    r, _, _ = select.select([sys.stdin], [], [], timeout)
    if r:
        ans = sys.stdin.readline().strip()
        return ans or default
    _append_todo(question, default)
    print(f"\n[timeout] using default: {default!r}")
    return default


def _append_todo(question: str, used_default: str) -> None:
    ts = dt.datetime.now().isoformat(timespec="seconds")
    TODO_PATH.touch(exist_ok=True)
    with TODO_PATH.open("a", encoding="utf-8") as f:
        f.write(f"- [ ] {ts} — **{question}** (auto used: `{used_default}`)\n")


if __name__ == "__main__":
    print(ask("test question?", "yes", timeout=1))
