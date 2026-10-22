from __future__ import annotations

import json
import re
from typing import Any

from app.config import settings
from app.rag import index
from app.schemas import ChatMessage, ChatResponse, Source, ToolCall
from app.tools import TOOL_SPECS, run_tool

SYSTEM = """You are InfraGPT, an infra-ops assistant.
Use retrieved runbooks and tool results. Never invent live cluster state.
If a tool was used, cite the mock result. If you are unsure, say so.
All vCenter / Nutanix data in this project is simulated.
"""


def _wants_tools(message: str) -> list[tuple[str, dict[str, Any]]]:
    q = message.lower()
    calls: list[tuple[str, dict[str, Any]]] = []
    if any(w in q for w in ("list vm", "list vms", "show vm", "which vm", "powered")):
        args: dict[str, Any] = {}
        if "off" in q:
            args["power_state"] = "poweredOff"
        elif "suspend" in q:
            args["power_state"] = "suspended"
        elif "on" in q and "power" in q:
            args["power_state"] = "poweredOn"
        for cluster in ("prod-west-01", "prod-east-01", "lab-shared"):
            if cluster in q:
                args["cluster"] = cluster
        calls.append(("list_vms", args))
    vm_names = [
        "payments-api-01",
        "payments-api-02",
        "checkout-web-01",
        "batch-etl-01",
        "jump-lab-01",
    ]
    named = next((n for n in vm_names if n in q), None)
    if named and any(w in q for w in ("power", "reset", "reboot", "shutdown", "start", "stop")):
        action = "reset" if any(w in q for w in ("reset", "reboot")) else "on"
        if any(w in q for w in ("off", "shutdown", "stop")):
            action = "off"
        if "suspend" in q:
            action = "suspend"
        calls.append(("get_vm", {"name": named}))
        calls.append(("power_action", {"name": named, "action": action}))
    elif named:
        calls.append(("get_vm", {"name": named}))
    if "cluster" in q:
        calls.append(("list_clusters", {}))
    if "alert" in q or "prism" in q and "disk" in q:
        args = {}
        if "critical" in q:
            args["severity"] = "critical"
        calls.append(("nutanix_alerts", args))
    if any(w in q for w in ("capacity", "storage", "cpu", "memory utilization")):
        calls.append(("nutanix_capacity", {}))
    # de-dupe by name keeping first args
    seen: dict[str, dict[str, Any]] = {}
    for name, args in calls:
        seen.setdefault(name, args)
    return list(seen.items())


def _offline_answer(message: str, sources: list[Source], tool_calls: list[ToolCall]) -> str:
    bits: list[str] = []
    if tool_calls:
        bits.append("Mock infra tools were called (no live hypervisor):")
        for call in tool_calls:
            bits.append(f"- `{call.name}` → `{json.dumps(call.result)[:500]}`")
    if sources:
        bits.append("From the runbooks:")
        for src in sources[:3]:
            bits.append(f"- **{src.title}**: {src.snippet[:220]}")
    if not bits:
        bits.append(
            "I can look up mock vCenter VMs, Nutanix alerts/capacity, and infra runbooks. "
            "Try: 'list powered-off VMs' or 'what is the disk failure runbook?'."
        )
    bits.append("\nOffline mock LLM is answering because no API key is configured.")
    return "\n".join(bits)


def _openai_chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.1,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return client.chat.completions.create(**kwargs).model_dump()


def chat(message: str, history: list[ChatMessage] | None = None) -> ChatResponse:
    sources = index.search(message, k=4)
    context = index.context_block(sources)
    history = history or []

    if not settings.openai_api_key:
        planned = _wants_tools(message)
        tool_calls = [
            ToolCall(name=name, arguments=args, result=run_tool(name, args)) for name, args in planned
        ]
        return ChatResponse(
            answer=_offline_answer(message, sources, tool_calls),
            sources=sources,
            tool_calls=tool_calls,
            model="mock-offline",
        )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "system",
            "content": f"Retrieved runbooks:\n{context}",
        },
    ]
    for item in history[-8:]:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": message})

    first = _openai_chat(messages, TOOL_SPECS)
    choice = first["choices"][0]["message"]
    tool_calls: list[ToolCall] = []
    api_tools = choice.get("tool_calls") or []
    if api_tools:
        messages.append(choice)
        for tc in api_tools:
            name = tc["function"]["name"]
            raw_args = tc["function"].get("arguments") or "{}"
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}
            result = run_tool(name, args)
            tool_calls.append(ToolCall(name=name, arguments=args, result=result))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": name,
                    "content": json.dumps(result),
                }
            )
        second = _openai_chat(messages)
        answer = second["choices"][0]["message"]["content"] or ""
        model = settings.llm_model
    else:
        answer = choice.get("content") or ""
        model = settings.llm_model

    answer = re.sub(r"\n{3,}", "\n\n", answer).strip()
    return ChatResponse(answer=answer, sources=sources, tool_calls=tool_calls, model=model)
