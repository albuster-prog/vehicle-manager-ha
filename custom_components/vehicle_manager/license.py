"""License validation for Vehicle Manager HA."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

_LOGGER = logging.getLogger(__name__)

# Pro license keys are SHA256 hashes stored in the backend.
# Format: VM-XXXX-XXXX-XXXX-XXXX (generated after BMAC payment)
# Offline validation: we store activated keys in HA storage.

LICENSE_STORAGE_KEY = "vehicle_manager_licenses"


def validate_license_format(key: str) -> bool:
    """Check if license key has correct format VM-XXXX-XXXX-XXXX-XXXX."""
    if not key:
        return False
    parts = key.strip().upper().split("-")
    if len(parts) != 5:
        return False
    if parts[0] != "VM":
        return False
    return all(len(p) == 4 and p.isalnum() for p in parts[1:])


def generate_license_hash(key: str) -> str:
    """Generate SHA256 hash of a license key for storage."""
    return hashlib.sha256(key.strip().upper().encode()).hexdigest()


async def verify_license_online(key: str, session) -> dict:
    """
    Verify license against the online backend (Vercel serverless).
    Returns: {"valid": bool, "tier": "pro"|"free", "activated_at": str|None}
    """
    from .const import BMAC_VERIFY_URL
    try:
        async with session.post(
            BMAC_VERIFY_URL,
            json={"key": key.strip().upper()},
            timeout=10,
        ) as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception as err:
        _LOGGER.warning("License verification failed (offline?): %s", err)
    return {"valid": False, "tier": "free", "activated_at": None}


def is_pro_feature_allowed(license_key: str | None) -> bool:
    """
    Check if a feature requiring PRO is allowed.
    During development / alpha: always True.
    In production: check license key.
    """
    # TODO: replace with real verification in v1.0
    if not license_key:
        return False
    return validate_license_format(license_key)


def get_license_tier(license_key: str | None) -> str:
    """Return 'pro' or 'free' based on license key."""
    from .const import LICENSE_FREE, LICENSE_PRO
    if is_pro_feature_allowed(license_key):
        return LICENSE_PRO
    return LICENSE_FREE
