from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('actions', '0017_alter_funcionario_username'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eixo',
            old_name='pai',
            new_name='principal',
        ),
    ]
