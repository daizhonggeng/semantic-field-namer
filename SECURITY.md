# Security Policy

## Supported versions

This project currently supports the latest main branch. Release branches are not maintained yet.

## Reporting a vulnerability

Do not open public issues for security problems.

Report:

- Affected version or commit
- Reproduction steps
- Expected impact
- Any suggested mitigation

If the issue involves credentials, tokens, or production data, rotate them first and then report the sanitized details.

## Security expectations for contributors

- Never commit real API keys or tokens
- Never commit production datasets
- Keep example data synthetic or clearly public
- Treat third-party OpenAI-compatible gateways as untrusted by default
