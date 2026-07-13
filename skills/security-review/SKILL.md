---
name: security-review
license: LICENSE
description: Security code review for vulnerabilities. Use when asked to "security review", "find vulnerabilities", "check for security issues", "audit security", "OWASP review", review code for injection, XSS, authentication, authorization, or cryptography issues. Also use when the user asks you to "look at this code" or "check this endpoint" in a security context, when reviewing PRs that touch auth/crypto/input-handling code, or when the user pastes code and asks "is this safe?" or "anything wrong with this?". Provides systematic review with confidence-based reporting.
---

# Security Review

Find exploitable security vulnerabilities in code. Report only **HIGH CONFIDENCE** vulnerabilities as findings. Put medium-confidence candidates in **Needs Verification** with a specific verification step. Skip theoretical issues.

## 1. Scope the Review

- **Specific file or diff:** review that artifact only. Research the broader codebase for context, but only report findings within scope.
- **Broad target** ("review the auth system", "audit this repo"): prioritize highest-risk entry points (auth flows, mutation endpoints, external input parsers, admin functionality). Propose a review order to the user before diving in.
- **Scope too large:** say so and propose a narrower focus.

## 2. Research Before Flagging

**CRITICAL: Do not report issues based on pattern matching.** For every potential finding, research the codebase:

1. **Trace the data flow.** Where does this input actually come from? Follow it from entry point to the suspect code.
2. **Check for upstream validation.** Is there middleware, decorators, schema validation (Zod, Pydantic), or sanitization libraries (DOMPurify, bleach) between the input source and the vulnerable code?
3. **Check framework protections.** Does the framework auto-escape, parameterize, or otherwise mitigate this? (See framework-specific sections below.)
4. **Check configuration.** Is this value from `settings`, `os.environ`, config files, or hardcoded constants? If so, it's server-controlled, not attacker-controlled.
5. **Verify the auth chain.** For endpoints, trace the middleware/decorator chain to confirm whether authentication and authorization are actually enforced, not just assumed.

## 3. Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **HIGH** | Vulnerable pattern + attacker-controlled input confirmed through data flow tracing | **Report** with full finding format |
| **MEDIUM** | Vulnerable pattern confirmed, but input source unclear after research | **Report** in "Needs Verification" section with a specific verification step |
| **LOW** | Theoretical, best practice, defense-in-depth | **Do not report** |

## 4. Do Not Flag

### General Rules
- Test files (unless explicitly reviewing test security)
- Dead code, commented code, documentation strings
- Patterns using constants or server-controlled configuration
- Authentication changes reachability, not safety. Confirm the required privilege and adjust severity or attack preconditions accordingly. Still report exploitable authorization gaps, privilege escalation, cross-tenant access, and vulnerabilities reachable by ordinary authenticated users.

### Server-Controlled Values (NOT Attacker-Controlled)

These are configured by operators, not controlled by attackers. **Never flag these as vulnerabilities:**

| Source | Examples |
|--------|---------|
| Framework settings | `settings.API_URL`, `settings.ALLOWED_HOSTS`, `app.config['KEY']` |
| Environment variables | `os.environ.get('DATABASE_URL')`, `process.env.API_KEY` |
| Config files | `config.yaml`, `.toml`, JSON config loaded at startup |
| Hardcoded constants | `BASE_URL = "https://api.internal"`, `const TIMEOUT = 30` |

```python
# SAFE: URL from Django settings (server-controlled)
response = requests.get(f"{settings.SEER_AUTOFIX_URL}{path}")

# VULNERABLE: URL from request (attacker-controlled)
response = requests.get(request.GET.get('url'))
```

### Attacker-Controlled Input Sources

These ARE worth investigating when they flow into sensitive operations:

| Source | Examples |
|--------|---------|
| Request parameters | `request.GET`, `request.POST`, `req.query`, `req.body`, `req.params` |
| Request headers | Most headers (especially `Host`, `X-Forwarded-For`, custom headers) |
| Cookies | Unsigned cookies, JWT without verification |
| URL path segments | `/users/<id>/`, route params |
| File uploads | Content AND filenames |
| Database content from other users | Stored XSS vector |
| WebSocket messages | Client-controlled real-time data |

### Framework Auto-Protections (Check Before Flagging)

| Pattern | Why It's Usually Safe | Flag ONLY When |
|---------|----------------------|----------------|
| Django `{{ variable }}` | Auto-escaped | `{{ var\|safe }}`, `{% autoescape off %}`, `mark_safe(user_input)` |
| React `{variable}` | Auto-escaped | `dangerouslySetInnerHTML={{__html: userInput}}` |
| Vue `{{ variable }}` | Auto-escaped | `v-html="userInput"` |
| Angular `{{ variable }}` | Auto-escaped + DomSanitizer | `bypassSecurityTrustHtml(userInput)` |
| `User.objects.filter(id=input)` | ORM parameterizes | `.raw()`, `.extra()`, `RawSQL()` with string interpolation |
| `cursor.execute("...%s", (input,))` | Parameterized query | `cursor.execute(f"...{input}")` (string interpolation) |
| `innerHTML = "<b>Loading...</b>"` | Constant string | `innerHTML = userInput` |
| `elem.textContent = userInput` | Text-only, no XSS | Never (this is always safe) |

---

## Vulnerability Patterns

For detailed vulnerability patterns by language, framework, and domain, see [references/vulnerability-patterns.md](references/vulnerability-patterns.md). Covers: critical/high/context-dependent patterns, Python/Django/Flask/FastAPI, JavaScript/TypeScript/React/Express/Next.js, Docker/Infrastructure, AI/LLM prompt injection, concurrency/race conditions, and auth flow verification.

---

## Severity Classification

| Severity | Criteria | Examples |
|----------|----------|---------|
| **Critical** | Direct exploit, severe impact, no/low auth required | RCE, SQLi to data exfil, auth bypass, deserialization, hardcoded prod secrets |
| **High** | Exploitable with conditions, significant impact | Stored XSS, SSRF to cloud metadata, IDOR to sensitive data, privilege escalation |
| **Medium** | Specific conditions required, moderate impact | Reflected XSS, CSRF on state-changing actions, path traversal (limited scope) |
| **Low** | Defense-in-depth, minimal direct impact | Missing headers, verbose errors, weak crypto in non-critical context |

---

## Output Format

### Full Review (multiple files or broad scope)

Headed `## Security Review: [Component]`. Include:
- **Summary**: scope reviewed, findings count by severity, overall risk level.
- **Findings**: one `#### [VULN-NNN] <Type> (<Severity>)` per finding, each with **Location**, **Confidence: High**, **Issue**, **Attack scenario**, **Evidence** (code block), **Fix** (code block).
- **Needs Verification**: same structure with `[VERIFY-NNN]` and a **Verification step** line explaining the specific check needed.

### Quick Check (single function or small snippet)

Skip the formal template. Report findings inline with the same severity/confidence/evidence structure, conversationally. Example:

> `utils.py:42` -- **High: SQL injection.** The `user_id` from `request.args` flows directly into an f-string query. Use parameterized query: `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))`.

### No Findings

State: "No high-confidence vulnerabilities identified in [scope]. Reviewed [N files/functions] covering [what was checked]."

## Attribution

Adapted from [Sentry's security-review skill](https://github.com/getsentry/skills/tree/main/skills/security-review) and the [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/). License: [CC BY-SA 4.0](LICENSE).
