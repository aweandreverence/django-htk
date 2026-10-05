# Native authentication tests

Isolated SQLite ORM and HTTP tests; no production settings or external accounts.
Expose the checkout as `htk` on PYTHONPATH, install Django, then run:
`python -m django test htk.apps.native_auth.tests --settings=htk.apps.native_auth.tests.settings`.
Covers two independent client configurations using one credential store, consent,
CSRF, redirect/PKCE binding, rotation/revocation and account invalidation. Consumer
repos additionally verify their real database router and existing API contract.
