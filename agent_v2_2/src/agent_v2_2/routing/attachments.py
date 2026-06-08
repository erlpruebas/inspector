from typing import List
from pathlib import Path
from ..models import Attachment

class AttachmentManager:
    """Gestiona archivos y adjuntos estructurados."""
    
    def process_incoming(self, files: List[Path]) -> List[Attachment]:
        # Convierte Paths en Attachments estructurados
        attachments = []
        for file in files:
            if not file.exists():
                continue
            attachments.append(Attachment(
                kind=self._determine_kind(file),
                path=file,
                label=file.name,
                source="user"
            ))
        return attachments

    def _determine_kind(self, file: Path) -> str:
        ext = file.suffix.lower()
        if ext in {'.jpg', '.png', '.jpeg'}: return "image"
        if ext in {'.mp3', '.wav', '.ogg'}: return "audio"
        if ext in {'.pdf', '.doc', '.docx'}: return "document"
        if ext in {'.py', '.js', '.ts', '.html'}: return "code"
        return "file"
