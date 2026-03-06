import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class FeatureConfig:
    """
    Feature flags and optional functionality.

    Args:
        allow_parameter_upload_from_file: Allow uploading parameters from file.
        use_authentication: Enable authentication for the app.
    """

    allow_parameter_upload_from_file: bool = False
    use_authentication: bool = False

    def __post_init__(self):
        if self.use_authentication is None:
            raise ValueError(
                "use_authentication must be set to True or False, not None"
            )

        if self.use_authentication:
            if not os.getenv("APP_USERNAME") or not os.getenv("APP_PASSWORD"):
                raise ValueError(
                    "Environment variables 'APP_USERNAME' and 'APP_PASSWORD' must be set"
                )  # todo document where to set username and password

    def as_dict(self) -> Dict[str, Any]:
        return {
            "allow_param_upload_by_file": self.allow_parameter_upload_from_file,
            "use_authentication": self.use_authentication,
        }
