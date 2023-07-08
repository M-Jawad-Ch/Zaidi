from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self):
        from .models import Generator

        generators = Generator.objects.filter(running=True)

        for generator in generators:
            generator.running = False
            generator.save()
