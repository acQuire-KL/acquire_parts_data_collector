"""Backward-compatible imports for the PDCPartProfile model.

New code should import from :mod:`provider_profiles.pdc_part_profile`.
"""
from .pdc_part_profile import *  # noqa: F401,F403
from .pdc_part_profile import (
    PDCPartProfile,
    PDC_PART_PROFILE_SCHEMA_VERSION,
)

# Temporary compatibility aliases for code written before Sprint 4.2.5.
ProviderPartProfile = PDCPartProfile
PROVIDER_PART_PROFILE_SCHEMA_VERSION = PDC_PART_PROFILE_SCHEMA_VERSION
