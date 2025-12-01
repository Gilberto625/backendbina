# Generated manually for security improvements
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_usuario_backup_codes'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='intentos_fallidos',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='usuario',
            name='bloqueado_hasta',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='ultimo_intento',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]



