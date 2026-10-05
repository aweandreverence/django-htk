# Native credential schema

Opt-in `native_auth` migrations. Apply on the database selected for both grant
and session models. Consumers must explicitly target their configured credential
database rather than an unrelated domain database.
Regenerate with Django makemigrations using the isolated test settings. No data
from legacy product-local credential tables is migrated automatically.

The initial, unreleased schema uses the `native_auth` app label and default
`native_auth_mobilegrant` / `native_auth_mobilesession` table names. A preview
that applied the earlier prefixed label must reconcile its migration history and
credential tables before upgrading; this change does not rename existing tables
or transfer sessions automatically. Do not apply it blindly to an existing store.
