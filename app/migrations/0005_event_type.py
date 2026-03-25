from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0004_passphrase_hint'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='event_type',
            field=models.CharField(
                choices=[
                    ("birthday", "Birthday"),
                    ("wedding", "Wedding"),
                    ("graduation", "Graduation"),
                    ("anniversary", "Anniversary"),
                    ("new_year", "New Year"),
                    ("sports", "Sports"),
                    ("travel", "Travel"),
                    ("festival", "Festival"),
                    ("music", "Music"),
                    ("memorial", "Memorial"),
                    ("reunion", "Reunion"),
                    ("other", "Other"),
                ],
                default='other',
                max_length=30,
            ),
        ),
    ]
