# Generated migration for PasswordResetToken and TwoFactorDevice models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import secrets


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(default=secrets.token_urlsafe, max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_tokens', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TwoFactorDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_type', models.CharField(choices=[('totp', 'Time-based OTP'), ('sms', 'SMS'), ('email', 'Email')], max_length=10)),
                ('device_name', models.CharField(help_text='e.g., iPhone 12, Google Authenticator', max_length=100)),
                ('secret', models.CharField(default=secrets.token_urlsafe, max_length=255)),
                ('is_primary', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='two_factor_devices', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-is_primary', '-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='twofactordevice',
            unique_together={('user', 'device_name')},
        ),
    ]
