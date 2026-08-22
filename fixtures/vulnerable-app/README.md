# ⚠️ INTENTIONALLY VULNERABLE FIXTURE — DO NOT DEPLOY

This directory exists **only** as a test fixture for a security-scanning pipeline
(GitHub Advisory Database / Dependabot / CodeQL / secret scanning).

Every file here is deliberately insecure. It is not imported by `src/redthread`,
is not on any runtime path, and must never be packaged, deployed, or executed
outside a throwaway sandbox.

## What is planted here

### 1. Dependency advisories (GHSA / Dependabot)
`requirements.txt` pins packages to versions with published advisories:

| Package | Pinned | Advisory | CVE |
|---|---|---|---|
| PyYAML | 5.3.1 | GHSA-8q59-q68h-6hv4 | CVE-2020-14343 |
| Jinja2 | 2.10 | GHSA-462w-v97r-4m45 | CVE-2019-10906 |
| requests | 2.19.1 | GHSA-x84v-xcm2-53pg | CVE-2018-18074 |
| urllib3 | 1.24.1 | GHSA-mh33-7rrq-662w | CVE-2019-11324 |
| Flask | 0.12.2 | GHSA-5wv5-4vpf-pj6m | CVE-2018-1000656 |
| Pillow | 8.1.0 | GHSA-8vj2-vgrf-5rv6 | CVE-2021-25287 |
| cryptography | 3.3.2 | GHSA-x4qr-2fvf-3mr5 | CVE-2023-23931 |

`package.json` does the same for the npm ecosystem (lodash prototype pollution,
minimist argument injection).

### 2. Source-level weaknesses (CodeQL / Semgrep)
`app.py` contains SQL injection, OS command injection, unsafe YAML and pickle
deserialization, SSTI, path traversal, SSRF, a weak hash, disabled TLS
verification, and a hardcoded credential. Each is annotated inline with the
secure approach that would have been used in real code.

## Expected pipeline behaviour
Opening this branch as a PR should produce Dependabot alerts for the manifests
above and code-scanning alerts for `app.py`. The follow-up "fix" PR reverses
all of it, giving the introducing-commit / fixing-commit pair used to exercise
advisory-to-commit correlation.
