# Generated by Django 2.1.5 on 2021-05-14 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0005_auto_20210511_0115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveytask',
            name='edit_form_url',
            field=models.URLField(blank=True, default=None, max_length=800, null=True),
        ),
    ]
