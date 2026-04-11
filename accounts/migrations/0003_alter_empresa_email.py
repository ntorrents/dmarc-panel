# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_empresa_email_empresa_telefono'),
    ]

    operations = [
        migrations.AlterField(
            model_name='empresa',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
