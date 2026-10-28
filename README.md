# SecureShop | Red Team Application Security Assignment

A small fictional e-commerce lab for the assignment's build, attack, identify, fix and retest workflow. The starter runs in intentionally vulnerable mode; a secure profile demonstrates remediation. **Use only on your own machine at `127.0.0.1:8080`. Never expose it to a LAN or the public internet.**

## Run the vulnerable lab

Requires Python 3.10+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8080`. Demo accounts: `alice / alice123`, `bob / bob123`, `admin / admin123`. These are disposable lab credentials. To reset the database, stop the app and delete `secureshop.db`; it is recreated on launch.

## Lab findings and fixes

| Issue | Safe local validation | Fix in secure mode | OWASP Top 10:2021 |
|---|---|---|---|
| SQL injection | Search `/products?q=' OR 1=1 --` | Parameterized query | A03 Injection |
| IDOR | Sign in as Alice; request `/orders?user_id=2` to view Bob's seeded order | Determine owner from session; ignore supplied user ID | A01 Broken Access Control |
| Plaintext passwords | Inspect only the local demo database | Werkzeug password hashing | A02 Cryptographic Failures / A07 Identification and Authentication Failures |
| Missing response headers | Compare vulnerable and secure HTTP responses | CSP, frame, MIME and referrer protections | A05 Security Misconfiguration |
| Outdated Flask dependency | Flask 2.2.2 in starter requirements | Upgrade to Flask 3.1.3 in `requirements-secure.txt` | A06 Vulnerable and Outdated Components |

The weaknesses are deliberately limited to a local seeded database. Flask debug mode is off and the app always binds to loopback.

## Remediation run

1. Stop the app and delete `secureshop.db` so the accounts are recreated with password hashes.
2. Install the updated dependency: `python -m pip install -r requirements-secure.txt`.
3. Start secure mode:

```powershell
$env:SECURE_MODE='1'
$env:SECRET_KEY='replace-with-a-random-local-lab-value'
python app.py
```

4. Retest: the search string should not alter the query, Alice should not see Bob's order, security headers should be present, and account passwords should be hashes. Reset the DB again before switching back to vulnerable mode.

## OWASP ZAP scan

Use ZAP Manual Explore against `http://127.0.0.1:8080`, then spider/passive scan. Run active scan only against this local app you own. Save the report before and after remediation using the same settings. Authenticated crawling requires configuring a ZAP context/user. Scanner output is evidence to investigate; it may not detect the manually demonstrated SQL injection or IDOR.

### Record actual results

| Field | Before remediation | After remediation |
|---|---|---|
| Scan date / ZAP version | _record from your run_ | _record from your run_ |
| Target / scan type | `http://127.0.0.1:8080` / _actual type_ | same / _actual type_ |
| Alert counts by severity | _from ZAP report_ | _from ZAP report_ |
| Manual validation | _request and observed result_ | _retest and observed result_ |
| Evidence | _ZAP report / screenshots_ | _ZAP report / screenshots_ |

## Outdated dependency note

Flask 2.2.2 is intentionally pinned as the outdated component. Flask's release notes identify CVE-2023-30861 and list 2.2.5 as the 2.2.x security fix. The release page lists 3.1.3 as current (checked 2026-10-28). Verify advisory status again at submission time. References: [Flask releases](https://github.com/pallets/flask/releases), [OWASP Top 10:2021](https://owasp.org/Top10/).

