# Generated by Django 2.2.19 on 2021-10-08 03:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_auto_20211007_0904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(unique=True, verbose_name='уникальный id'),
        ),
    ]