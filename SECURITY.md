# Security Policy

## Supported versions

Security updates are applied to the default branch (`main`) of this repository. There are no separate long-term support (LTS) release branches unless documented elsewhere in this project.

## Reporting a vulnerability

If you believe you have found a security issue in this project, please **do not** open a public GitHub issue.

Instead, report it privately so we can assess and fix it responsibly:

1. **Preferred:** Use [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) for this repository (if enabled), or  
2. **Email:** Contact the repository maintainers through a channel they have published for security contact (if any). If none is listed, open a **private** discussion with maintainers only if your platform supports it.

Include:

- A clear description of the issue and its impact  
- Steps to reproduce (or a proof-of-concept) if safe to share  
- Affected versions or commit range, if known  

We will acknowledge receipt when possible and work on a fix and disclosure timeline.

## Scope

This policy applies to the code in this repository. Third-party services (e.g. cloud LLM APIs, hosted CI, external sites you test against) are governed by their own providers’ policies.

## Safe usage reminders

- **Secrets:** Do not commit API keys (OpenAI, Anthropic, etc.). Use environment variables (see `README.md`) and keep `.env` out of version control (see `.gitignore`).  
- **Generated output:** Artifacts under `output/` may contain URLs or selectors from your runs; review before sharing.  
- **Dependencies:** Run `uv sync` / keep lockfiles updated; review updates for supply-chain risk as you would for any Python project.
