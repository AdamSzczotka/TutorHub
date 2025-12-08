from celery import shared_task


@shared_task
def check_attendance_alerts():
    """Periodic task to check and send attendance alerts."""
    from .services import alert_service

    alerts = alert_service.check_and_create_alerts()
    return f'Created {len(alerts)} new alerts'


@shared_task
def generate_monthly_reports_task(month_str: str | None = None):
    """Background task to generate and send monthly reports."""
    from datetime import datetime

    from .services import report_service

    if month_str:
        month = datetime.fromisoformat(month_str)
    else:
        # Use previous month
        today = datetime.now()
        if today.month == 1:
            month = datetime(today.year - 1, 12, 1)
        else:
            month = datetime(today.year, today.month - 1, 1)

    results = report_service.generate_and_send_monthly_reports(month)

    success_count = sum(1 for r in results if r['success'])
    return f"Generated {success_count}/{len(results)} reports for {month.strftime('%B %Y')}"
