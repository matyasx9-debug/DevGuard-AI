"""Discord webhook integration for DevGuard AI."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .rules import Finding

_SEVERITY_RANK = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}

@dataclass(frozen=True)
class DiscordConfig:
    webhook_url: str
    min_severity: str = "WARNING"
    mention: str = ""

    @classmethod
    def from_env(cls) -> "DiscordConfig | None":
        url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        if not url:
            return None
        return cls(
            webhook_url=url,
            min_severity=os.getenv("DEVGUARD_DISCORD_MIN_SEVERITY", "WARNING").upper(),
            mention=os.getenv("DEVGUARD_DISCORD_MENTION", "").strip(),
        )

def _validate_config(config: DiscordConfig) -> None:
    if not config.webhook_url.startswith(("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")):
        raise ValueError("Discord webhook URL must use the official Discord webhook endpoint.")
    if config.min_severity not in _SEVERITY_RANK:
        raise ValueError("min_severity must be INFO, WARNING, or CRITICAL.")

def send_findings(findings: Sequence[Finding], *, source: str = "DevGuard AI",
                  config: DiscordConfig, timeout: float = 10.0) -> int:
    _validate_config(config)
    threshold = _SEVERITY_RANK[config.min_severity]
    selected = [f for f in findings if _SEVERITY_RANK.get(f.severity, 0) >= threshold]
    if not selected:
        return 0
    counts = {severity: 0 for severity in _SEVERITY_RANK}
    for finding in selected:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    lines = [
        f"**{f.severity}** · {f.category} · line {f.line}\n{f.message}"
        for f in selected[:15]
    ]
    if len(selected) > 15:
        lines.append(f"*…and {len(selected) - 15} more findings.*")
    payload = {
        "content": config.mention or None,
        "embeds": [{
            "title": "🚨 DevGuard AI incident report",
            "description": "\n\n".join(lines),
            "fields": [
                {"name": "Source", "value": source[:1024], "inline": True},
                {"name": "Critical", "value": str(counts.get("CRITICAL", 0)), "inline": True},
                {"name": "Warnings", "value": str(counts.get("WARNING", 0)), "inline": True},
            ],
            "footer": {"text": "DevGuard AI"},
        }],
        "allowed_mentions": {"parse": ["users", "roles"] if config.mention else []},
    }
    return _post(config.webhook_url, payload, timeout)

def send_test(config: DiscordConfig, *, timeout: float = 10.0) -> None:
    _validate_config(config)
    _post(config.webhook_url, {
        "content": "✅ DevGuard AI Discord integration is working.",
        "allowed_mentions": {"parse": []},
    }, timeout)

def _post(url: str, payload: dict, timeout: float) -> int:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "DevGuard-AI/0.2.0"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status not in (200, 204):
                raise RuntimeError(f"Discord webhook returned HTTP {response.status}")
    except HTTPError as exc:
        raise RuntimeError(f"Discord webhook returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Discord webhook: {exc.reason}") from exc
    return 1
