from django.db import models
from apps.accounts.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="إشعار جديد")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"🔔 {self.user.full_name}: {self.title} - {self.message[:50]}"

@receiver(post_save, sender=Notification)
def send_realtime_notification(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        group_name = f"user_{instance.user.id}_notifications"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "content": {
                    "id": instance.id,
                    "title": instance.title,
                    "message": instance.message,
                    "is_read": instance.is_read,
                    "created_at": instance.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }
        )
