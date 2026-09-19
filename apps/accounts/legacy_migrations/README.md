# Optional legacy account schema baseline

This source migration history covers the existing `accounts.UserAttribute` and
`accounts.UserEmail` models. Their labels, table names, public imports, signals
and runtime behavior are unchanged. The module is opt-in, not a new default
`accounts/migrations/` directory. It does not own auth users, product profiles,
legacy feedback or other account-service models.

## Scope and selection

First review actual table locations, migration records and backups. Do not
create empty replacements beside existing data on another database, replace
an unrelated app's `accounts` migration graph, or assume a missing recorder
proves the tables are absent. No discovery/transfer/reconciliation is automated.

For the reviewed Awesome.Bible/core fixture, explicitly select:

```python
MIGRATION_MODULES = {
    # Preserve all other reviewed module overrides.
    'accounts': 'htk.apps.accounts.legacy_migrations',
}
HTK_LEGACY_ACCOUNTS_DATABASE = 'core'
HTK_LEGACY_ACCOUNTS_SCHEMA_MODE = 'adopt'  # or explicitly 'create'
```

Both models and the auth user must read/write on that alias; both account
tables must migrate together there. Apply normally to the explicit database:

```bash
python manage.py migrate accounts --database=core
```

Do **not** use `--fake` or `--fake-initial`: these can bypass validation. These
examples are preparation, not permission for a live migration. The static
BigAutoField state matches the verified Awesome.Bible consumer. Consumers using
HTK's AutoField AppConfig, different auth models or other migration histories
require their own state comparison; the separate accounts service is not
certified by this fixture.

Consumers explicitly wanting the existing accounts signals with this reviewed
BigAutoField state can select
`htk.apps.accounts.apps.HtkAccountsBigAutoFieldAppConfig` in `INSTALLED_APPS`.
It inherits the current handlers and is excluded from automatic discovery.
This is a separate registration choice, not implicit migration activation. For a
single-default-database service, choose `HTK_LEGACY_ACCOUNTS_DATABASE = 'default'`
only after verifying its actual co-located user/account schema. Retain the same
explicit create/adopt mode and use `--database=default` for that selected target.
The old explicit AutoField configuration remains unchanged and does not match
this static BigAutoField history.

## Modes, guarantees and limits

- **Create:** both tables must be absent, and the co-located user table must
  already exist. Only then create the two tables with their foreign keys and
  per-user uniqueness. One existing table is not an invitation to fill gaps.
- **Adopt:** both base tables must exist. Validate both before recording the
  baseline, without changing rows or table DDL. Check exact columns, field type
  categories, nullability, character widths, primary keys, expected uniqueness
  and user foreign keys. MySQL cross-schema foreign keys are rejected.
- **Reject:** absent mode/alias, incoherent routing, mixed/incorrect presence or
  incompatible structure raises before account-table changes and recorder
  advancement. A defect in the second table cannot mutate the first.
- **Reverse:** deliberately refused. Django cannot infer whether these tables
  were newly created or adopted; a rollback must not drop pre-existing account
  data. Prepare an explicit recovery plan from the real schema and backups.

Compatible 32-bit and 64-bit legacy IDs may be adopted without widening or
increasing capacity. This is bounded structural validation, not an audit of
existing data, triggers, collation, permissions, writers or arbitrary drift.
TextField's application max length is not a database length constraint. MySQL
DDL is not transactional: an execution failure after preflight can leave a
partially created schema and requires operator review, not automatic retries
with a different mode. No constraint disabling, row cleanup or table relocation
is provided.

## Verification and ownership

Shared HTK accounts owns this baseline. The consumer integration harness is
`awesomebible.tests.reader_legacy_accounts_acceptance`, using the full source
app registry, disposable SQLite or owned MySQL, blocked host/default/Maskil
access and enabled foreign-key checks. Cases cover fresh create, populated
32/64-bit adoption, rejected choices/layouts, model-state parity and reversal.
Successful baselines also exercise unreferenced instance/queryset deletion with
and without profiles, populated attributes/emails, per-user uniqueness,
unrelated-row preservation, retained feedback with a null user, and referenced
saved-data restriction. They do not test the separate accounts-service signals,
Passport, outbound providers, raw SQL or concurrent cross-database deletion.

A separate `awesomebible.tests.accounts_service_registry_preflight` consumer
harness now compares the literal accounts-service source list, the old explicit
AutoField configuration and the new explicit BigAutoField configuration. On
SQLite/MySQL, the BigAutoField candidate passes fresh/create and populated
32/64-bit adoption with connected signals, automatic profiles, state parity and
unrelated-row preservation. Repeat `ready()` does not duplicate receivers; user
updates do not create another profile. The original configurations and absent
schema mode retain their reported failures. This uses isolated source-derived
settings and candidate dependencies, not accounts-service HTTP or deployed
settings. Physical 32-bit capacity remains 32-bit after adoption.

Use SPEAR for adoption: scope the real consumer/history, plan backups/recovery,
execute a disposable rehearsal, assess schema/data/routes/lifecycle separately,
then resolve with explicit remaining limits. No deployment or live setting is
changed by adding this module.
