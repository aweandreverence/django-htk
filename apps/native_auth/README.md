# Native browser authentication

Opt-in Django app providing reusable, client-scoped S256 PKCE browser consent,
single-use grants, hashed bearer/refresh credentials, rotation and device logout.
No Bible, A&R, Expo, Accounts-provider, or product-domain dependencies. Python
3.12+, Django 4.2+; portable clients can use a different account login provider.

## Adopt

1. Add `htk.apps.native_auth` to INSTALLED_APPS. Its Django app label is
   `native_auth`, consistent with the unprefixed labels of other HTK apps.
   Route `native_auth` to one
   credential database and apply its migrations there. Grant/session writes must
   use the same connection; account lookups honor the user model's router.
2. Construct a `NativeClient(client_id=..., redirect_uri=..., app_name=...,
   login_url_name=..., consent_description=...)` from trusted server settings.
   Callback is exact: HTTPS or a private scheme, no query/fragment/userinfo.
3. Construct `NativeAuthService(client)` and use `build_views(factory)` from
   `views.py`. Include the resulting `authorize`, `token`, `logout` functions at
   product-selected paths. The login route must honor a safe local `next` return.
4. Protect business APIs using the same service's `authenticate(Authorization)`.
   Cookie/query-token authentication is intentionally unsupported there.

Native client contract: open authorize with client_id, redirect_uri,
code_challenge_method=S256, challenge and 256-bit state; validate returned state
and exact callback; exchange the code plus verifier by POST JSON. Store returned
credentials in OS secure storage, refresh on expiry, revoke on logout. Do not
put bearer/refresh credentials in URLs, logs or browser localStorage. Device
credential storage and browser-return handling remain client responsibilities.

Each product must have a unique client_id even when it shares the same credential
store. Every issue/exchange/read/refresh/revoke binds that audience. Codes also
bind the exact redirect; another app cannot consume them or revoke its sibling's
session. This provides authentication, not business authorization: ownership,
roles, resource permissions and scopes belong in the consumer's domain layer.
It is not advertised as a full OAuth/OIDC authorization server.

## Structure and boundaries

- `config.py`: validated immutable client policy and credential lifetimes.
- `models/`, `migrations/`: opt-in persistence, with no automatic migrations.
- `services.py`: protocol/credential operations; no HTTP or product imports.
- `views.py`: CSRF-protected consent, exact callback, bounded JSON token/logout.
- `tests/`: real ORM/HTTP tests and two-client isolation; see its README.
- `htk.api.http`: reusable private JSON responses and bounded string-body parser.
- `htk.utils.db.atomic_for`: transaction decorator using a model's write router.

Default lifetimes: grant 2 minutes, access 15 minutes, absolute session 30 days.
Password changes, account disablement/removal and device logout invalidate access.
Only digests are stored; expired rows may be purged by the consumer's maintenance
process. Deleting Accounts data and downstream personal data is a coordinated
consumer operation, not a cross-database cascade promised by this package.

SPEAR review rubric: protocol/cross-client isolation; storage/transaction and
migration correctness; consumer compatibility; consent/privacy; reproducible
verification. No hosted identity provider or physical-device behavior is certified
by the isolated SQLite suite. Keep production/MySQL and client acceptance explicit.

Provenance: extracted from the reviewed Awesome.Bible native handoff into generic
HTK APIs; governed by this repository's license. No production credentials/data.
