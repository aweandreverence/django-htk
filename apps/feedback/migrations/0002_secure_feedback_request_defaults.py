# Generated manually for safer feedback request defaults.

# Django Imports
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedbackrequest',
            name='needs_review',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='feedbackrequest',
            name='visibility',
            field=models.CharField(
                choices=[
                    ('public', 'Public'),
                    ('unlisted', 'Unlisted'),
                    ('private', 'Private'),
                ],
                default='private',
                max_length=24,
            ),
        ),
    ]
