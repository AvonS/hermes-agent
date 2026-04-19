# Security Dependencies

Minimum safe versions for known vulnerabilities. Update this file when new CVEs are disclosed.

| Package | CVE | Affected | Safe Version |
|---------|-----|----------|--------------|
| protobufjs | CVE-2022-25878, CVE-2018-3738 | <7.2.5, <6.11.3 | >=7.2.5 |
| lodash | CVE-2026-4800, CVE-2026-2950 | <4.18.1 | >=4.18.1 |
| lodash-es | CVE-2026-4800, CVE-2026-2950 | <4.18.0 | >=4.18.0 |
| serialize-javascript | (check npm) | <=7.0.2 | >=7.0.3 |

## Checking

Run the security check:

```bash
scripts/check_security_deps.sh
```

This script verifies installed versions meet the minimums above.