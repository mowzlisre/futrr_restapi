from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_event_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="subtitle",
            field=models.CharField(max_length=200, blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="event",
            name="event_type_label",
            field=models.CharField(max_length=100, blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="event",
            name="is_time_locked",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="event",
            name="entry_start",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="event",
            name="entry_close",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="event",
            name="max_participants",
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="event",
            name="allowed_content_types",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="event",
            name="unlock_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
