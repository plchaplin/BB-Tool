from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Job
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

def dashboard(request):
    # Get the selected date from the request, default to today if not provided
    selected_date_str = request.GET.get('date', date.today().isoformat())

    try:
        # Convert the string date to a datetime object
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Handle invalid date format by defaulting to today
        selected_date = date.today()

    # Filter jobs where the start_time is on the selected date
    jobs = Job.objects.filter(date=selected_date).order_by('start_time')

    context = {
        'jobs': jobs,
        'selected_date': selected_date,
        'status_choices': Job.STATUS_CHOICES,
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
