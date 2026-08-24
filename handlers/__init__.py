"""
RailCall Lead Governance Airlock Handlers
"""

from typing import Any, Dict, TypedDict, Optional

class HandlerResult(TypedDict, total=False):
    status: str
    action: str
    summary: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    preview_diff: Optional[Dict[str, Any]]
    receipt_meta: Optional[Dict[str, Any]]
