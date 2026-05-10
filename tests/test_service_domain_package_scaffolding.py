from __future__ import annotations

from importlib import import_module
from pathlib import Path


DOMAIN_PACKAGES = [
    "platform",
    "delivery",
    "celonis",
    "knowledge",
    "integrations",
    "orchestration",
    "shared",
]


def test_domain_service_packages_exist() -> None:
    services_dir = Path("src/foundry/services")

    for package in DOMAIN_PACKAGES:
        package_dir = services_dir / package
        assert package_dir.is_dir(), f"Missing package directory: {package_dir}"
        assert (package_dir / "__init__.py").is_file(), f"Missing __init__.py for {package}"


def test_domain_service_packages_are_importable() -> None:
    for package in DOMAIN_PACKAGES:
        module = import_module(f"foundry.services.{package}")
        assert module is not None
