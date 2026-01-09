import subprocess
from pathlib import Path
import re


def extract_package_name(whl_filename):
    """
    Extract package name from wheel filename.
    Example: algomancy_utils-0.1.0-py3-none-any.whl -> algomancy-utils
    """
    # Wheel filenames follow the pattern: {distribution}-{version}(-{build})?-{python}-{abi}-{platform}.whl
    # We want the distribution name, normalized to use hyphens
    match = re.match(r"^(.+?)-\d+", whl_filename)
    if match:
        package_name = match.group(1)
        # Replace underscores with hyphens (standard package naming)
        return package_name.replace("_", "-")
    return None


def get_wheel_files(dist_dir="dist"):
    """Get all .whl files from the dist directory."""
    dist_path = Path(dist_dir)
    if not dist_path.exists():
        print(f"Error: '{dist_dir}' directory not found!")
        return []

    whl_files = list(dist_path.glob("*.whl"))
    return whl_files


def remove_package(package_name):
    """Remove a package using uv remove."""
    print(f"  Removing {package_name}...", end=" ")
    result = subprocess.run(
        ["uv", "remove", package_name], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✓")
        return True
    else:
        print("⚠ (might not be installed)")
        return False


def add_package(package_name, whl_path):
    """Add a package from a local .whl file using uv add."""
    print(f"  Adding {package_name}...", end=" ")
    result = subprocess.run(
        ["uv", "add", str(whl_path)], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✓")
        return True
    else:
        print("✗")
        print(f"    Error: {result.stderr.strip()}")
        return False


def sort_packages_by_dependency_order(packages):
    """
    Sort packages according to dependency order.
    Order: utils -> data -> gui -> scenario -> cli -> content -> algomancy
    """
    # Define the desired order
    order = [
        "algomancy-utils",
        "algomancy-data",
        "algomancy-gui",
        "algomancy-scenario",
        "algomancy-cli",
        "algomancy-content",
        "algomancy",
    ]

    # Create a mapping for sorting
    order_map = {pkg: idx for idx, pkg in enumerate(order)}

    # Sort packages based on the order map, putting unknowns at the end
    sorted_packages = sorted(packages, key=lambda x: order_map.get(x[0], len(order)))

    return sorted_packages


def main():
    print("=" * 60)
    print("Automated Algomancy Package Reinstallation")
    print("=" * 60)
    print()

    # ========== PHASE 1: SCAN ==========
    print("PHASE 1: SCANNING dist/ folder")
    print("-" * 60)

    whl_files = get_wheel_files()

    if not whl_files:
        print("No .whl files found in dist/ directory!")
        return

    packages = []
    for whl_file in whl_files:
        package_name = extract_package_name(whl_file.name)
        if package_name == "algomancy-installer":
            continue
        if package_name:
            packages.append((package_name, whl_file))
            print(f"  ✓ Found: {whl_file.name} -> {package_name}")

    print(f"\nTotal packages found: {len(packages)}")

    # Sort packages by dependency order
    packages = sort_packages_by_dependency_order(packages)

    # ========== PHASE 2: REMOVE ==========
    print("\n" + "=" * 60)
    print("PHASE 2: REMOVING existing packages")
    print("-" * 60)

    removed_count = 0
    for package_name, _ in packages:
        if remove_package(package_name):
            removed_count += 1

    print(f"\nPackages removed: {removed_count}/{len(packages)}")

    # ========== PHASE 3: ADD ==========
    print("\n" + "=" * 60)
    print("PHASE 3: ADDING packages in dependency order")
    print("-" * 60)
    print(
        "Installation order: utils → data → gui → scenario → cli → content → algomancy"
    )
    print()

    success_count = 0
    fail_count = 0

    for idx, (package_name, whl_path) in enumerate(packages, 1):
        print(f"[{idx}/{len(packages)}] {package_name}")
        if add_package(package_name, whl_path):
            success_count += 1
        else:
            fail_count += 1
        print()

    # ========== SUMMARY ==========
    print("=" * 60)
    print("INSTALLATION SUMMARY")
    print("=" * 60)
    print(f"✓ Successfully installed: {success_count}")
    print(f"✗ Failed: {fail_count}")
    print("=" * 60)

    if fail_count == 0:
        print("\n All packages reinstalled successfully!")
    else:
        print("\n⚠ Some packages failed to install. Check errors above.")


if __name__ == "__main__":
    main()
