#!/usr/bin/env python3
"""
Script to bump version across all packages in the Algomancy workspace.
Usage: uv run algomancy-version-bump --major|--minor|--patch
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
import tomllib


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Bump version for Algomancy and all its packages"
    )

    # Create mutually exclusive group for version bump type
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--major", action="store_true", help="Bump major version")
    group.add_argument("--minor", action="store_true", help="Bump minor version")
    group.add_argument("--patch", action="store_true", help="Bump patch version")

    return parser.parse_args()


def get_bump_type(args):
    """Determine which version component to bump."""
    if args.major:
        return "major"
    elif args.minor:
        return "minor"
    elif args.patch:
        return "patch"


def get_version_from_pyproject(pyproject_path: Path) -> str:
    """Extract version from pyproject.toml file."""
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def get_workspace_package_names(pyproject_path: Path) -> list[str]:
    """Extract workspace package names from root pyproject.toml."""
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    # Get package names from workspace members
    workspace_members = (
        data.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", [])
    )
    package_names = []

    for member in workspace_members:
        # Extract package name from path like "packages/algomancy-content"
        package_name = member.split("/")[-1]
        package_names.append(package_name)

    return package_names


def bump_root_version(bump_type: str) -> str:
    """Bump the root package version and return the new version."""
    print(f"Bumping root package version ({bump_type})...")

    try:
        result = subprocess.run(
            ["uv", "version", "--bump", bump_type],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout.strip())

        # Get the new version from root pyproject.toml
        root_pyproject = Path("pyproject.toml")
        new_version = get_version_from_pyproject(root_pyproject)
        print(f"New root version: {new_version}")

        return new_version
    except subprocess.CalledProcessError as e:
        print(f"Error bumping root version: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def update_package_version(package_path: Path, new_version: str):
    """Update a package's pyproject.toml with the new version."""
    pyproject_path = package_path / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"Warning: {pyproject_path} not found, skipping...")
        return

    print(f"Updating {package_path.name} to version {new_version}...")

    try:
        # Read the file
        with open(pyproject_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Update the version line
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith("version ="):
                lines[i] = f'version = "{new_version}"\n'
                updated = True
                break

        if not updated:
            print(f"Warning: Could not find version line in {pyproject_path}")
            return

        # Write back
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"✓ Updated {package_path.name}")

    except Exception as e:
        print(f"Error updating {package_path}: {e}", file=sys.stderr)
        sys.exit(1)


def update_root_dependencies(new_version: str, package_names: list[str]):
    """Update dependency versions in the root pyproject.toml."""
    root_pyproject = Path("pyproject.toml")

    print(f"Updating root package dependencies to >= {new_version}...")

    try:
        # Read the file
        with open(root_pyproject, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Pattern to match dependency lines for workspace packages
        # Matches lines like: "algomancy-cli >= 0.1.2",
        dependency_pattern = re.compile(
            r'^(\s*)"('
            + "|".join(re.escape(name) for name in package_names)
            + r')\s*>=?\s*[\d.]+"\s*,?\s*$'
        )

        updated_count = 0
        for i, line in enumerate(lines):
            match = dependency_pattern.match(line)
            if match:
                indent = match.group(1)
                package_name = match.group(2)
                # Preserve trailing comma if present
                has_comma = line.rstrip().endswith(",")
                lines[i] = (
                    f'{indent}"{package_name} >= {new_version}"{"," if has_comma else ""}\n'
                )
                updated_count += 1
                print(f"  ✓ Updated {package_name} dependency")

        if updated_count == 0:
            print("  Warning: No workspace package dependencies found to update")

        # Write back
        with open(root_pyproject, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"✓ Updated {updated_count} dependencies in root pyproject.toml")

    except Exception as e:
        print(f"Error updating root dependencies: {e}", file=sys.stderr)
        sys.exit(1)


def update_lockfile():
    try:
        _ = subprocess.run(
            ["uv", "lock"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✓ Updated lockfile")
    except Exception as e:
        print(f"Error updating lockfile: {e}", file=sys.stderr)


def main():
    """Main entry point."""
    args = parse_args()
    bump_type = get_bump_type(args)

    print(f"Starting version bump: {bump_type}")
    print("=" * 50)

    # Get workspace package names before bumping
    root_pyproject = Path("pyproject.toml")
    package_names = get_workspace_package_names(root_pyproject)
    print(f"Found workspace packages: {', '.join(package_names)}\n")

    # Bump root package version
    new_version = bump_root_version(bump_type)

    print("\n" + "=" * 50)
    print("Updating workspace packages...")
    print("=" * 50)

    # Update all packages in the workspace
    packages_dir = Path("packages")

    if not packages_dir.exists():
        print("Error: packages directory not found", file=sys.stderr)
        sys.exit(1)

    # Find all package directories
    package_dirs = [
        d for d in packages_dir.iterdir() if d.is_dir() and not d.name.startswith("__")
    ]

    for package_dir in sorted(package_dirs):
        update_package_version(package_dir, new_version)

    print("\n" + "=" * 50)
    print("Updating root dependencies...")
    print("=" * 50)

    # Update dependency versions in root pyproject.toml
    update_root_dependencies(new_version, package_names)

    print("\n" + "=" * 50)
    print("Updating lock file...")
    print("=" * 50)

    # Update lock file
    update_lockfile()

    print("\n" + "=" * 50)
    print(f"✓ Version bump complete! All packages now at version {new_version}")
    print("=" * 50)


if __name__ == "__main__":
    main()
