# Generated manually for backup_codes field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_usuario_totp_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='backup_codes',
            field=models.TextField(blank=True, null=True),
        ),
    ]

