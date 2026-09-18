"""Baseline legacy feedback only after an explicit create/adopt decision.

This optional history must be selected as MIGRATION_MODULES['htk']; it does not
change the default root HTK history. Do not replay South or silently fake this
migration. Existing tables are adopted only after bounded structural validation.
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


class LegacyFeedbackSchemaError(RuntimeError):
    """The reviewed database/mode/schema contract was not satisfied."""


def validate_table(connection: Any, model: Any) -> None:
    """Reject unknown layouts; never repair, truncate or relabel existing data."""
    table = model._meta.db_table
    with connection.cursor() as cursor:
        tables = {row.name: row.type for row in connection.introspection.get_table_list(cursor)}
        if tables.get(table) != 't':
            raise LegacyFeedbackSchemaError('Expected a legacy feedback base table')
        columns = {row.name: row for row in connection.introspection.get_table_description(cursor, table)}
        constraints = connection.introspection.get_constraints(cursor, table)
    fields = {field.column: field for field in model._meta.local_fields}
    if columns.keys() != fields.keys():
        raise LegacyFeedbackSchemaError('Legacy feedback columns require a separate compatibility migration')
    kinds = {
        'id': {'AutoField', 'BigAutoField'},
        'site_id': {'IntegerField', 'BigIntegerField'},
        'user_id': {'IntegerField', 'BigIntegerField'},
        'processed': {'BooleanField', 'IntegerField'},
        'needs_followup': {'BooleanField', 'IntegerField'},
        'created_on': {'DateTimeField'},
    }
    for name, field in fields.items():
        column = columns[name]
        kind = connection.introspection.get_field_type(column.type_code, column)
        if kind not in kinds.get(name, {'CharField'}) or bool(column.null_ok) != field.null:
            raise LegacyFeedbackSchemaError('Legacy feedback column type/nullability differs: ' + name)
        if name in {'processed', 'needs_followup'} and connection.vendor == 'mysql' and column.data_type != 'tinyint':
            raise LegacyFeedbackSchemaError('Legacy feedback boolean storage differs: ' + name)
        if field.max_length:
            length = column.internal_size
            if connection.vendor == 'sqlite':
                match = re.fullmatch(r'varchar\((\d+)\)', column.type_code, flags=re.IGNORECASE)
                length = int(match.group(1)) if match else None
            if length != field.max_length:
                raise LegacyFeedbackSchemaError('Legacy feedback character width differs: ' + name)
    primary = [value['columns'] for value in constraints.values() if value['primary_key']]
    if primary != [['id']]:
        raise LegacyFeedbackSchemaError('Legacy feedback primary key differs')
    if any(value['unique'] and not value['primary_key'] for value in constraints.values()):
        raise LegacyFeedbackSchemaError('Unexpected uniqueness constraint on legacy feedback')
    if sum(bool(value['foreign_key']) for value in constraints.values()) != 2:
        raise LegacyFeedbackSchemaError('Unexpected legacy feedback foreign keys')
    for name in ('site', 'user'):
        field = model._meta.get_field(name)
        expected = (field.remote_field.model._meta.db_table, field.target_field.column)
        if not any(value['foreign_key'] == expected and value['columns'] == [field.column]
                   for value in constraints.values()):
            raise LegacyFeedbackSchemaError('Legacy feedback foreign key differs: ' + name)


class CreateOrAdoptLegacyFeedback(migrations.CreateModel):
    """Provide normal model state, but make database baseline selection explicit."""

    reversible = False

    def database_forwards(self, app_label: str, schema_editor: Any,
                          from_state: Any, to_state: Any) -> None:
        model = to_state.apps.get_model(app_label, self.name)
        connection = schema_editor.connection
        alias = getattr(settings, 'HTK_LEGACY_FEEDBACK_DATABASE', None)
        mode = getattr(settings, 'HTK_LEGACY_FEEDBACK_SCHEMA_MODE', None)
        if not alias or mode not in {'create', 'adopt'}:
            raise LegacyFeedbackSchemaError('Select an explicit legacy feedback database and create/adopt mode')
        if router.db_for_read(model) != alias or router.db_for_write(model) != alias:
            raise LegacyFeedbackSchemaError('Legacy feedback read/write routing does not match the selected database')
        if not self.allow_migrate_model(connection.alias, model):
            return
        if connection.alias != alias:
            raise LegacyFeedbackSchemaError('Legacy feedback migrations route to an unselected database')
        for name in ('user', 'site'):
            target = model._meta.get_field(name).remote_field.model
            if router.db_for_write(target) != alias:
                raise LegacyFeedbackSchemaError('Legacy feedback user/site targets must be co-located')
        with connection.cursor() as cursor:
            tables = {row.name for row in connection.introspection.get_table_list(cursor)}
        if any(model._meta.get_field(name).remote_field.model._meta.db_table not in tables
               for name in ('user', 'site')):
            raise LegacyFeedbackSchemaError('Legacy feedback target tables are absent')
        exists = model._meta.db_table in tables
        if (mode == 'create') == exists:
            raise LegacyFeedbackSchemaError('Create requires an absent table; adopt requires an existing table')
        if mode == 'create':
            schema_editor.create_model(model)
        else:
            validate_table(connection, model)

    def database_backwards(self, app_label: str, schema_editor: Any,
                           from_state: Any, to_state: Any) -> None:
        raise IrreversibleError('Legacy feedback baseline cannot drop a possibly adopted table')


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL),
                    ('sites', '0002_alter_domain_unique')]
    operations = [CreateOrAdoptLegacyFeedback(
        name='Feedback',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('name', models.CharField(max_length=100, null=True, blank=True)),
            ('comment', models.CharField(max_length=2000, null=True, blank=True)),
            ('email', models.EmailField(max_length=100, null=True, blank=True)),
            ('uri', models.CharField(max_length=200, null=True, blank=True)),
            ('processed', models.BooleanField(default=False)),
            ('needs_followup', models.BooleanField(default=True)),
            ('created_on', models.DateTimeField(auto_now_add=True)),
            ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sites.site')),
            ('user', models.ForeignKey(
                blank=True, default=None, null=True,
                on_delete=django.db.models.deletion.SET_DEFAULT,
                related_name='feedback', to=settings.AUTH_USER_MODEL,
            )),
        ],
        options={'verbose_name': 'Feedback', 'verbose_name_plural': 'Feedback'},
    )]
