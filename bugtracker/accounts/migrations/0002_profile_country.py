# Generated by Django 3.0.8 on 2020-07-25 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='country',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
