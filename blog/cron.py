from random import randrange

from django_cron import CronJobBase, Schedule

from .models import Rss, Index, Category
from .admin import generate_thread_func


class Task(CronJobBase):
    schedule = Schedule(
        run_every_mins=24 * 60,
        retry_after_failure_mins=5
    )

    code = 'blog.Task'

    def do(self):
        rss_ = [*Rss.objects.all()]
        index = Index.objects.first()

        if not rss_ or not index.articles_generated_per_day:
            return

        for _ in range(index.articles_generated_per_day):
            rss = rss_[randrange(len(rss_))]
            generate_thread_func(rss)
