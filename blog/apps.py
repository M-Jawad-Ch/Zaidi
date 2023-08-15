from django.apps import AppConfig
from django.conf import settings


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self):
        try:
            from .models import Generator

            generators = Generator.objects.filter(running=True)

            for generator in generators:
                generator.running = False
                generator.save()
        except:
            pass

        try:
            from .models import Index
            if not Index.objects.first():
                Index.objects.create()

            index = Index.objects.first()
            settings.EMAIL_HOST_USER = index.notification_sender_email
            settings.EMAIL_HOST_PASSWORD = index.notification_sender_email_password
            settings.EMAIL_RECEIVER = index.notification_receiver_email
        except:
            pass

        try:
            from .models import ExtraPages

            ExtraPages.objects.get_or_create(slug='contact-us', visible=True)

        except:
            pass

        try:
            from .models import Image
            images = Image.objects.all()

            for image in images:
                image.html = ''
                image.save()
        except:
            pass

        try:
            from .models import Category

            categories = Category.objects.all()
            for category in categories:
                category.visible = category.isPointedBy()
                category.save()
        except:
            pass
