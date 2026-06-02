import click
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
from algomancy_data import FileExtension

from .data_inference import SchemaInferenceEngine, DataFileInfo
from .asset_manager import AssetManager
from .styling_wizard import StylingWizard


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

        # Will be set in step 3
        self.detected_files: list[DataFileInfo] = []
        self.inference_engine = SchemaInferenceEngine(sample_rows=100)

        # Asset manager for step 4
        self.asset_manager = AssetManager(self.current_dir)

        # Styling wizard for step 5
        self.styling_wizard = StylingWizard()

        # Track what was generated
        self.has_custom_implementations = False
        self.has_generated_etl = False
        self.has_styling = False
        # When the user declines step 1's "overwrite existing main.py?"
        # prompt, ``_render_main_py`` becomes a no-op for the rest of the
        # run — otherwise steps 2/3/5 would silently clobber the file the
        # user just asked us to leave alone. Only meaningful for re-runs
        # against an existing project; on a fresh run the file doesn't
        # exist yet and this stays False.
        self._preserve_main_py = False
        # Interfaces baked into the generated main.py. GUI is the historical
        # default; the wizard's step_1 prompt may narrow / widen this.
        self.interfaces: list[str] = ["gui"]
        # Persistence backend: "none" | "json" | "database". The wizard's
        # step_1 prompt selects this; the template wires it into CoreConfig.
        self.persistence_backend: str = "json"
        self.database_url: str | None = None
        self.host = "127.0.0.1"
        self.port = 8050

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

        # Step 2: Generate custom implementation shells (optional). The
        # ``has_custom_implementations`` flag is set BEFORE the step so the
        # ``_update_main_py_with_custom_implementations`` call inside step 2
        # renders the right wiring on the first try (previously the flag
        # was set after the step, and the placeholder main.py only got
        # corrected when a later step re-rendered).
        if click.confirm(
            "Do you want to generate custom implementation templates?", default=True
        ):
            self.has_custom_implementations = True
            self.step_2_generate_implementations()

        click.echo()

        # Step 3: Scan data folder and generate ETL pipeline (optional).
        # ``has_generated_etl`` is set inside step 3 itself, right before the
        # main.py re-render, and only when the schemas/etl_factory files
        # were actually written. Setting it here instead would leave the
        # flag out of sync with disk (step 3's first main.py render would
        # see ``has_generated_etl=False``) and would also wrongly mark the
        # ETL as generated when the user declined the final confirm prompt.
        if click.confirm(
            "Do you want to scan your data folder and generate an ETL pipeline?",
            default=True,
        ):
            self.step_3_generate_etl_from_data()

        click.echo()

        # Steps 4 (assets) and 5 (styling) are GUI-only — the API launcher
        # never reads them. Skip the prompts entirely when GUI is not in the
        # selected interfaces, so an API-only project doesn't end up with
        # orphaned ``assets/`` content or ``src/styling_config.py``.
        if "gui" in self.interfaces:
            # Step 4: Install assets (optional)
            if click.confirm(
                "Do you want to install default assets (CSS, images)?", default=True
            ):
                self.step_4_install_assets()

            click.echo()

            # Step 5: Configure styling (optional)
            if click.confirm(
                "Do you want to configure custom styling (colors, themes)?",
                default=True,
            ):
                self.step_5_configure_styling()

            click.echo()

        # Step 6: Generate pytest skeletons (optional)
        if click.confirm(
            "Do you want to generate pytest skeletons for the generated code?",
            default=True,
        ):
            self.step_6_generate_tests()

        click.echo()
        click.echo(click.style(" Setup complete!", fg="green", bold=True))
        click.echo(
            f"Your Algomancy application has been created in: {self.current_dir}"
        )
        click.echo()
        click.echo("Next steps:")
        click.echo("  1. Review and customize the generated files")
        extra_pkgs = []
        if "api" in self.interfaces:
            extra_pkgs.append("algomancy-api")
        if self.persistence_backend == "database":
            extra_pkgs.append("algomancy-data[database]")
        if extra_pkgs:
            click.echo(
                f"  2. Install required packages: pip install {' '.join(extra_pkgs)}"
            )
        if len(self.interfaces) == 1:
            click.echo("  3. Run: python main.py")
        else:
            click.echo(
                f"  3. Run: python main.py --interface {{{','.join(self.interfaces)}}}"
            )
        if "gui" in self.interfaces:
            click.echo(
                f"  4. (GUI) Open your browser at http://{self.host}:{self.port}"
            )

    def step_1_create_structure(self):
        """Step 1: Create folder structure and generate basic main.py"""
        click.echo(
            click.style(" Step 1: Creating folder structure", fg="blue", bold=True)
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
        self.host = click.prompt("Host address", default="127.0.0.1", type=str)
        self.port = click.prompt("Port number", default=8050, type=int)

        # Ask which interface(s) to expose. The generated ``main.py`` will
        # only wire up the launchers the user picked here; if more than one
        # is selected, it dispatches on ``--interface``.
        self.interfaces = self._prompt_interfaces()

        # Ask which persistence backend to bake into CoreConfig.
        self.persistence_backend, self.database_url = self._prompt_persistence()

        # Define folder structure. ``assets/`` and ``src/pages/`` are
        # GUI-only — emit them only when the user opted into the GUI
        # interface. ``data/setup/`` stays unconditional: the ETL pipeline
        # still reads from it for API-only projects.
        folders = [
            "data",
            "data/setup",
            "src",
            "src/data_handling",
            "src/templates",
            "src/templates/kpi",
            "src/templates/algorithm",
        ]
        if "gui" in self.interfaces:
            folders = ["assets", *folders, "src/pages"]

        # Check if any folders already exist
        existing_folders = [f for f in folders if (self.current_dir / f).exists()]

        if existing_folders and not self.skip_confirmation:
            click.echo(
                click.style(
                    "  Warning: The following folders already exist:", fg="yellow"
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
            click.echo(click.style("  Warning: main.py already exists!", fg="yellow"))

            if not self.skip_confirmation:
                if not click.confirm("Do you want to overwrite it?"):
                    click.echo("Skipping main.py generation.")
                    # Lock subsequent steps out of re-rendering main.py too.
                    self._preserve_main_py = True
                    return

        # Generate main.py from template
        click.echo()
        click.echo("Generating main.py...")
        self._generate_main_py(self.title, self.host, self.port)
        click.echo("  ✓ main.py created")

        click.echo()
        click.echo(click.style(" Step 1 complete!", fg="green"))

    def step_2_generate_implementations(self):
        """Step 2: Generate custom implementation shells."""
        click.echo(
            click.style(
                " Step 2: Generating custom implementation templates",
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

        # Generate each component. Page templates are GUI-only — for an
        # API-only project the generated ``main.py`` doesn't import them, so
        # emitting them just leaves orphans on disk (#170).
        components = [
            ("schema", "src/data_handling", "schemas.py"),
            ("algorithm", "src/templates/algorithm", f"{self.filename}_algorithm.py"),
            ("kpi", "src/templates/kpi", f"{self.filename}_kpi.py"),
            ("etl_factory", "src/data_handling", "etl_factory.py"),
        ]
        if "gui" in self.interfaces:
            components.extend(
                [
                    ("home_page", "src/pages", "home_page.py"),
                    ("data_page", "src/pages", "data_page.py"),
                    ("scenario_page", "src/pages", "scenario_page.py"),
                    ("compare_page", "src/pages", "compare_page.py"),
                    ("overview_page", "src/pages", "overview_page.py"),
                ]
            )

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
        click.echo(click.style(" Step 2 complete!", fg="green"))
        click.echo()
        click.echo(
            click.style(
                " Next: Customize the TODO items in the generated files.", fg="cyan"
            )
        )

    def step_3_generate_etl_from_data(self):
        """Step 3: Scan data folder and generate ETL pipeline."""
        click.echo(
            click.style(
                " Step 3: Scanning data folder and generating ETL pipeline",
                fg="blue",
                bold=True,
            )
        )
        click.echo()

        data_setup_dir = self.current_dir / "data" / "setup"

        # Check if data/setup exists
        if not data_setup_dir.exists():
            click.echo(
                click.style("  Directory data/setup/ does not exist!", fg="yellow")
            )
            return

        # Scan for files with retry logic
        while True:
            detected_files = self.inference_engine.scan_directory(data_setup_dir)

            if not detected_files:
                click.echo(
                    click.style("  No data files found in data/setup/", fg="yellow")
                )
                click.echo()
                click.echo("Supported file types: CSV, XLSX, JSON")
                click.echo()

                choice = click.prompt(
                    "What would you like to do?",
                    type=click.Choice(["retry", "skip"], case_sensitive=False),
                    default="retry",
                )

                if choice == "skip":
                    click.echo("Skipping ETL generation.")
                    return
                else:
                    click.echo()
                    click.echo(
                        "Please add your data files to data/setup/ and press Enter to retry..."
                    )
                    input()
                    continue
            else:
                break

        # Display detected files
        click.echo(f"Found {len(detected_files)} data file(s):")
        for file_info in detected_files:
            sheets_info = (
                f" ({len(file_info.sheet_names)} sheets)"
                if file_info.sheet_names
                else ""
            )
            click.echo(
                f"  • {file_info.file_name}{file_info.file_path.suffix} - {file_info.extension.value}{sheets_info}"
            )

        # Interactive schema inference for each file
        click.echo()
        click.echo(click.style("Let's configure each file...", fg="cyan"))

        for file_info in detected_files:
            success = self.inference_engine.infer_schema_interactive(file_info)

            if success and not file_info.skip_file:
                # Refresh total_columns now that inference is done — the
                # ``class_name`` / ``snake_name`` defaults from DataFileInfo
                # are already in place, and we let any per-project rename
                # logic stay there so failed-inference files still render.
                file_info.total_columns = sum(
                    len(cols) for cols in file_info.inferred_schemas.values()
                )
            elif not success and not file_info.skip_file:
                # Inference failed (e.g., pandas raised on a malformed file).
                # Drop the file rather than emit an empty schema class that
                # collides with the imported ``Schema`` symbol.
                file_info.skip_file = True

        # Filter out skipped files
        self.detected_files = [f for f in detected_files if not f.skip_file]

        # Disambiguate class names across files that share a stem (e.g.
        # ``orders.csv`` + ``orders.xlsx``) so the generated schema classes
        # remain unique.
        self._disambiguate_class_names(self.detected_files)

        if not self.detected_files:
            click.echo()
            click.echo(
                click.style("  No files selected for ETL pipeline.", fg="yellow")
            )
            return

        click.echo()
        click.echo(click.style("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", fg="cyan"))
        click.echo()

        # Display summary of inferred schemas
        self._display_inferred_schemas_summary()

        # Ask for final confirmation
        if not self.skip_confirmation:
            click.echo()
            if not click.confirm(
                "Generate ETL pipeline with these configurations?", default=True
            ):
                click.echo("Skipping ETL generation.")
                return

        click.echo()
        click.echo("Generating schema and ETL files...")

        # Generate schemas file
        self._generate_schemas_file()
        click.echo("  ✓ src/data_handling/generated_schemas.py")

        # Generate or update ETL factory
        self._generate_etl_factory_file()
        click.echo("  ✓ src/data_handling/etl_factory.py")

        # Flip the flag BEFORE re-rendering main.py — otherwise the template
        # would emit imports pointing at ``schemas.py`` (the step-2 stub)
        # rather than ``generated_schemas.py`` that we just wrote.
        self.has_generated_etl = True

        # Update main.py to use generated schemas
        click.echo()
        click.echo("Updating main.py to use generated schemas...")
        self._update_main_py_with_generated_etl()
        click.echo("  ✓ main.py updated")

        click.echo()
        click.echo(click.style(" Step 3 complete!", fg="green"))
        click.echo()
        click.echo(
            click.style(
                " Generated files can be customized in src/data_handling/", fg="cyan"
            )
        )

    def step_4_install_assets(self):
        """Step 4: Install default assets from GitHub or bundled fallback."""
        try:
            success = self.asset_manager.install_assets(
                skip_confirmation=self.skip_confirmation
            )

            if success:
                click.echo()
                click.echo(click.style(" Step 4 complete!", fg="green"))
                click.echo()
                click.echo(
                    click.style(
                        " Assets installed. You can customize them in the assets/ folder.",
                        fg="cyan",
                    )
                )
            else:
                click.echo()
                click.echo(
                    click.style(
                        "  Step 4 incomplete - no assets installed", fg="yellow"
                    )
                )

        except Exception as e:
            click.echo()
            click.echo(click.style(f" Error in Step 4: {e}", fg="red"))

    def step_5_configure_styling(self):
        """Step 5: Configure custom styling."""
        try:
            # Run the styling wizard
            styling_config = self.styling_wizard.run()

            click.echo()
            click.echo("Generating styling configuration...")

            # Generate styling_config.py
            self._generate_styling_config(styling_config)
            click.echo("  ✓ src/styling_config.py")

            # Update main.py to use styling
            click.echo()
            click.echo("Updating main.py to use custom styling...")
            self._update_main_py_with_styling()
            click.echo("  ✓ main.py updated")

            click.echo()
            click.echo(click.style(" Step 5 complete!", fg="green"))
            click.echo()
            click.echo(
                click.style(
                    " You can customize styling further in src/styling_config.py",
                    fg="cyan",
                )
            )

        except Exception as e:
            click.echo()
            click.echo(click.style(f" Error in Step 5: {e}", fg="red"))

    def step_6_generate_tests(self):
        """Step 6: Generate pytest skeletons for the generated code.

        Always emits a ``conftest.py`` (so the ``src`` package is importable
        from ``tests/``). Algorithm + KPI skeletons land when
        ``has_custom_implementations`` is true; the ETL-factory skeleton
        lands when either custom implementations or a generated ETL exists.
        """
        click.echo(
            click.style(" Step 6: Generating pytest skeletons", fg="blue", bold=True)
        )
        click.echo()

        tests_dir = self.current_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # tests/__init__.py keeps editors / type-checkers happy even though
        # pytest itself does not require it.
        init_file = tests_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()

        # conftest.py ensures the project root is on sys.path so the
        # generated ``from src... import ...`` statements resolve.
        self._write_test_file("conftest.py.jinja", tests_dir / "conftest.py")
        click.echo("  ✓ tests/conftest.py")

        if self.has_custom_implementations:
            self._write_test_file(
                "test_algorithm.py.jinja",
                tests_dir / f"test_{self.filename}_algorithm.py",
            )
            click.echo(f"  ✓ tests/test_{self.filename}_algorithm.py")

            self._write_test_file(
                "test_kpi.py.jinja",
                tests_dir / f"test_{self.filename}_kpi.py",
            )
            click.echo(f"  ✓ tests/test_{self.filename}_kpi.py")

        if self.has_custom_implementations or self.has_generated_etl:
            self._write_test_file(
                "test_etl_factory.py.jinja",
                tests_dir / "test_etl_factory.py",
            )
            click.echo("  ✓ tests/test_etl_factory.py")

        click.echo()
        click.echo(click.style(" Step 6 complete!", fg="green"))
        click.echo()
        click.echo(
            click.style(
                " Run the tests with: pytest tests/",
                fg="cyan",
            )
        )

    def _write_test_file(self, template_name: str, target_path: Path) -> None:
        """Render a pytest-skeleton template and write it to ``target_path``.

        Skips files that already exist unless ``--skip-confirmation`` is set
        and the user opted in to overwrite — mirrors the convention used
        elsewhere in the wizard.
        """
        template = self.jinja_env.get_template(template_name)
        content = template.render(
            project_name=self.project_name or "Project",
            class_name=self.class_name or "Custom",
            filename=self.filename or "custom",
            has_custom_implementations=self.has_custom_implementations,
            has_generated_etl=self.has_generated_etl,
        )

        if target_path.exists() and not self.skip_confirmation:
            if not click.confirm(f"File tests/{target_path.name} exists. Overwrite?"):
                return

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

    def _generate_styling_config(self, config: dict):
        """Generate styling_config.py file.

        Guarded by the same overwrite-confirm pattern as the schemas / ETL
        factory writes so a wizard re-run can't silently clobber a
        user-edited ``styling_config.py``.
        """
        template = self.jinja_env.get_template("styling_config.py.jinja")

        content = template.render(
            project_name=self.project_name or "Project",
            background=config["background"],
            primary=config["primary"],
            secondary=config["secondary"],
            text=config["text"],
            text_highlight=config["text_highlight"],
            text_selected=config["text_selected"],
            button_mode=config["button_mode"].name,
            card_mode=config["card_mode"].name,
            logo_path=config.get("logo_path"),
            button_path=config.get("button_path"),
        )

        config_path = self.current_dir / "src" / "styling_config.py"

        if config_path.exists() and not self.skip_confirmation:
            if not click.confirm(f"File {config_path.name} exists. Overwrite?"):
                return

        config_path.write_text(content, encoding="utf-8")

    def _update_main_py_with_styling(self):
        """Update main.py to import and use styling configuration."""
        self.has_styling = True
        self._render_main_py()

    def _display_inferred_schemas_summary(self):
        """Display a summary of all inferred schemas.

        For ``SchemaType.MULTI`` files (XLSX-multi or nested-JSON), each
        group is rendered as its own section with ``source_path``,
        primary-key, and foreign-key annotations so the user can see the
        structure that will end up in the generated schema file.
        """
        click.echo(click.style("Summary of detected schemas:", fg="cyan", bold=True))
        click.echo()

        for file_info in self.detected_files:
            type_label = "MULTI" if file_info.is_multi_table else "SINGLE"
            click.echo(
                click.style(
                    f"📄 {file_info.file_name}{file_info.file_path.suffix}"
                    f"   ({type_label})",
                    fg="cyan",
                    bold=True,
                )
            )

            # Show configuration
            if file_info.extension == FileExtension.CSV:
                click.echo(f"  Config: CSV separator = '{file_info.csv_separator}'")
            elif file_info.extension == FileExtension.XLSX:
                click.echo(
                    f"  Config: Extracting {len(file_info.sheets_to_extract)} sheet(s)"
                )

            # Show schemas
            for schema_name, columns in file_info.inferred_schemas.items():
                if file_info.is_multi_table:
                    self._echo_group_header(file_info, schema_name)

                pk_cols = set(file_info.primary_key_columns.get(schema_name, []))
                fk_map = file_info.nested_foreign_keys.get(schema_name, {})

                col_items = list(columns.items())
                show_count = min(10, len(col_items))

                # Right-pad column names within the shown window so the type
                # column lines up vertically — easier to scan than ragged.
                shown = col_items[:show_count]
                width = max((len(name) for name, _ in shown), default=0)

                for col_name, data_type in shown:
                    type_color = self._get_type_color(data_type)
                    annotations: list[str] = []
                    if col_name in pk_cols:
                        annotations.append("primary key")
                    fk = fk_map.get(col_name)
                    if fk:
                        annotations.append(f"foreign key → {fk[0]}.{fk[1]}")
                    suffix = f"  ({', '.join(annotations)})" if annotations else ""
                    click.echo(
                        f"    • {col_name.ljust(width)}  "
                        f"{click.style(data_type.value, fg=type_color)}{suffix}"
                    )

                if len(col_items) > show_count:
                    click.echo(
                        f"    ... and {len(col_items) - show_count} more column(s)"
                    )

            click.echo()

    @staticmethod
    def _echo_group_header(file_info, group_name: str) -> None:
        """Print the ``Group: <name>   (source_path: ...)`` header for a MULTI group.

        XLSX-multi files have no ``source_path`` — they're inherently
        per-sheet — so the header collapses to the group name alone. Nested
        JSON renders ``root`` for the parent and the dotted key path for
        children.
        """
        if file_info.is_nested_json:
            path = file_info.nested_source_paths.get(group_name, ())
            source_label = ".".join(path) if path else "root"
            click.echo(f"  Group: {group_name}   (source_path: {source_label})")
        else:
            click.echo(f"  Sheet: {group_name}")

    def _get_type_color(self, data_type) -> str:
        """Get color for a data type."""
        from algomancy_data import DataType

        color_map = {
            DataType.INTEGER: "blue",
            DataType.FLOAT: "blue",
            DataType.STRING: "green",
            DataType.BOOLEAN: "magenta",
            DataType.DATETIME: "yellow",
        }
        return color_map.get(data_type, "white")

    def _generate_schemas_file(self):
        """Generate the schemas file from detected data.

        Honors the same ``skip_confirmation`` / existing-file dance as
        :meth:`_generate_etl_factory_file` so a wizard re-run can't silently
        clobber a user-edited ``generated_schemas.py``.
        """
        template = self.jinja_env.get_template("generated_schemas.py.jinja")

        content = template.render(
            project_name=self.project_name or "Project",
            files=self.detected_files,
        )

        schemas_path = (
            self.current_dir / "src" / "data_handling" / "generated_schemas.py"
        )

        if schemas_path.exists() and not self.skip_confirmation:
            if not click.confirm(f"File {schemas_path.name} exists. Overwrite?"):
                return

        schemas_path.write_text(content, encoding="utf-8")

    def _generate_etl_factory_file(self):
        """Generate the ETL factory file with extractors.

        Files are partitioned into registry-default (handled by
        ``super().create_extraction_sequence``) vs custom (hand-wired with
        an explicit extractor) based on whether they need non-default
        constructor arguments — CSV with a non-comma separator, or a
        single-sheet XLSX where the sheet must be specified by name.
        """
        template = self.jinja_env.get_template("etl_factory_generated.py.jinja")

        default_files: list = []
        custom_files: list = []
        needs_csv_extractor = False
        needs_xlsx_single_extractor = False

        for file_info in self.detected_files:
            ext = file_info.extension.name
            if file_info.is_multi_sheet or ext == "JSON":
                default_files.append(file_info)
            elif ext == "CSV":
                if (file_info.csv_separator or ",") == ",":
                    default_files.append(file_info)
                else:
                    custom_files.append(file_info)
                    needs_csv_extractor = True
            elif ext == "XLSX":
                # Single-sheet XLSX: pin the sheet by name explicitly so we
                # don't depend on the registry default's sheet selection.
                custom_files.append(file_info)
                needs_xlsx_single_extractor = True
            else:
                default_files.append(file_info)

        content = template.render(
            project_name=self.project_name or "Project",
            class_name=self.class_name or "Custom",
            files=self.detected_files,
            file_count=len(self.detected_files),
            default_files=default_files,
            custom_files=custom_files,
            needs_csv_extractor=needs_csv_extractor,
            needs_xlsx_single_extractor=needs_xlsx_single_extractor,
        )

        etl_path = self.current_dir / "src" / "data_handling" / "etl_factory.py"

        # Check if file exists
        if etl_path.exists() and not self.skip_confirmation:
            if not click.confirm(f"File {etl_path.name} exists. Overwrite?"):
                return

        etl_path.write_text(content, encoding="utf-8")

    def _update_main_py_with_generated_etl(self):
        """Update main.py to use generated ETL and schemas."""
        self._render_main_py()

    def _generate_main_py(self, title: str, host: str, port: int):
        """Generate the initial main.py (called from step 1).

        Later steps re-render ``main.py`` via :meth:`_render_main_py` with
        richer context (custom implementations, generated ETL, styling) — they
        all share the same unified template.
        """
        self._render_main_py()

    def _render_main_py(self) -> None:
        """Render ``main.py`` using the current wizard state.

        Idempotent — every step that wants to refresh the wiring just calls
        this, and the template's flags (``interfaces``, ``has_styling``,
        ``has_custom_implementations``, ``has_generated_etl``) take care of
        emitting the right launchers and imports.

        No-op when ``_preserve_main_py`` is set — the user already declined
        step 1's overwrite prompt, and a later step's re-render would
        contradict that decision.
        """
        if self._preserve_main_py:
            return
        template = self.jinja_env.get_template("main.py.jinja")
        content = template.render(
            title=self.title,
            host=self.host,
            port=self.port,
            interfaces=self.interfaces,
            class_name=self.class_name or "Custom",
            filename=self.filename or "custom",
            has_custom_implementations=self.has_custom_implementations,
            has_generated_etl=self.has_generated_etl,
            has_styling=self.has_styling,
            persistence_backend=self.persistence_backend,
            database_url=self.database_url,
        )
        main_py_path = self.current_dir / "main.py"
        main_py_path.write_text(content, encoding="utf-8")

    @staticmethod
    def _prompt_persistence() -> tuple[str, str | None]:
        """Ask the user which persistence backend the generated app should use.

        Returns ``(backend, database_url)`` where ``backend`` is one of
        ``"none"`` / ``"json"`` / ``"database"`` and ``database_url`` is
        only meaningful when ``backend == "database"`` (otherwise ``None``).
        """
        click.echo()
        click.echo("Which persistence backend should the generated app use?")
        click.echo("  none     — in-memory only, nothing is persisted")
        click.echo("  json     — persistent JSON-on-disk (the historical default)")
        click.echo("  database — SQL-backed via DatabaseDataManager")
        backend = click.prompt(
            "Backend",
            type=click.Choice(["none", "json", "database"], case_sensitive=False),
            default="json",
            show_default=True,
        ).lower()

        if backend == "database":
            click.echo()
            click.echo(
                "  Tip: install the database extras via "
                "'pip install algomancy-data[database]'"
            )
            database_url = click.prompt(
                "Database URL (SQLAlchemy)",
                default="sqlite:///myapp.db",
                type=str,
                show_default=True,
            )
            return backend, database_url
        return backend, None

    @staticmethod
    def _prompt_interfaces() -> list[str]:
        """Ask the user which interface(s) to bake into ``main.py``.

        Accepts a comma-separated list of ``gui``, ``api`` (any
        non-empty subset). The wizard's default is GUI for backwards
        compatibility with pre-#128 quickstart runs.
        """
        click.echo()
        click.echo("Which interface(s) should the generated main.py expose?")
        click.echo("  Options: gui, api (comma-separated, e.g. 'gui,api')")
        valid = {"gui", "api"}
        while True:
            raw = click.prompt("Interfaces", default="gui", type=str, show_default=True)
            parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
            unique: list[str] = []
            for p in parts:
                if p not in valid:
                    click.echo(
                        click.style(
                            f"  Unknown interface '{p}' — choose from {sorted(valid)}",
                            fg="yellow",
                        )
                    )
                    break
                if p not in unique:
                    unique.append(p)
            else:
                if unique:
                    return unique
                click.echo(click.style("  Pick at least one interface.", fg="yellow"))

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

        # Ensure the target directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Don't overwrite existing files
        if file_path.exists() and not self.skip_confirmation:
            if not click.confirm(f"File {target_dir}/{target_file} exists. Overwrite?"):
                return

        file_path.write_text(content, encoding="utf-8")

    def _update_main_py_with_custom_implementations(self):
        """Update main.py to import and use custom implementations."""
        self._render_main_py()

    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert text to PascalCase."""
        from .data_inference import _to_pascal_case as _impl

        return _impl(text)

    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert text to snake_case."""
        from .data_inference import _to_snake_case as _impl

        return _impl(text)

    @staticmethod
    def _disambiguate_class_names(files: list) -> None:
        """Ensure ``file_info.class_name`` is unique across ``files``.

        When two files have the same stem (e.g. ``orders.csv`` and
        ``orders.xlsx``), suffix the class name with the file extension so
        the generated schema classes remain distinct.
        """
        seen: dict[str, int] = {}
        for file_info in files:
            name = file_info.class_name
            count = seen.get(name, 0)
            if count > 0:
                ext_suffix = file_info.extension.name.title()
                candidate = f"{name}{ext_suffix}"
                # If even the ext-suffixed name collides, append a counter.
                bumped = candidate
                n = 2
                while bumped in seen:
                    bumped = f"{candidate}{n}"
                    n += 1
                file_info.class_name = bumped
            seen[file_info.class_name] = seen.get(file_info.class_name, 0) + 1


def run_quickstart(skip_confirmation: bool = False, title: str | None = None):
    """Entry point for running the quickstart wizard."""
    wizard = QuickstartWizard(skip_confirmation=skip_confirmation, title=title)
    wizard.run()
