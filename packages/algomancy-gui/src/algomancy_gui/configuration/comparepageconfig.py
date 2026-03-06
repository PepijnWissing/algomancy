from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ComparePageConfig:
    """Compare page specific settings."""

    default_open: List[str] = field(default_factory=list)
    ordered_components: List[str] = field(default_factory=list)

    VALID_COMPONENTS = ["side-by-side", "kpis", "compare", "details"]

    def __post_init__(self):
        self._validate()

    def _validate(self) -> None:
        """Validate compare page configuration."""
        # Basic type checks for collections
        if not isinstance(self.default_open, list):
            raise ValueError("default_open must be a list of strings")
        if not isinstance(self.ordered_components, list):
            raise ValueError("ordered_components must be a list of strings")

        # Ensure all strings are valid
        for component in self.default_open:
            if not isinstance(component, str):
                raise ValueError(
                    f"default_open must be a list of strings, but contains {component}"
                )
            if component not in self.VALID_COMPONENTS:
                raise ValueError(
                    f"default_open contains invalid component: {component}"
                )

        for component in self.ordered_components:
            if not isinstance(component, str):
                raise ValueError(
                    f"ordered_components must be a list of strings, but contains {component}"
                )
            if component not in self.VALID_COMPONENTS:
                raise ValueError(
                    f"ordered_components contains invalid component: {component}"
                )

        # Ensure all strings are unique
        if len(self.default_open) != len(set(self.default_open)):
            raise ValueError("default_open contains duplicate values")
        if len(self.ordered_components) != len(set(self.ordered_components)):
            raise ValueError("ordered_components contains duplicate values")

    def as_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "compare_default_open": self.default_open,
            "compare_ordered_list_components": self.ordered_components,
        }
