# Generated by Django 4.0 on 2024-01-01 05:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_rename_voice_note_blob_chat_voice_note_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='voice_note_data',
            field=models.TextField(blank=True, null=True),
        ),
    ]
