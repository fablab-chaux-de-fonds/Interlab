from django.core.management.commands.runserver import Command as RunServerCommand
from django_q.cluster import Cluster

class Command(RunServerCommand):
    def handle(self, *args, **options):
        q = Cluster()
        q.start()
        try:
            super().handle(*args, **options)
        finally:
            q.stop()