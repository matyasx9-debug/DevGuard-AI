from unittest.mock import patch

import pytest

from devguard.discord import DiscordConfig, send_findings, send_test
from devguard.rules import Finding

def test_discord_config_rejects_non_discord_webhook():
    with pytest.raises(ValueError):
        send_test(DiscordConfig("https://example.com/webhook"))

def test_send_findings_filters_by_severity():
    findings = [
        Finding("WARNING", "network", "timeout", 2),
        Finding("CRITICAL", "runtime", "panic", 4),
    ]
    with patch("devguard.discord.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.status = 204
        sent = send_findings(
            findings,
            source="example.log",
            config=DiscordConfig("https://discord.com/api/webhooks/123/token"),
        )
    assert sent == 2
    request = urlopen.call_args.args[0]
    assert request.full_url.startswith("https://discord.com/api/webhooks/")
    assert b"DevGuard AI incident report" in request.data

def test_send_findings_sends_nothing_when_below_threshold():
    finding = Finding("WARNING", "network", "timeout", 2)
    with patch("devguard.discord.urlopen") as urlopen:
        sent = send_findings(
            [finding],
            config=DiscordConfig(
                "https://discord.com/api/webhooks/123/token",
                min_severity="CRITICAL",
            ),
        )
    assert sent == 0
    urlopen.assert_not_called()
