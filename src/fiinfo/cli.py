import logging

import click

from fiinfo.pipeline import run_daily


@click.group()
def cli():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@cli.command()
@click.option("--source", default=None, help="fixture | playwright (default: auto by env)")
@click.option("--live-publish", is_flag=True, help="实际发布到 Twitter(默认 dry-run)")
@click.option("--force-mock-llm", is_flag=True, help="强制使用 EchoSummarizer 不调用真实 LLM")
def daily(source: str | None, live_publish: bool, force_mock_llm: bool):
    """跑一遍每日流水线:采集 → 摘要 → 渲染 → 分发。"""
    r = run_daily(source_name=source, dry_run=not live_publish, force_mock_llm=force_mock_llm)
    click.echo(f"OK: {r}")


def main():
    cli()


if __name__ == "__main__":
    main()
