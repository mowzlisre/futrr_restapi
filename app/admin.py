from django.contrib import admin
from .models import Event, Capsule, CapsuleRecipient, CapsuleContent, CapsuleEncryptionKey, CapsuleFavorite

# Register your models here.
admin.site.register(Event)
admin.site.register(Capsule)
admin.site.register(CapsuleRecipient)
admin.site.register(CapsuleContent)
admin.site.register(CapsuleEncryptionKey)
admin.site.register(CapsuleFavorite)