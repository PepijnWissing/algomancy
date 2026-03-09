"""
Asset management utilities for downloading and copying default assets.
"""

import shutil
import tempfile
import zipfile
from pathlib import Path
import click
import requests


class AssetManager:
    """Manages downloading and installing default Algomancy assets."""

    # GitHub repository details
    GITHUB_REPO = "PepijnWissing/algomancy"
    GITHUB_BRANCH = "main"
    ASSETS_PATH = "example/assets"

    def __init__(self, target_dir: Path):
        """
        Initialize the asset manager.

        Args:
            target_dir: Target directory where assets should be installed.
        """
        self.target_dir = target_dir
        self.assets_dir = target_dir / "assets"

    def install_assets(self, skip_confirmation: bool = False) -> bool:
        """
        Install default assets, either from GitHub or bundled fallback.

        Args:
            skip_confirmation: If True, skip confirmation prompts.

        Returns:
            True if assets were installed successfully.
        """
        click.echo(
            click.style("📦 Step 4: Installing default assets", fg="blue", bold=True)
        )
        click.echo()

        # Check if assets directory already has files
        if self.assets_dir.exists() and list(self.assets_dir.iterdir()):
            click.echo(click.style("⚠️  Assets directory is not empty", fg="yellow"))

            existing_files = list(self.assets_dir.iterdir())
            click.echo(f"Found {len(existing_files)} existing item(s)")

            if not skip_confirmation:
                choice = click.prompt(
                    "What would you like to do?",
                    type=click.Choice(
                        ["merge", "skip", "overwrite"], case_sensitive=False
                    ),
                    default="merge",
                )

                if choice == "skip":
                    click.echo("Skipping asset installation.")
                    return False
                elif choice == "overwrite":
                    click.echo("Removing existing assets...")
                    shutil.rmtree(self.assets_dir)
                    self.assets_dir.mkdir(parents=True)
                # 'merge' continues without deletion

        # Ensure assets directory exists
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        # Try downloading from GitHub first
        click.echo("Attempting to download assets from GitHub...")
        if self._download_from_github():
            click.echo(click.style("  ✓ Assets downloaded successfully!", fg="green"))
            return True

        # Fallback to bundled assets
        click.echo()
        click.echo(
            click.style(
                "⚠️  Could not download from GitHub, using bundled assets", fg="yellow"
            )
        )

        if self._install_bundled_assets():
            click.echo(
                click.style("  ✓ Bundled assets installed successfully!", fg="green")
            )
            return True

        click.echo(click.style("  ❌ Failed to install assets", fg="red"))
        return False

    def _download_from_github(self) -> bool:
        """
        Download assets from GitHub repository.

        Returns:
            True if download was successful.
        """
        try:
            # Construct URL for downloading the repository archive
            url = f"https://github.com/{self.GITHUB_REPO}/archive/refs/heads/{self.GITHUB_BRANCH}.zip"

            click.echo(f"  Downloading from: {url}")

            # Download with timeout
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_path = temp_path / "repo.zip"

                # Save zip file
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                click.echo("  Extracting assets...")

                # Extract zip file
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_path)

                # Find the extracted repository folder
                extracted_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if not extracted_dirs:
                    return False

                repo_dir = extracted_dirs[0]
                source_assets = repo_dir / self.ASSETS_PATH

                if not source_assets.exists():
                    click.echo(
                        f"  ⚠️  Assets not found in repository at {self.ASSETS_PATH}"
                    )
                    return False

                # Copy assets to target directory
                self._copy_assets(source_assets, self.assets_dir)

            return True

        except requests.exceptions.RequestException as e:
            click.echo(f"  ⚠️  Network error: {e}")
            return False
        except Exception as e:
            click.echo(f"  ⚠️  Error downloading assets: {e}")
            return False

    def _install_bundled_assets(self) -> bool:
        """
        Install bundled fallback assets from the package.

        Returns:
            True if installation was successful.
        """
        try:
            # Get path to bundled assets within the package
            from importlib.resources import files

            package_assets = files("algomancy_quickstart").joinpath("templates/assets")

            if not package_assets.is_dir():
                click.echo("  ⚠️  Bundled assets not found in package")
                return False

            # Copy bundled assets
            self._copy_assets(Path(str(package_assets)), self.assets_dir)

            return True

        except Exception as e:
            click.echo(f"  ⚠️  Error installing bundled assets: {e}")
            return False

    def _copy_assets(self, source: Path, target: Path) -> None:
        """
        Copy assets from source to target directory.

        Args:
            source: Source directory containing assets.
            target: Target directory where assets should be copied.
        """
        for item in source.iterdir():
            target_item = target / item.name

            if item.is_file():
                shutil.copy2(item, target_item)
                click.echo(f"    • {item.name}")
            elif item.is_dir():
                if target_item.exists():
                    # Merge directories
                    self._copy_assets(item, target_item)
                else:
                    shutil.copytree(item, target_item)
                    click.echo(f"    • {item.name}/")
