import json
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict

class AccessMethod(BaseModel):
    operation: str  # read, extract, create, modify, preserve, verify
    format: str     # family: text, office_modern, pdf, etc.
    support: str    # unsupported, prepared, direct

class Capability(BaseModel):
    id: str
    name: str
    description: str

class ToolEntry(BaseModel):
    tool_name: str
    capabilities: List[str]
    access_methods: List[AccessMethod]

class CapabilityCatalog(BaseModel):
    version: str = "2.2.0"
    capabilities: List[Capability]
    tools: List[ToolEntry]

def create_default_catalog() -> CapabilityCatalog:
    """
    Retorna el catálogo base según las 17 capacidades puntuables exigidas en Agent 2.2.
    """
    caps = [
        Capability(id="cap_extract_short", name="extracción puntual en texto corto", description=""),
        Capability(id="cap_extract_long", name="extracción puntual en documento largo", description=""),
        Capability(id="cap_extract_cross", name="extracción cruzada en varios documentos", description=""),
        Capability(id="cap_synth_long", name="síntesis de texto largo", description=""),
        Capability(id="cap_synth_multi", name="síntesis de varios documentos", description=""),
        Capability(id="cap_compare", name="comparación de datos o documentos", description=""),
        Capability(id="cap_calc_filter", name="cálculo y filtrado estructurado", description=""),
        Capability(id="cap_transform_redact", name="transformación y redacción con datos", description=""),
        Capability(id="cap_web_punctual", name="búsqueda web puntual", description=""),
        Capability(id="cap_web_multi", name="búsqueda web multifactor", description=""),
        Capability(id="cap_investigate", name="investigación y criterio multifuente", description=""),
        Capability(id="cap_read_pdf_bin", name="lectura de PDF y documentos binarios", description=""),
        Capability(id="cap_read_visual", name="lectura visual y OCR", description=""),
        Capability(id="cap_inspect_zip", name="inspección de carpetas y archivos comprimidos", description=""),
        Capability(id="cap_create_modify", name="creación o modificación de archivos", description=""),
        Capability(id="cap_exec_tech", name="ejecución técnica y diagnóstico", description=""),
        Capability(id="cap_verify", name="verificación del resultado", description="")
    ]
    return CapabilityCatalog(capabilities=caps, tools=[])

def save_catalog(path: Path, catalog: CapabilityCatalog):
    path.write_text(catalog.model_dump_json(indent=2), encoding="utf-8")

def load_catalog(path: Path) -> CapabilityCatalog:
    return CapabilityCatalog.model_validate_json(path.read_text(encoding="utf-8"))
