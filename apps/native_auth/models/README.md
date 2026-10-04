# Native credential models

`credentials.py` owns short-lived grants and rotating sessions. Every query must
bind `client_id`; knowing another application's credential grants no access.
User IDs may be routed to a separate account database; do not join across stores.
Import both models explicitly through `models/__init__.py`. This app is opt-in;
apply its migrations to the configured credential database before enabling routes.
