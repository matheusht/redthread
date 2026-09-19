"""Shared capability taxonomy for Phase 8 authorization decisions."""

from __future__ import annotations

from enum import Enum


class CapabilityClass(str, Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    EXECUTION = "execution"
    EXFILTRATION = "exfiltration"
    DELEGATION = "delegation"
    CONFIG_MUTATION = "config_mutation"
    MEMORY_MUTATION = "memory_mutation"
    NETWORK_EGRESS = "network_egress"
    SECRET_ACCESS = "secret_access"
    UNKNOWN = "unknown"


READ_ONLY_CAPABILITIES = {"lookup_status", "tool.read", "web.fetch", "docs.search", "db.read", "file.read"}
HIGH_RISK_CAPABILITIES = {
    "agent.delegate",
    "db.export",
    "db.write",
    "file.write",
    "file.delete",
    "file.chmod",
    "http.post",
    "memory.write",
    "network.egress",
    "prompt.update",
    "secrets.read",
    "shell.exec",
    "system.update",
}
CAPABILITY_PREFIX_CLASSES: tuple[tuple[str, CapabilityClass], ...] = (
    ("agent.", CapabilityClass.DELEGATION),
    ("db.read", CapabilityClass.READ_ONLY),
    ("db.export", CapabilityClass.EXFILTRATION),
    ("db.write", CapabilityClass.WRITE),
    ("docs.", CapabilityClass.READ_ONLY),
    ("file.write", CapabilityClass.WRITE),
    ("file.read", CapabilityClass.READ_ONLY),
    ("file.delete", CapabilityClass.WRITE),
    ("file.chmod", CapabilityClass.CONFIG_MUTATION),
    ("http.post", CapabilityClass.NETWORK_EGRESS),
    ("memory.write", CapabilityClass.MEMORY_MUTATION),
    ("network.", CapabilityClass.NETWORK_EGRESS),
    ("prompt.", CapabilityClass.CONFIG_MUTATION),
    ("secrets.", CapabilityClass.SECRET_ACCESS),
    ("shell.", CapabilityClass.EXECUTION),
    ("system.", CapabilityClass.CONFIG_MUTATION),
    ("tool.read", CapabilityClass.READ_ONLY),
    ("web.fetch", CapabilityClass.READ_ONLY),
)
HIGH_IMPACT_CLASSES = {
    CapabilityClass.WRITE,
    CapabilityClass.EXECUTION,
    CapabilityClass.EXFILTRATION,
    CapabilityClass.DELEGATION,
    CapabilityClass.CONFIG_MUTATION,
    CapabilityClass.MEMORY_MUTATION,
    CapabilityClass.NETWORK_EGRESS,
    CapabilityClass.SECRET_ACCESS,
}


def classify_capability(capability: str) -> CapabilityClass:
    if capability in READ_ONLY_CAPABILITIES:
        return CapabilityClass.READ_ONLY
    if capability in HIGH_RISK_CAPABILITIES:
        return _classify_by_prefix(capability)
    return _classify_by_prefix(capability)



def is_high_risk_capability(capability: str) -> bool:
    return capability in HIGH_RISK_CAPABILITIES or classify_capability(capability) in HIGH_IMPACT_CLASSES



def is_read_only_capability(capability: str) -> bool:
    return classify_capability(capability) == CapabilityClass.READ_ONLY



def _classify_by_prefix(capability: str) -> CapabilityClass:
    for prefix, capability_class in CAPABILITY_PREFIX_CLASSES:
        if capability.startswith(prefix):
            return capability_class
    return CapabilityClass.UNKNOWN
