from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_followrequest_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient', models.EmailField(max_length=254)),
                ('email_type', models.CharField(max_length=30)),
                ('priority', models.CharField(choices=[('high', 'High'), ('low', 'Low')], max_length=4)),
                ('payload', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending', max_length=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('attempts', models.IntegerField(default=0)),
                ('error', models.TextField(blank=True, null=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['status', 'priority', 'created_at'], name='users_email_status_d2e3f4_idx'),
                ],
            },
        ),
    ]
