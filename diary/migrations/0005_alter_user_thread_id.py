# Generated by Django 4.2.7 on 2023-11-14 20:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diary", "0004_message_telegram_message_id_alter_message_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="thread_id",
            field=models.CharField(max_length=50),
        ),
    ]
