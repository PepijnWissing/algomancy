import sys
import requests
from pathlib import Path
import tomli


ROOT_PYPROJECT = Path("pyproject.toml")


def load_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomli.load(f)


def read_name_and_version(pyproject_path: Path) -> tuple[str, str]:
    data = load_toml(pyproject_path)

    try:
        project = data["project"]
        return project["name"], project["version"]
    except KeyError:
        raise RuntimeError(
            f"Missing project.name or project.version in {pyproject_path}"
        )


def get_workspace_member_pyprojects(root_pyproject: Path) -> list[Path]:
    data = load_toml(root_pyproject)

    try:
        members = data["tool"]["uv"]["workspace"]["members"]
    except KeyError:
        return []

    return [Path(member) / "pyproject.toml" for member in members]


def pypi_versions(dist_name: str) -> set[str]:
    url = f"https://pypi.org/pypi/{dist_name}/json"
    r = requests.get(url)

    if r.status_code == 404:
        return set()

    r.raise_for_status()
    return set(r.json()["releases"].keys())


def main():
    if not ROOT_PYPROJECT.exists():
        print("❌ Root pyproject.toml not found")
        sys.exit(1)

    failed = False

    # 1. Root package (algomancy)
    packages = [ROOT_PYPROJECT]

    # 2. Workspace members
    packages.extend(get_workspace_member_pyprojects(ROOT_PYPROJECT))

    print(f"🔍 Checking {len(packages)} packages\n")

    for pyproject in packages:
        if not pyproject.exists():
            print(f"❌ {pyproject}: not found")
            failed = True
            continue

        name, version = read_name_and_version(pyproject)
        existing_versions = pypi_versions(name)

        location = "root" if pyproject == ROOT_PYPROJECT else pyproject.parent
        print(f"🔍 {name} ({location}): local version = {version}")

        if version in existing_versions:
            print(f"❌ {name}: version {version} already exists on PyPI\n")
            failed = True
        else:
            print(f"✅ {name}: version {version} is not on PyPI\n")

    if failed:
        print("One or more package versions already exist on PyPI.")
        sys.exit(1)

    print("🎉 All package versions (including root) are safe to publish.")


if __name__ == "__main__":
    main()
