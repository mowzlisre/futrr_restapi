"""
Drain the EmailQueue table respecting SES limits and priority rules.

Priority logic:
  - daily sent < 40k  → process both high and low (5 high : 1 low)
  - daily sent >= 40k → process only high priority
  - Rate: ~12/sec (leave 2/sec headroom for inline OTP sends)
  - Max 3 attempts per email before marking as failed

Run as: python manage.py process_email_queue
"""

import logging
import time
from itertools import cycle

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import EmailQueue
from users.emails.queue import send_queued_email

logger = logging.getLogger("futrr.email")

DAILY_THRESHOLD = 40_000   # after this, only high-priority emails
RATE_LIMIT = 12            # emails/sec (headroom for inline sends)
CYCLE_SLEEP = 5            # seconds between queue cycles


class Command(BaseCommand):
    help = "Process the email queue with priority-based delivery"

    def handle(self, **options):
        self.stdout.write("Email queue processor started")
        logger.info("queue_processor_started", extra={"action": "queue_processor_started"})

        while True:
            try:
                self._process_cycle()
            except Exception:
                logger.error("queue_cycle_error", extra={"action": "queue_cycle_error"}, exc_info=True)
            time.sleep(CYCLE_SLEEP)

    def _process_cycle(self):
        today = timezone.now().date()
        daily_sent = EmailQueue.objects.filter(
            status=EmailQueue.Status.SENT,
            sent_at__date=today,
        ).count()

        high_qs = EmailQueue.objects.filter(
            status=EmailQueue.Status.PENDING,
            priority=EmailQueue.Priority.HIGH,
            attempts__lt=3,
        ).order_by("created_at")

        low_qs = EmailQueue.objects.filter(
            status=EmailQueue.Status.PENDING,
            priority=EmailQueue.Priority.LOW,
            attempts__lt=3,
        ).order_by("created_at")

        over_threshold = daily_sent >= DAILY_THRESHOLD

        if over_threshold:
            # Only process high-priority emails
            batch = list(high_qs[:50])
        else:
            # 5:1 ratio — interleave 5 high then 1 low
            high_list = list(high_qs[:50])
            low_list = list(low_qs[:10])
            batch = self._interleave(high_list, low_list)

        if not batch:
            return

        sent_this_cycle = 0
        for entry in batch:
            send_queued_email(entry)
            sent_this_cycle += 1
            daily_sent += 1

            # Stop sending low-priority if we cross the threshold mid-cycle
            if daily_sent >= DAILY_THRESHOLD and entry.priority == EmailQueue.Priority.LOW:
                break

            # Rate limit: ~12/sec
            if sent_this_cycle % RATE_LIMIT == 0:
                time.sleep(1)

        if sent_this_cycle:
            logger.info("queue_cycle_complete", extra={
                "action": "queue_cycle_complete",
                "sent": sent_this_cycle,
                "daily_total": daily_sent,
            })

    @staticmethod
    def _interleave(high_list, low_list):
        """Yield 5 high-priority items, then 1 low-priority, repeat."""
        result = []
        hi_idx = 0
        lo_idx = 0
        while hi_idx < len(high_list) or lo_idx < len(low_list):
            # Take up to 5 high
            for _ in range(5):
                if hi_idx < len(high_list):
                    result.append(high_list[hi_idx])
                    hi_idx += 1
            # Take 1 low
            if lo_idx < len(low_list):
                result.append(low_list[lo_idx])
                lo_idx += 1
        return result
