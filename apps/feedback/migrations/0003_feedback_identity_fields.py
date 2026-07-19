# Generated manually for optional feedback submitter identity fields.

# Django Imports
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0002_secure_feedback_request_defaults'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackrequest',
            name='username',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequest',
            name='first_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequest',
            name='last_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestvote',
            name='username',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestvote',
            name='first_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestvote',
            name='last_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestsubscription',
            name='username',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestsubscription',
            name='first_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestsubscription',
            name='last_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestcomment',
            name='username',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestcomment',
            name='first_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackrequestcomment',
            name='last_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackevidence',
            name='username',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackevidence',
            name='first_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='feedbackevidence',
            name='last_name',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
