from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Job
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

import json

def dashboard(request):
    view_type = request.GET.get('view_type', 'day')
    selected_date_str = request.GET.get('date', date.today().isoformat())

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = date.today()

    events_json = "[]"
    jobs = Job.objects.all()

    if view_type == 'week':
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        jobs = jobs.filter(date__range=[start_of_week, end_of_week]).order_by('date', 'start_time')
        date_display = f"{start_of_week.strftime('%d-%m-%Y')} to {end_of_week.strftime('%d-%m-%Y')}"
    else:  # Day view
        jobs = jobs.filter(date=selected_date).order_by('start_time')
        date_display = selected_date.strftime('%d-%m-%Y')

        events = []
        for job in jobs:
            if job.date and job.start_time and job.end_time:
                events.append({
                    'title': f"{job.customer.name} ({job.get_job_type_display()})",
                    'start': datetime.combine(job.date, job.start_time).isoformat(),
                    'end': datetime.combine(job.date, job.end_time).isoformat(),
                })
        # This is now a list of dicts, not a JSON string.
        # The json_script tag in the template will handle serialization.
        events_json = events

    context = {
        'jobs': jobs,
        'selected_date': selected_date,
        'view_type': view_type,
        'date_display': date_display,
        'status_choices': Job.STATUS_CHOICES,
        'events_json': events_json,
    }
    return render(request, 'core/dashboard.html', context)

@require_POST
def update_job_status(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    original_recurrence_type = job.recurrence_type
    original_recurrence_frequency = job.recurrence_frequency

    new_status = request.POST.get('status')
    if new_status in [status[0] for status in Job.STATUS_CHOICES]:
        job.status = new_status
        job.save()

    if job.status == 'completed' and original_recurrence_type != 'none':
        # Create the next job in the series
        new_job = job
        new_job.pk = None  # This will create a new instance

        delta = None
        if original_recurrence_type == 'weekly':
            delta = timedelta(weeks=original_recurrence_frequency)
        elif original_recurrence_type == 'monthly':
            delta = relativedelta(months=original_recurrence_frequency)

        if delta:
            new_job.date = job.date + delta
            new_job.status = 'scheduled'
            # The start_time and end_time remain the same
            new_job.start_time = job.start_time
            new_job.end_time = job.end_time
            # Keep the recurrence for the new job
            new_job.recurrence_type = original_recurrence_type
            new_job.recurrence_frequency = original_recurrence_frequency
            new_job.save()
            new_job.staff.set(job.staff.all())

            # Mark the original job as non-recurring
            job.recurrence_type = 'none'
            job.save()

    # Preserve the date filter
    selected_date = job.date.strftime('%Y-%m-%d')
    return redirect(f"/?date={selected_date}")
