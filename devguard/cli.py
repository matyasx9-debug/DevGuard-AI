import argparse
import json
import os
from .analyzer import analyze_file
from .llm import summarize
from .discord import DiscordConfig, send_findings, send_test

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="devguard",
        description="AI-assisted IT incident triage",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Analyze a log file")
    scan.add_argument("file")
    scan.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    scan.add_argument("--ai", action="store_true", help="Generate an optional AI summary")
    scan.add_argument("--discord", action="store_true", help="Send findings to Discord")
    scan.add_argument("--discord-webhook", help="Discord webhook URL; defaults to DISCORD_WEBHOOK_URL")
    scan.add_argument(
        "--discord-min-severity",
        choices=("INFO", "WARNING", "CRITICAL"),
        help="Minimum severity sent to Discord (default: WARNING)",
    )
    scan.add_argument("--discord-mention", help="Optional Discord user/role mention")

    discord = sub.add_parser("discord-test", help="Test the configured Discord webhook")
    discord.add_argument("--discord-webhook", help="Discord webhook URL; defaults to DISCORD_WEBHOOK_URL")
    discord.add_argument(
        "--discord-min-severity",
        choices=("INFO", "WARNING", "CRITICAL"),
        help="Minimum severity for the Discord integration",
    )
    discord.add_argument("--discord-mention", help="Optional Discord user/role mention")

    args = parser.parse_args()

    if args.command == "scan":
        content, findings = analyze_file(args.file)

        if args.json:
            print(json.dumps([f.__dict__ for f in findings], indent=2))
        else:
            if not findings:
                print("No known incident signals detected.")
            for item in findings:
                print(f"{item.severity:<8} {item.category:<10} line {item.line}: {item.message}")

        if args.ai:
            print("\n--- AI INCIDENT SUMMARY ---")
            print(summarize(findings, content))

        if args.discord:
            config = _discord_config(args)
            sent = send_findings(findings, source=args.file, config=config)
            print(f"\nDiscord: sent {sent} finding(s).")

    elif args.command == "discord-test":
        config = _discord_config(args)
        send_test(config)
        print("Discord: webhook test sent successfully.")

def _discord_config(args: argparse.Namespace) -> DiscordConfig:
    env = DiscordConfig.from_env()
    webhook = args.discord_webhook or (env.webhook_url if env else "")
    if not webhook:
        raise SystemExit("Discord webhook not configured. Set DISCORD_WEBHOOK_URL or pass --discord-webhook.")

    return DiscordConfig(
        webhook_url=webhook,
        min_severity=args.discord_min_severity or (env.min_severity if env else "WARNING"),
        mention=args.discord_mention if args.discord_mention is not None else (env.mention if env else ""),
    )

if __name__ == "__main__":
    main()
