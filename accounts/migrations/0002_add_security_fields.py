# Generated manually for security enhancements
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='totp_secret',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='totp_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='backup_codes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='password_reset_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='password_reset_expires',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
