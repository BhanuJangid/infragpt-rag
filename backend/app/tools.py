"""Mock VMware vCenter and Nutanix Prism APIs — no real credentials."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from app.config import settings

INVENTORY_PATH = settings.data_dir / "inventory.json"


def _load() -> dict[str, Any]:
    return json.loads(INVENTORY_PATH.read_text())


def list_vms(cluster: str | None = None, power_state: str | None = None) -> dict[str, Any]:
    data = _load()
    vms = data["vcenter"]["vms"]
    if cluster:
        vms = [vm for vm in vms if vm["cluster"].lower() == cluster.lower()]
    if power_state:
        vms = [vm for vm in vms if vm["power_state"].lower() == power_state.lower()]
    return {"count": len(vms), "vms": vms}


def get_vm(name: str) -> dict[str, Any]:
    data = _load()
    for vm in data["vcenter"]["vms"]:
        if vm["name"].lower() == name.lower():
            return vm
    return {"error": f"VM '{name}' not found"}


def power_action(name: str, action: str) -> dict[str, Any]:
    action = action.lower()
    allowed = {"on", "off", "reset", "suspend"}
    if action not in allowed:
        return {"error": f"Unsupported action '{action}'. Use one of {sorted(allowed)}"}
    vm = get_vm(name)
    if "error" in vm:
        return vm
    mapping = {"on": "poweredOn", "off": "poweredOff", "reset": "poweredOn", "suspend": "suspended"}
    return {
        "vm": vm["name"],
        "requested_action": action,
        "simulated_state": mapping[action],
        "note": "Mock vCenter — no live hypervisor was contacted.",
    }


def list_clusters() -> dict[str, Any]:
    data = _load()
    return {
        "vcenter": data["vcenter"]["clusters"],
        "nutanix": data["nutanix"]["clusters"],
    }


def nutanix_alerts(severity: str | None = None) -> dict[str, Any]:
    alerts = _load()["nutanix"]["alerts"]
    if severity:
        alerts = [a for a in alerts if a["severity"].lower() == severity.lower()]
    return {"count": len(alerts), "alerts": alerts}


def nutanix_capacity() -> dict[str, Any]:
    return _load()["nutanix"]["capacity"]


TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "list_vms",
            "description": "List mock vCenter virtual machines. Filter by cluster or power_state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster": {"type": "string"},
                    "power_state": {
                        "type": "string",
                        "enum": ["poweredOn", "poweredOff", "suspended"],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vm",
            "description": "Get a mock vCenter VM by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "power_action",
            "description": "Simulate a vCenter power operation on a VM (on/off/reset/suspend).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "action": {"type": "string", "enum": ["on", "off", "reset", "suspend"]},
                },
                "required": ["name", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_clusters",
            "description": "List mock vCenter and Nutanix clusters.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nutanix_alerts",
            "description": "List mock Nutanix Prism alerts, optionally by severity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["info", "warning", "critical"]}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nutanix_capacity",
            "description": "Return mock Nutanix cluster CPU, memory, and storage utilization.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "list_vms": list_vms,
    "get_vm": get_vm,
    "power_action": power_action,
    "list_clusters": list_clusters,
    "nutanix_alerts": nutanix_alerts,
    "nutanix_capacity": nutanix_capacity,
}


def run_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    handler = HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool '{name}'"}
    return handler(**(arguments or {}))
