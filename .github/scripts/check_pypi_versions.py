import sys
import requests
from pathlib import Path
import tomli


ROOT_PYPROJECT = Path("pyproject.toml")


def load_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomli.load(f)


def get_workspace_members(root_pyproject: Path) -> list[Path]:
    data = load_toml(root_pyproject)

    try:
        members = data["tool"]["uv"]["workspace"]["members"]
    except KeyError:
        raise RuntimeError(
            "No [tool.uv.workspace].members found in root pyproject.toml"
        )

    return [Path(member) for member in members]


def read_name_and_version(pyproject_path: Path) -> tuple[str, str]:
    data = load_toml(pyproject_path)

    try:
        project = data["project"]
        return project["name"], project["version"]
    except KeyError:
        raise RuntimeError(
            f"Missing project.name or project.version in {pyproject_path}"
        )


def pypi_versions(dist_name: str) -> set[str]:
    url = f"https://pypi.org/pypi/{dist_name}/json"
    r = requests.get(url)

    if r.status_code == 404:
        # Package not published yet
        return set()

    r.raise_for_status()
    return set(r.json()["releases"].keys())


def main():
    if not ROOT_PYPROJECT.exists():
        print("❌ Root pyproject.toml not found")
        sys.exit(1)

    members = get_workspace_members(ROOT_PYPROJECT)
    failed = False

    print(f"🔍 Found {len(members)} workspace members\n")

    for member in members:
        pyproject = member / "pyproject.toml"

        if not pyproject.exists():
            print(f"❌ {member}: pyproject.toml not found")
            failed = True
            continue

        name, version = read_name_and_version(pyproject)
        existing_versions = pypi_versions(name)

        print(f"🔍 {name}: local version = {version}")

        if version in existing_versions:
            print(f"❌ {name}: version {version} already exists on PyPI\n")
            failed = True
        else:
            print(f"✅ {name}: version {version} is not on PyPI\n")

    if failed:
        print("One or more package versions already exist on PyPI.")
        sys.exit(1)

    print("🎉 All package versions are safe to publish.")


if __name__ == "__main__":
    main()
