"""
RailCall Local Vault Integration
Reads credentials from ~/.railcall/keys.local.json with fallback to environment variables.
"""

import json
import os
from typing import Any, Dict, Optional

VAULT_PATH = os.path.expanduser("~/.railcall/keys.local.json")


def load_vault(path: str = VAULT_PATH) -> Dict[str, Any]:
    """Loads keys from RailCall's 0600 secret vault."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_secret(key_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieves secret from:
    1. Environment variable (OS env / .env)
    2. RailCall Local Vault (~/.railcall/keys.local.json)
    3. Default value
    """
    # 1. Check OS environment
    env_val = os.getenv(key_name)
    if env_val:
        return env_val

    # 2. Check RailCall Vault
    vault = load_vault()
    if key_name in vault:
        return str(vault[key_name])

    return default


def get_signing_seed() -> Optional[str]:
    """Retrieves local Ed25519 signing seed from RailCall vault."""
    return get_secret("_railcall_signing_seed")
