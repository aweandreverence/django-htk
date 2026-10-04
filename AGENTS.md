# AGENTS.md

Instructions for AI agents and maintainers working in `django-htk`.

## Operating Model

Use SPEAR — Scope, Plan, Execute, Assess, Resolve — as the default work loop. Compress it for small reversible changes; slow down for public APIs, migrations, security, data model changes, and anything hard to reverse.

## Django Model Organization

For new Django apps/modules, prefer a `models/` package instead of a monolithic `models.py` whenever there is more than one model or the model set is likely to grow.

Recommended shape:

```text
apps/example/models/
├── __init__.py
├── README.md
├── thing.py
└── thing_event.py
```

Guidelines:

- Put each concrete model, or tightly-coupled tiny model group, in its own focused file.
- Keep `models/__init__.py` explicit; import every public model there so Django discovers them and callers can keep using `from htk.apps.example.models import Thing`.
- Avoid wildcard filesystem/dynamic imports in `models/__init__.py`; import order should be deterministic and reviewable.
- Use local imports inside methods when needed to avoid circular model imports.
- Do not split truly tiny one-model apps solely for ceremony, but default new multi-model work to the package pattern.
- When creating a new `models/` folder, include a short `README.md` explaining the files and import convention.

## Documentation

When adding or materially changing reusable app structure, update the app README and any relevant top-level docs in the same change. Keep examples generic unless the module is intentionally product-specific.

## Reuse and Naming Style

HTK should stay DRY and composable: prefer extending existing utilities in `htk.utils`, shared model/base classes, or reusable app APIs before adding one-off helpers to a feature module. Build small Lego-block functions that downstream projects can reuse.

For new APIs, avoid `get_*` names unless matching Django conventions, preserving backward compatibility, or overriding an existing API. Follow the naming principles in `CONTRIBUTING.md` and Jonathan Tsai's post ["Get Is the Worst Function Prefix Ever"](https://www.jontsai.com/2022/07/14/get-is-the-worst-function-prefix-ever): use precise verbs such as `extract_*`, `build_*`, `enrich_*`, `combine_*`, `calculate_*`, `look_up_*`, `retrieve_*`, `fetch_*`, `format_*`, and `transform_*` so the name reveals what the function does and what costs/risks callers should expect.

## Safety

- Do not commit secrets, tokens, private credentials, or private customer/user data.
- Treat migrations and public API changes as higher-risk: inspect generated migrations, run the smallest relevant test/check, and call out compatibility implications.
- Prefer additive/reversible changes and explicit deprecation paths for shared library behavior.

<!-- ar-engineering-handbook:start -->
## A&R maintainers: Shared engineering guidance

Reference revision: `5cef9e63509ede20e776b614ef44464454b57ebe`.

- [Engineering handbook](https://github.com/aweandreverence/engineering/blob/5cef9e63509ede20e776b614ef44464454b57ebe/README.md)
- [Architecture and ownership](https://github.com/aweandreverence/engineering/blob/5cef9e63509ede20e776b614ef44464454b57ebe/architecture.md)
- [Applicable style guide](https://github.com/aweandreverence/engineering/blob/5cef9e63509ede20e776b614ef44464454b57ebe/style/python-django.md)
- [Review checklist](https://github.com/aweandreverence/engineering/blob/5cef9e63509ede20e776b614ef44464454b57ebe/review-checklist.md)
- [Adoption and exceptions](https://github.com/aweandreverence/engineering/blob/5cef9e63509ede20e776b614ef44464454b57ebe/adoption.md)

This is a private, optional reference for A&R maintainers. Outside contributors
are not required to access it; this repository's public instructions remain
self-contained and authoritative for their contributions. Do not copy private
handbook contents into this public repository or upstream PRs.

Keep repository-specific security, domain, build and deployment instructions in
this repo. This reference does not authorize migrations, runtime upgrades, merges
or deployments. Resolve substantive conflicts explicitly and record local
exceptions; do not silently overwrite existing policy. Follow SPEAR proportionately:
scope, plan, execute, assess, resolve. Update the pinned revision through a PR.
<!-- ar-engineering-handbook:end -->
