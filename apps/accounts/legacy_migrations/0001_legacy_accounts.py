"""Baseline both legacy account tables together after explicit schema review.

Keep this validation frozen with its historical state. Do not make applied
history depend on a mutable application schema helper or replay old South code.
"""

# Python Standard Library Imports
import re
from typing import Any

# Django Imports
import django.db.models.deletion
from django.conf import settings
from django.db import (
    migrations,
    models,
    router,
)
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.operations.base import Operation


class LegacyAccountSchemaError(RuntimeError):
    """An explicit route, mode or bounded structural requirement was not met."""


def create_operations() -> list[migrations.CreateModel]:
    """Describe the verified BigAutoField consumer without importing live models."""
    return [
        migrations.CreateModel(
            name='UserAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(blank=True, max_length=128)),
                ('value', models.TextField(blank=True, max_length=4096)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('holder', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attributes', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'User Attribute', 'unique_together': {('holder', 'key')}},
        ),
        migrations.CreateModel(
            name='UserEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='emails', to=settings.AUTH_USER_MODEL,
                )),
                ('email', models.EmailField(max_length=254, verbose_name='email address')),
                ('activation_key', models.CharField(blank=True, max_length=40)),
                ('key_expires', models.DateTimeField(blank=True, null=True)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('replacing', models.EmailField(blank=True, max_length=254, null=True)),
            ],
            options={'verbose_name': 'User Email', 'unique_together': {('user', 'email')}},
        ),
    ]


def validate_table(connection: Any, model: Any) -> None:
    """Validate a legacy table's bounded shape; never alter or inspect its rows."""
    table = model._meta.db_table
    with connection.cursor() as cursor:
        tables = {row.name: row.type for row in connection.introspection.get_table_list(cursor)}
        if tables.get(table) != 't':
            raise LegacyAccountSchemaError('Expected legacy account base table: ' + table)
        columns = {row.name: row for row in connection.introspection.get_table_description(cursor, table)}
        constraints = connection.introspection.get_constraints(cursor, table)
        if connection.vendor == 'mysql':
            cursor.execute(
                'SELECT REFERENCED_TABLE_SCHEMA FROM information_schema.KEY_COLUMN_USAGE '
                'WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL',
                [table],
            )
            if any(row[0] != connection.settings_dict['NAME'] for row in cursor.fetchall()):
                raise LegacyAccountSchemaError('Legacy account foreign key crosses database schemas')
    fields = {field.column: field for field in model._meta.local_fields}
    if columns.keys() != fields.keys():
        raise LegacyAccountSchemaError('Legacy account columns differ: ' + table)
    for name, field in fields.items():
        column = columns[name]
        expected = field.get_internal_type()
        allowed = {
            'BigAutoField': {'AutoField', 'BigAutoField'},
            'ForeignKey': {'IntegerField', 'BigIntegerField'},
            'EmailField': {'CharField'},
            'BooleanField': {'BooleanField', 'IntegerField'},
        }.get(expected, {expected})
        kind = connection.introspection.get_field_type(column.type_code, column)
        if kind not in allowed or bool(column.null_ok) != field.null:
            raise LegacyAccountSchemaError('Legacy account type/nullability differs: ' + table + '.' + name)
        if expected == 'BooleanField' and connection.vendor == 'mysql' and column.data_type != 'tinyint':
            raise LegacyAccountSchemaError('Legacy account boolean storage differs')
        if expected in {'CharField', 'EmailField'}:
            length = column.internal_size
            if connection.vendor == 'sqlite':
                match = re.fullmatch(r'varchar\((\d+)\)', column.type_code, flags=re.IGNORECASE)
                length = int(match.group(1)) if match else None
            if length != field.max_length:
                raise LegacyAccountSchemaError('Legacy account character width differs: ' + table + '.' + name)
    if [v['columns'] for v in constraints.values() if v['primary_key']] != [['id']]:
        raise LegacyAccountSchemaError('Legacy account primary key differs')
    unique = {tuple(v['columns']) for v in constraints.values() if v['unique'] and not v['primary_key']}
    expected_unique = {tuple(model._meta.get_field(name).column for name in names)
                       for names in model._meta.unique_together}
    if unique != expected_unique:
        raise LegacyAccountSchemaError('Legacy account uniqueness differs')
    foreign = [v for v in constraints.values() if v['foreign_key']]
    targets = [f for f in fields.values() if f.remote_field]
    if len(foreign) != len(targets):
        raise LegacyAccountSchemaError('Legacy account foreign-key count differs')
    for field in targets:
        expected = (field.remote_field.model._meta.db_table, field.target_field.column)
        if not any(v['columns'] == [field.column] and v['foreign_key'] == expected for v in foreign):
            raise LegacyAccountSchemaError('Legacy account foreign-key target differs')


class LegacyAccountBaseline(Operation):
    """Preflight both tables before applying any optional baseline schema changes."""

    reversible = False

    def state_forwards(self, app_label: str, state: Any) -> None:
        for operation in create_operations():
            operation.state_forwards(app_label, state)

    def database_forwards(self, app_label: str, schema_editor: Any,
                          from_state: Any, to_state: Any) -> None:
        connection = schema_editor.connection
        alias = getattr(settings, 'HTK_LEGACY_ACCOUNTS_DATABASE', None)
        mode = getattr(settings, 'HTK_LEGACY_ACCOUNTS_SCHEMA_MODE', None)
        if not alias or mode not in {'create', 'adopt'}:
            raise LegacyAccountSchemaError('Select an explicit legacy account database and create/adopt mode')
        targets = [to_state.apps.get_model(app_label, operation.name) for operation in create_operations()]
        if any(router.db_for_read(model) != alias or router.db_for_write(model) != alias for model in targets):
            raise LegacyAccountSchemaError('Legacy account read/write routing differs from selected database')
        allowed = [self.allow_migrate_model(connection.alias, model) for model in targets]
        if not any(allowed):
            return
        if not all(allowed) or connection.alias != alias:
            raise LegacyAccountSchemaError('Legacy account tables must migrate together on the selected database')
        user = targets[0]._meta.get_field('holder').remote_field.model
        if router.db_for_read(user) != alias or router.db_for_write(user) != alias:
            raise LegacyAccountSchemaError('Legacy account user table must be co-located')
        with connection.cursor() as cursor:
            tables = {row.name: row.type for row in connection.introspection.get_table_list(cursor)}
        if tables.get(user._meta.db_table) != 't':
            raise LegacyAccountSchemaError('Legacy account user base table is absent')
        present = [model._meta.db_table in tables for model in targets]
        if (mode == 'create' and any(present)) or (mode == 'adopt' and not all(present)):
            raise LegacyAccountSchemaError('Create requires both absent; adopt requires both existing')
        if mode == 'adopt':
            for model in targets:
                validate_table(connection, model)
        else:
            for model in targets:
                schema_editor.create_model(model)

    def database_backwards(self, app_label: str, schema_editor: Any,
                           from_state: Any, to_state: Any) -> None:
        raise IrreversibleError('Legacy account baseline cannot drop possibly adopted tables')

    def describe(self) -> str:
        return 'Explicitly create or validate/adopt both legacy account tables'


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [LegacyAccountBaseline()]
