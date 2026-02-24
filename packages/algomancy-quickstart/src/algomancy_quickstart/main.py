import click
import sys
import os


def _ensure_dev_path():
    """Ensure the dev path is available for imports during development."""
    here = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from algomancy_quickstart.quickstart import run_quickstart  # noqa: F401

        return
    except Exception:
        pass


_ensure_dev_path()

from algomancy_quickstart.quickstart import run_quickstart  # type: ignore  # noqa: E402


@click.command()
@click.option(
    "--skip-confirmation",
    is_flag=True,
    help="Skip confirmation prompts and use defaults where possible.",
)
@click.option(
    "--title", default=None, help="Project title (will be prompted if not provided)."
)
def main(skip_confirmation: bool, title: str | None):
    """
    Algomancy Quickstart - Interactive setup wizard for Algomancy applications.

    This tool will guide you through creating a new Algomancy application with:
    - Folder structure
    - Basic main.py with placeholders
    - Custom implementation shells
    - ETL pipeline generation
    - Asset imports
    - Styling configuration
    """
    click.echo(click.style("🎯 Algomancy Quickstart Wizard", fg="cyan", bold=True))
    click.echo()

    try:
        run_quickstart(skip_confirmation=skip_confirmation, title=title)
    except KeyboardInterrupt:
        click.echo()
        click.echo(click.style("❌ Setup cancelled by user.", fg="red"))
        sys.exit(1)
    except Exception as e:
        click.echo()
        click.echo(click.style(f"❌ Error: {e}", fg="red"))
        sys.exit(1)


if __name__ == "__main__":
    main()
