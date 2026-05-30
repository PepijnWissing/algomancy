"""Extractor registry keyed on ``(FileExtension, SchemaType)``.

Replaces the previous hand-wired if/elif dispatch with a registry that
ships pre-populated for the built-in extractors and is open for projects
to extend via :func:`register_extractor` (see M5).

Example::

    register_extractor(FileExtension.PARQUET, SchemaType.SINGLE, ParquetExtractor)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Tuple, Type

from .schema import FileExtension, SchemaType

if TYPE_CHECKING:
    from .extractor import Extractor


_REGISTRY: Dict[Tuple[FileExtension, SchemaType], Type["Extractor"]] = {}


def register_extractor(
    extension: FileExtension,
    schema_type: SchemaType,
    cls: Type["Extractor"],
) -> None:
    """Register ``cls`` as the extractor for ``(extension, schema_type)``.

    Overwrites any prior registration for the same key. Intended for
    framework defaults at import time and for user projects to plug in
    custom file formats (issue #97 in M5).
    """
    _REGISTRY[(extension, schema_type)] = cls


def get_extractor_class(
    extension: FileExtension, schema_type: SchemaType
) -> Optional[Type["Extractor"]]:
    """Return the registered extractor class for ``(extension, schema_type)``.

    Returns ``None`` if no entry is registered; callers decide whether
    that is a hard error or a fallback condition.
    """
    return _REGISTRY.get((extension, schema_type))


def registered_keys() -> Tuple[Tuple[FileExtension, SchemaType], ...]:
    """Return all currently registered ``(extension, schema_type)`` keys."""
    return tuple(_REGISTRY.keys())


def _populate_defaults() -> None:
    """Register the built-in extractors. Called at import time."""
    # Local imports to avoid a circular dependency between extractor.py
    # and registry.py.
    from .extractor import (
        CSVSingleExtractor,
        JSONMultiExtractor,
        JSONSingleExtractor,
        XLSXMultiExtractor,
        XLSXSingleExtractor,
    )

    register_extractor(FileExtension.CSV, SchemaType.SINGLE, CSVSingleExtractor)
    register_extractor(FileExtension.JSON, SchemaType.SINGLE, JSONSingleExtractor)
    register_extractor(FileExtension.JSON, SchemaType.MULTI, JSONMultiExtractor)
    register_extractor(FileExtension.XLSX, SchemaType.SINGLE, XLSXSingleExtractor)
    register_extractor(FileExtension.XLSX, SchemaType.MULTI, XLSXMultiExtractor)
