from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import imaplib
import os
import smtplib


@dataclass(frozen=True)
class EmailConfig:
    smtp_host: str = ""
    smtp_port: int = 587
    imap_host: str = ""
    imap_port: int = 993
    username: str = ""
    app_password: str = ""
    sender: str = ""

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            smtp_host=os.getenv("EMAIL_SMTP_HOST", ""),
            smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
            imap_host=os.getenv("EMAIL_IMAP_HOST", ""),
            imap_port=int(os.getenv("EMAIL_IMAP_PORT", "993")),
            username=os.getenv("EMAIL_USERNAME", ""),
            app_password=os.getenv("EMAIL_APP_PASSWORD", ""),
            sender=os.getenv("EMAIL_SENDER", os.getenv("EMAIL_USERNAME", "")),
        )

    def can_send(self) -> bool:
        return bool(self.smtp_host and self.username and self.app_password and self.sender)

    def can_receive(self) -> bool:
        return bool(self.imap_host and self.username and self.app_password)


class EmailGateway:
    def __init__(self, config: EmailConfig | None = None):
        self.config = config or EmailConfig.from_env()

    def send_email(self, *, to: str, subject: str, body: str) -> None:
        if not self.config.can_send():
            raise RuntimeError("Config email incompleta: EMAIL_SMTP_HOST, EMAIL_USERNAME, EMAIL_APP_PASSWORD, EMAIL_SENDER.")
        message = EmailMessage()
        message["From"] = self.config.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=60) as smtp:
            smtp.starttls()
            smtp.login(self.config.username, self.config.app_password)
            smtp.send_message(message)

    def fetch_unread_subjects(self, limit: int = 10) -> list[str]:
        if not self.config.can_receive():
            raise RuntimeError("Config email incompleta: EMAIL_IMAP_HOST, EMAIL_USERNAME, EMAIL_APP_PASSWORD.")
        with imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port) as imap:
            imap.login(self.config.username, self.config.app_password)
            imap.select("INBOX")
            _status, data = imap.search(None, "UNSEEN")
            ids = data[0].split()[-limit:]
            subjects: list[str] = []
            for msg_id in ids:
                _status, msg_data = imap.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (SUBJECT)])")
                raw = msg_data[0][1].decode("utf-8", errors="replace") if msg_data and msg_data[0] else ""
                subjects.append(raw.strip())
            return subjects
