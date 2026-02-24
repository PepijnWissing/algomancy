import click
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape


class QuickstartWizard:
    """Main wizard for setting up an Algomancy application."""

    def __init__(self, skip_confirmation: bool = False, title: str | None = None):
        self.skip_confirmation = skip_confirmation
        self.title = title
        self.current_dir = Path.cwd()

        # Will be set in step 2
        self.project_name = None
        self.class_name = None
        self.filename = None

        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=PackageLoader("algomancy_quickstart", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def run(self):
        """Execute the full quickstart wizard."""
        click.echo("Starting Algomancy application setup...")
        click.echo()

        # Step 1: Create folder structure and basic main method
        self.step_1_create_structure()

        click.echo()

        # Step 2: Generate custom implementation shells (optional)
        if click.confirm(
            "Do you want to generate custom implementation templates?", default=True
        ):
            self.step_2_generate_implementations()

        click.echo()
        click.echo(click.style("✅ Setup complete!", fg="green", bold=True))
        click.echo(
            f"Your Algomancy application has been created in: {self.current_dir}"
        )
        click.echo()
        click.echo("Next steps:")
        click.echo("  1. Add your data files to the data/ folder")
        click.echo("  2. Customize the generated templates in src/")
        click.echo("  3. Run: python main.py")

    def step_1_create_structure(self):
        """Step 1: Create folder structure and generate basic main.py"""
        click.echo(
            click.style("📁 Step 1: Creating folder structure", fg="blue", bold=True)
        )
        click.echo()

        # Get project title
        if not self.title:
            self.title = click.prompt(
                "What is your project title?",
                default="My Algomancy Dashboard",
                type=str,
            )

        # Get host and port
        host = click.prompt("Host address", default="127.0.0.1", type=str)
        port = click.prompt("Port number", default=8050, type=int)

        # Define folder structure
        folders = [
            "assets",
            "data",
            "src",
            "src/data_handling",
            "src/pages",
            "src/templates",
            "src/templates/kpi",
            "src/templates/algorithm",
        ]

        # Check if any folders already exist
        existing_folders = [f for f in folders if (self.current_dir / f).exists()]

        if existing_folders and not self.skip_confirmation:
            click.echo(
                click.style(
                    "⚠️  Warning: The following folders already exist:", fg="yellow"
                )
            )
            for folder in existing_folders:
                click.echo(f"  - {folder}")
            click.echo()

            if not click.confirm(
                "Do you want to continue? (existing files will not be overwritten)"
            ):
                click.echo("Setup cancelled.")
                raise SystemExit(0)

        # Create folders
        click.echo("Creating folder structure...")
        for folder in folders:
            folder_path = self.current_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)

            # Create __init__.py for Python packages
            if folder.startswith("src"):
                init_file = folder_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()

            click.echo(f"  ✓ {folder}/")

        # Check if main.py already exists
        main_py_path = self.current_dir / "main.py"
        if main_py_path.exists():
            click.echo()
            click.echo(click.style("⚠️  Warning: main.py already exists!", fg="yellow"))

            if not self.skip_confirmation:
                if not click.confirm("Do you want to overwrite it?"):
                    click.echo("Skipping main.py generation.")
                    return

        # Generate main.py from template
        click.echo()
        click.echo("Generating main.py...")
        self._generate_main_py(self.title, host, port)
        click.echo("  ✓ main.py created")

        click.echo()
        click.echo(click.style("✅ Step 1 complete!", fg="green"))

    def step_2_generate_implementations(self):
        """Step 2: Generate custom implementation shells."""
        click.echo(
            click.style(
                "🔧 Step 2: Generating custom implementation templates",
                fg="blue",
                bold=True,
            )
        )
        click.echo()

        # Get project name for class naming
        self.project_name = click.prompt(
            "What is your project/domain name? (e.g., Sales, Inventory, Logistics)",
            type=str,
        )

        # Generate class name (PascalCase)
        self.class_name = self._to_pascal_case(self.project_name)

        # Generate filename (snake_case)
        self.filename = self._to_snake_case(self.project_name)

        click.echo()
        click.echo(f"Using class name: {self.class_name}")
        click.echo(f"Using filename: {self.filename}")
        click.echo()

        # Generate each component
        components = [
            ("schema", "src/data_handling", "schemas.py"),
            ("algorithm", "src/templates/algorithm", f"{self.filename}_algorithm.py"),
            ("kpi", "src/templates/kpi", f"{self.filename}_kpi.py"),
            ("etl_factory", "src/data_handling", "etl_factory.py"),
        ]

        click.echo("Generating implementation templates...")

        for template_name, target_dir, target_file in components:
            self._generate_implementation_file(template_name, target_dir, target_file)
            click.echo(f"  ✓ {target_dir}/{target_file}")

        # Update main.py to use custom implementations
        click.echo()
        click.echo("Updating main.py to use custom implementations...")
        self._update_main_py_with_custom_implementations()
        click.echo("  ✓ main.py updated")

        click.echo()
        click.echo(click.style("✅ Step 2 complete!", fg="green"))
        click.echo()
        click.echo(
            click.style(
                "📝 Next: Customize the TODO items in the generated files.", fg="cyan"
            )
        )

    def _generate_main_py(self, title: str, host: str, port: int):
        """Generate main.py from Jinja2 template."""
        template = self.jinja_env.get_template("main.py.jinja")

        content = template.render(title=title, host=host, port=port)

        main_py_path = self.current_dir / "main.py"
        main_py_path.write_text(content, encoding="utf-8")

    def _generate_implementation_file(
        self, template_name: str, target_dir: str, target_file: str
    ):
        """Generate an implementation file from a Jinja2 template."""
        template = self.jinja_env.get_template(f"{template_name}.py.jinja")

        content = template.render(
            project_name=self.project_name,
            class_name=self.class_name,
            filename=self.filename,
        )

        file_path = self.current_dir / target_dir / target_file

        # Don't overwrite existing files
        if file_path.exists() and not self.skip_confirmation:
            if not click.confirm(f"File {target_dir}/{target_file} exists. Overwrite?"):
                return

        file_path.write_text(content, encoding="utf-8")

    def _update_main_py_with_custom_implementations(self):
        """Update main.py to import and use custom implementations."""
        template = self.jinja_env.get_template("main_custom.py.jinja")

        content = template.render(
            title=self.title,
            host="127.0.0.1",  # Get from previous input if needed
            port=8050,  # Get from previous input if needed
            class_name=self.class_name,
            filename=self.filename,
        )

        main_py_path = self.current_dir / "main.py"
        main_py_path.write_text(content, encoding="utf-8")

    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert text to PascalCase."""
        return "".join(word.capitalize() for word in text.split())

    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert text to snake_case."""
        return "_".join(text.lower().split())


def run_quickstart(skip_confirmation: bool = False, title: str | None = None):
    """Entry point for running the quickstart wizard."""
    wizard = QuickstartWizard(skip_confirmation=skip_confirmation, title=title)
    wizard.run()
