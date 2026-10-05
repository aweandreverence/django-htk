# Native authentication tests

Isolated SQLite ORM and HTTP tests; no production settings or external accounts.
Expose the checkout as `htk` on PYTHONPATH, install Django, then run:
`python -m django test htk.apps.native_auth.tests --settings=htk.apps.native_auth.tests.settings`.
Covers two independent client configurations using one credential store, consent,
CSRF, redirect/PKCE binding, rotation/revocation and account invalidation. Consumer
repos additionally verify their real database router and existing API contract.

Consent tests include HTTPS same-origin approval/cancellation and rejection of
null/untrusted origins with valid CSRF tokens. A consumer real-browser check is
still required to verify the browser-generated Origin and native callback.
