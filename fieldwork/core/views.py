from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Job
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

import json

from django.contrib.auth.models import User


def dashboard(request):
    view_type = request.GET.get('view_type', 'day')
    selected_date_str = request.GET.get('date', date.today().isoformat())
    selected_staff_id = request.GET.get('staff_id', 'all')

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = date.today()

    # Base queryset for jobs
    jobs = Job.objects.prefetch_related('staff', 'customer').all()

    # Filter by staff member if one is selected
    if selected_staff_id and selected_staff_id != 'all':
        try:
            staff_id = int(selected_staff_id)
            jobs = jobs.filter(staff__id=staff_id)
        except (ValueError, TypeError):
            # Catcher for if staff_id is not a valid number
            pass

    # Filter by date range based on the view type
    if view_type == 'week':
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        jobs = jobs.filter(date__range=[start_of_week, end_of_week]).order_by('date', 'start_time')
        date_display = f"{start_of_week.strftime('%d-%m-%Y')} to {end_of_week.strftime('%d-%m-%Y')}"
    else:  # Day view
        jobs = jobs.filter(date=selected_date).order_by('start_time')
        date_display = selected_date.strftime('%d-%m-%Y')

    # Prepare events for FullCalendar, now including staff names in the title
    events = []
    if view_type == 'day':
        for job in jobs:
            if job.date and job.start_time and job.end_time:
                staff_names = ", ".join([s.get_full_name() or s.username for s in job.staff.all()])
                title = f"{job.customer.name} ({job.get_job_type_display()})"
                if staff_names:
                    title += f" - {staff_names}"

                events.append({
                    'title': title,
                    'start': datetime.combine(job.date, job.start_time).isoformat(),
                    'end': datetime.combine(job.date, job.end_time).isoformat(),
                    'resourceIds': [s.id for s in job.staff.all()] # For potential future use
                })

    # Get all staff members for the filter dropdown
    staff_list = User.objects.filter(staffprofile__isnull=False).order_by('first_name', 'last_name')

    context = {
        'jobs': jobs,
        'selected_date': selected_date,
        'view_type': view_type,
        'date_display': date_display,
        'status_choices': Job.STATUS_CHOICES,
        'events_json': events,
        'staff_list': staff_list,
        'selected_staff_id': selected_staff_id,
    }
    return render(request, 'core/dashboard.html', context)

@require_POST
def update_job_status(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    new_status = request.POST.get('status')
    if new_status in [status[0] for status in Job.STATUS_CHOICES]:
        job.status = new_status
        job.save()

    # Check for recurrence based on the CUSTOMER's settings, not the individual job's.
    customer_recurrence_type = job.customer.default_recurrence_type
    customer_recurrence_freq = job.customer.default_recurrence_frequency

    if job.status == 'completed' and customer_recurrence_type != 'none':
        # Create the next job in the series from the completed one
        new_job = job
        new_job.pk = None  # This will create a new instance when saved

        delta = None
        if customer_recurrence_type == 'weekly':
            delta = timedelta(weeks=customer_recurrence_freq)
        elif customer_recurrence_type == 'monthly':
            delta = relativedelta(months=customer_recurrence_freq)

        if delta:
            new_job.date = job.date + delta
            new_job.status = 'scheduled'

            # The start_time remains the same as the completed job
            new_job.start_time = job.start_time

            # Calculate new end_time based on customer's default duration
            if job.customer.default_duration_minutes:
                # Combine date and time to create a datetime object for calculation
                start_datetime = datetime.combine(new_job.date, new_job.start_time)
                end_datetime = start_datetime + timedelta(minutes=job.customer.default_duration_minutes)
                new_job.end_time = end_datetime.time()
            else:
                # Fallback to old duration if no default is set for the customer
                new_job.end_time = job.end_time

            # The new job should inherit the customer's default recurrence settings
            new_job.recurrence_type = job.customer.default_recurrence_type
            new_job.recurrence_frequency = job.customer.default_recurrence_frequency

            new_job.save()
            # Ensure staff are carried over to the new job
            new_job.staff.set(job.staff.all())

            # Mark the original job as non-recurring so this logic isn't triggered again
            # from this specific job instance.
            job.recurrence_type = 'none'
            job.save()

    # Preserve the view type and date filter on redirect
    selected_date_str = job.date.strftime('%Y-%m-%d')
    view_type = request.GET.get('view_type', 'day') # 'week' or 'day'
    return redirect(f"/?view_type={view_type}&date={selected_date_str}")
