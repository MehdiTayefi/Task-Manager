import time

from django.core.management.base import BaseCommand
from demo.api.services import cleanup_expired


class Command(BaseCommand):
    help= "Delete only expired demo accounts and their tasks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Keep running, including when the site has no traffic."
        )

        parser.add_argument(
            "--interval",
            type=int,
            default=60
        )

    def handle(self, *args, **options):
        interval = max(1, options["interval"])

        try:
            while True:
                total = 0
                while True:
                    removed = cleanup_expired(batch_size=100)
                    total += removed
                    if removed < 100:
                        break
                self.stdout.write(f"Removed {total} expired demo account(s).")
                if not options["loop"]:
                    return
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write("Demo cleanup worker stopped.")