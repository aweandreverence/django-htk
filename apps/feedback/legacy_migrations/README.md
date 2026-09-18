# Optional legacy feedback schema baseline

This source migration module gives **`htk.Feedback`** a modern Django migration
state without moving its app label, renaming `htk_feedback`, unregistering its
relations, or replaying South migrations. It is opt-in: HTK's default root
`migrations/` remains unchanged. It does not migrate the other legacy HTK apps.

## Before selecting this history

Review the actual database layout and backups. Determine whether the legacy
table is absent everywhere relevant or already exists on the intended database.
Do not create an empty replacement beside legacy data in another database.
This module does not inspect, relocate or reconcile tables in other aliases.
The table, auth user and Site must be co-located, with matching read/write and
migration routing. An app-label-only router that sends all `htk` models elsewhere
is not sufficient. Keep unrelated HTK routes unchanged.

For a reviewed Awesome.Bible/core integration, the candidate core router uses:

```python
HTK_LEGACY_FEEDBACK_DATABASE = 'core'
MIGRATION_MODULES = {
    # Preserve any other project-specific overrides.
    'htk': 'htk.apps.feedback.legacy_migrations',
}
HTK_LEGACY_FEEDBACK_SCHEMA_MODE = 'adopt'  # or explicitly 'create'
```

Apply with an explicit database, using normal migration execution, **not**
`--fake` or `--fake-initial` (which can bypass the validation):

```bash
python manage.py migrate htk --database=core
```

These are deployment preparation instructions, not authorization to alter a
live schema. Do not replace a populated project's different `MIGRATION_MODULES`
history or a future root HTK migration graph without reconciling its recorder.
The model state uses BigAutoField, matching the verified Python 3.12/Django 5.2
consumer; consumers using a different automatic-PK policy need a separate review.

## Contract and limits

| Mode | Required table state | Result |
| --- | --- | --- |
| `create` | Absent on the reviewed target; auth/Site tables present | Create the canonical table and record the migration. |
| `adopt` | Existing compatible base table on the reviewed target | Validate and record state, without feedback-table DDL or row changes. |
| Missing mode/alias, wrong route, incompatible layout | Any | Raise before feedback-table changes; no migration record is added. |

Adoption checks exact column names, type categories, nullability, character
widths, primary key, two user/site foreign keys and unexpected uniqueness. A
signed 32-bit or 64-bit auto-increment legacy ID is accepted without alteration;
adoption does **not** widen a 32-bit ID or increase its capacity. Old South
`date_created` layouts are rejected: the historical rename to `created_on` needs
its own reviewed compatibility migration. The original South files remain
unchanged. Adoption is not a full audit of triggers, data quality, collation,
permissions, concurrent writers or arbitrary historical drift.

The baseline is deliberately **irreversible**: Django cannot safely distinguish
a newly created table from one it adopted during a future rollback. Reversal
must not drop possibly pre-existing feedback. Prepare an explicit recovery plan
from the actual schema and backups instead. Keep the routing setting active
after adoption; unsetting it can send reads back to the historical fallback.

## Verification and ownership

Owned by shared HTK feedback, coordinated with the consumer's database router.
The cross-repo integration harness is
`awesomebible.tests.reader_legacy_feedback_acceptance` in Awesome.Bible's reader
branch. It uses the full source app registry, pinned dependencies, disposable
SQLite or an owned MySQL container, and blocked host/default/Maskil access.
Cases cover fresh create, populated 64/32-bit adoption, absent mode/route,
wrong create/adopt choice, old columns, wrong widths/uniqueness/foreign keys,
model-state parity, no-DDL rejection/adoption, and refused reversal.

This fixes only the selected feedback schema boundary. The verified consumer
then reaches a separate missing `accounts_userattribute` table during account
deletion; the user and feedback remain intact. It is **not** account-erasure
acceptance. No production default, other app's schema, endpoint, data or model
registration is changed by merely adding this module.
