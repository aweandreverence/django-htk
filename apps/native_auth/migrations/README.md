# Native credential schema

Opt-in `htk_native_auth` migrations. Apply on the database selected for both grant
and session models. In A&R this is `core`, not a product or Bible database.
Regenerate with Django makemigrations using the isolated test settings. No data
from legacy product-local credential tables is migrated automatically.
