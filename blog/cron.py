from random import randrange

from django_cron import CronJobBase, Schedule
from django.conf import settings
from threading import Thread

from .models import Rss
from .admin import generate_thread_func


class Task(CronJobBase):
    schedule = Schedule(
        run_every_mins=24 * 60,
        retry_after_failure_mins=5
    )

    code = 'blog.Task'

    def do(self):
        rss_ = [*Rss.objects.all()]

        if not rss_:
            return

        for _ in range(settings.ARTICLES_PER_DAY):
            rss = rss_[randrange(len(rss_))]

            Thread(
                daemon=True,
                target=generate_thread_func,
                args=[rss]
            ).start()
