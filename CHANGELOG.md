# Changelog

All notable changes to DevGuard AI are documented here.

## [0.2.0] - 2026-10-05

### Added

- Discord webhook integration using Discord embeds
- Automatic incident notifications from the \`scan\` command
- Configurable minimum Discord severity: INFO, WARNING, or CRITICAL
- Optional Discord user/role mentions
- \`discord-test\` CLI command for webhook connectivity checks
- Environment-based Discord configuration
- Unit tests for Discord filtering and webhook payloads

### Security

- Discord webhook URLs are accepted only for official Discord webhook endpoints
- Webhook secrets are not stored in repository configuration

## [0.1.0] - 2026-09-30

### Added

- Local log analyzer
- HTTP 5xx detection
- Authentication failure detection
- Runtime crash detection
- Network timeout and connection detection
- Filesystem permission detection
- Application error detection
- Severity classification
- JSON output
- Optional OpenAI-compatible LLM summaries
- CLI interface
- Unit tests
- GitHub Actions CI
- Project documentation
