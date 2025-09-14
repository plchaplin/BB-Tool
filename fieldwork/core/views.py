from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Job
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

import json

from django.contrib.auth.models import User


from collections import defaultdict
from django.contrib.auth.models import User


from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Customer, Job


@login_required
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

    # Filter jobs based on user type
    if request.user.is_superuser:
        # Superusers can filter by any staff member from the dropdown
        if selected_staff_id and selected_staff_id != 'all':
            try:
                jobs = jobs.filter(staff__id=int(selected_staff_id))
            except (ValueError, TypeError):
                pass # Invalid staff_id, show all
    else:
        # Regular staff only see their own jobs
        jobs = jobs.filter(staff=request.user)
        # Set this so the context is aware of the filtered user
        selected_staff_id = str(request.user.id)

    # Filter by date range based on the view type
    if view_type == 'week':
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        jobs = jobs.filter(date__range=[start_of_week, end_of_week]).order_by('date', 'start_time')
        date_display = f"{start_of_week.strftime('%d-%m-%Y')} to {end_of_week.strftime('%d-%m-%Y')}"
    else:  # Day view
        jobs = jobs.filter(date=selected_date).order_by('start_time')
        date_display = selected_date.strftime('%d-%m-%Y')

    # Get all staff members for the filter dropdown and availability calculation
    staff_list = User.objects.filter(staffprofile__isnull=False).order_by('first_name', 'last_name')

    # --- Day View Specific Logic ---
    events = []
    staff_availability = []
    if view_type == 'day':
        # --- Conflict Detection & Staff Schedules ---
        conflicting_job_ids = set()
        staff_schedules = defaultdict(list)
        for job in jobs:
            for staff in job.staff.all():
                staff_schedules[staff.id].append(job)

        for staff_id, staff_jobs in staff_schedules.items():
            sorted_jobs = sorted(staff_jobs, key=lambda j: j.start_time)
            for i in range(1, len(sorted_jobs)):
                prev_job = sorted_jobs[i-1]
                current_job = sorted_jobs[i]
                if current_job.start_time < prev_job.end_time:
                    conflicting_job_ids.add(prev_job.id)
                    conflicting_job_ids.add(current_job.id)

        # --- Staff Availability Calculation ---
        for staff_member in staff_list:
            jobs_today = staff_schedules.get(staff_member.id, [])
            total_duration_seconds = 0
            for job in jobs_today:
                if job.start_time and job.end_time:
                    start_dt = datetime.combine(date.min, job.start_time)
                    end_dt = datetime.combine(date.min, job.end_time)
                    total_duration_seconds += (end_dt - start_dt).total_seconds()

            allocated_hours = total_duration_seconds / 3600

            # Get the day name to construct the field name, e.g., 'hours_monday'
            day_name = selected_date.strftime('%A').lower()
            hours_field_name = f'hours_{day_name}'

            # Get the contracted hours for the specific day using getattr
            contracted_hours = float(getattr(staff_member.staffprofile, hours_field_name, 0))

            unallocated_hours = contracted_hours - allocated_hours

            staff_availability.append({
                'name': staff_member.get_full_name() or staff_member.username,
                'allocated_hours': round(allocated_hours, 2),
                'contracted_hours': contracted_hours,
                'unallocated_hours': round(unallocated_hours, 2)
            })
        staff_availability.sort(key=lambda x: x['unallocated_hours'], reverse=True)

        # --- Event Preparation for FullCalendar ---
        for job in jobs:
            if job.date and job.start_time and job.end_time:
                staff_names = ", ".join([s.get_full_name() or s.username for s in job.staff.all()])
                title = f"{job.customer.name} ({job.get_job_type_display()})"
                if staff_names:
                    title += f" - {staff_names}"

                event_data = {
                    'title': title,
                    'start': datetime.combine(job.date, job.start_time).isoformat(),
                    'end': datetime.combine(job.date, job.end_time).isoformat(),
                    'resourceIds': [s.id for s in job.staff.all()]
                }
                if job.id in conflicting_job_ids:
                    event_data['color'] = '#dc3545'

                events.append(event_data)

    # --- Potential Jobs Calculation (independent of view type) ---
    customers_with_future_jobs = Customer.objects.filter(
        job__date__gte=date.today(),
        job__status__in=['scheduled', 'in_progress']
    ).distinct()
    potential_job_customers = Customer.objects.exclude(
        id__in=customers_with_future_jobs.values_list('id', flat=True)
    )

    context = {
        'jobs': jobs,
        'selected_date': selected_date,
        'view_type': view_type,
        'date_display': date_display,
        'status_choices': Job.STATUS_CHOICES,
        'events_json': events,
        'staff_list': staff_list,
        'selected_staff_id': selected_staff_id,
        'staff_availability': staff_availability,
        'potential_job_customers': potential_job_customers,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
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
