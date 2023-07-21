from django.apps import AppConfig


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
        except:
            pass

        try:
            from .models import ExtraPages
            if not ExtraPages.objects.all():
                ExtraPages.objects.create()
                ExtraPages.objects.create()
        except:
            pass
