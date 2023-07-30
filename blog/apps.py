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
            extra_pages = [*ExtraPages.objects.all()]

            if len(extra_pages) < 3:
                for _ in range(3 - (len(extra_pages))):
                    ExtraPages.objects.create()
        except:
            pass

        try:
            from .models import Image
            images = Image.objects.all()

            for image in images:
                image.html = f'<img src="/{image.image.name}">'
                image.save()
        except:
            pass
