from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .catalog import CapabilityCatalog, create_default_catalog


@dataclass
class IntrospectionAnswer:
    title: str
    body: str


class IntrospectionManager:
    """Responde preguntas sobre capacidades y herramientas disponibles."""

    def __init__(self, catalog: Optional[CapabilityCatalog] = None) -> None:
        self.catalog = catalog or create_default_catalog()

    def list_capabilities(self) -> IntrospectionAnswer:
        lines = [f"{len(self.catalog.capabilities)} capacidades disponibles:"]
        for capability in self.catalog.capabilities:
            lines.append(f"- {capability.id}: {capability.name}")
        return IntrospectionAnswer(
            title="capacidades",
            body="\n".join(lines),
        )

    def describe_tool(self, tool_name: str) -> IntrospectionAnswer:
        matches = [tool for tool in self.catalog.tools if tool.tool_name.casefold() == tool_name.casefold()]
        if not matches:
            return IntrospectionAnswer(
                title=tool_name,
                body=f"No tengo todavía una herramienta registrada con el nombre {tool_name}.",
            )

        lines = [f"Herramienta: {tool_name}"]
        for tool in matches:
            caps = ", ".join(tool.capabilities) if tool.capabilities else "sin capacidades declaradas"
            lines.append(f"- capacidades: {caps}")
            for method in tool.access_methods:
                lines.append(f"- {method.operation} / {method.format}: {method.support}")
        return IntrospectionAnswer(title=tool_name, body="\n".join(lines))

    def answer_question(self, question: str) -> IntrospectionAnswer:
        lower = question.casefold().strip()
        if any(keyword in lower for keyword in ("capacidad", "capacidades", "qué puede", "que puede")):
            return self.list_capabilities()
        if "herramienta" in lower or "tool" in lower:
            for tool in self.catalog.tools:
                if tool.tool_name.casefold() in lower:
                    return self.describe_tool(tool.tool_name)
            return IntrospectionAnswer(
                title="herramientas",
                body="Puedo describir herramientas registradas, pero todavía necesito el nombre exacto de la herramienta.",
            )
        return IntrospectionAnswer(
            title="intención",
            body="Puedo explicar capacidades y herramientas registradas, pero necesito una pregunta más concreta.",
        )
