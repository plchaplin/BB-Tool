from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
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

    if request.user.is_superuser:
        selected_staff_id = request.GET.get('staff_id', 'all')
    else:
        selected_staff_id = str(request.user.id)

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = date.today()

    # Base queryset for jobs
    jobs = Job.objects.prefetch_related('staff', 'customer', 'logs', 'logs__author').all()

    # Filter jobs based on user type
    if request.user.is_superuser:
        if selected_staff_id and selected_staff_id != 'all':
            try:
                jobs = jobs.filter(staff__id=int(selected_staff_id))
            except (ValueError, TypeError):
                pass
    else:
        jobs = jobs.filter(staff=request.user)

    # Filter by date range
    if view_type == 'week':
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        jobs_for_period = jobs.filter(date__range=[start_of_week, end_of_week]).order_by('date', 'start_time')
        date_display = f"{start_of_week.strftime('%d-%m-%Y')} to {end_of_week.strftime('%d-%m-%Y')}"
    else:  # Day view
        jobs_for_period = jobs.filter(date=selected_date).order_by('start_time')
        date_display = selected_date.strftime('%d-%m-%Y')

    staff_list = User.objects.filter(staffprofile__isnull=False).order_by('first_name', 'last_name')

    # --- Day View Specific Logic ---
    events = []
    staff_availability = []
    if view_type == 'day':
        day_jobs = jobs_for_period
        conflicting_job_ids = set()
        staff_schedules = defaultdict(list)
        for job in day_jobs:
            for staff in job.staff.all():
                staff_schedules[staff.id].append(job)

        for staff_id, staff_jobs in staff_schedules.items():
            sorted_jobs = sorted(staff_jobs, key=lambda j: j.start_time)
            for i in range(1, len(sorted_jobs)):
                if sorted_jobs[i].start_time < sorted_jobs[i-1].end_time:
                    conflicting_job_ids.add(sorted_jobs[i-1].id)
                    conflicting_job_ids.add(sorted_jobs[i].id)

        for staff_member in staff_list:
            jobs_today = staff_schedules.get(staff_member.id, [])
            total_duration_seconds = sum((datetime.combine(date.min, j.end_time) - datetime.combine(date.min, j.start_time)).total_seconds() for j in jobs_today if j.start_time and j.end_time)

            allocated_hours = total_duration_seconds / 3600
            day_name = selected_date.strftime('%A').lower()
            hours_field_name = f'hours_{day_name}'
            contracted_hours = float(getattr(staff_member.staffprofile, hours_field_name, 0))
            unallocated_hours = contracted_hours - allocated_hours

            staff_availability.append({
                'name': staff_member.get_full_name() or staff_member.username,
                'allocated_hours': round(allocated_hours, 2),
                'contracted_hours': contracted_hours,
                'unallocated_hours': round(unallocated_hours, 2)
            })
        staff_availability.sort(key=lambda x: x['unallocated_hours'], reverse=True)

        for job in day_jobs:
            if job.date and job.start_time and job.end_time:
                staff_names = ", ".join([s.get_full_name() or s.username for s in job.staff.all()])
                title = f"{job.customer.name} ({job.get_job_type_display()}) - {staff_names}"

                address = f"{job.customer.street}, {job.customer.town}, {job.customer.postcode}"
                logs = [{'timestamp': log.timestamp.strftime('%d-%m-%Y %H:%M'), 'author': log.author.get_full_name() or log.author.username if log.author else "Unknown", 'note': log.note} for log in job.logs.all()]

                event_data = {
                    'id': job.id,
                    'title': title,
                    'start': datetime.combine(job.date, job.start_time).isoformat(),
                    'end': datetime.combine(job.date, job.end_time).isoformat(),
                    'extendedProps': {
                        'job_id': job.id, 'description': job.description, 'customer_name': job.customer.name,
                        'address': address, 'status': job.status, 'status_display': job.get_status_display(),
                        'logs': logs, 'update_url': reverse('update_job_status', args=[job.id])
                    }
                }
                if job.id in conflicting_job_ids:
                    event_data['color'] = '#dc3545'
                events.append(event_data)

    # --- Potential Jobs Calculation ---
    customers_with_future_jobs = Customer.objects.filter(job__date__gte=date.today(), job__status__in=['scheduled', 'in_progress']).distinct()
    potential_job_customers = Customer.objects.exclude(id__in=customers_with_future_jobs.values_list('id', flat=True))

    context = {
        'jobs': jobs_for_period,
        'selected_date': selected_date, 'view_type': view_type, 'date_display': date_display,
        'status_choices': Job.STATUS_CHOICES, 'events_json': events, 'staff_list': staff_list,
        'selected_staff_id': selected_staff_id, 'staff_availability': staff_availability,
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

        # If the job is completed, create the next recurring job if applicable
        if job.status == 'completed':
            customer_recurrence_type = job.customer.default_recurrence_type
            customer_recurrence_freq = job.customer.default_recurrence_frequency

            if customer_recurrence_type != 'none':
                new_job = job
                new_job.pk = None

                delta = None
                if customer_recurrence_type == 'weekly':
                    delta = timedelta(weeks=customer_recurrence_freq)
                elif customer_recurrence_type == 'monthly':
                    delta = relativedelta(months=customer_recurrence_freq)

                if delta:
                    new_job.date = job.date + delta
                    new_job.status = 'scheduled'
                    new_job.start_time = job.start_time

                    if job.customer.default_duration_minutes:
                        start_datetime = datetime.combine(new_job.date, new_job.start_time)
                        end_datetime = start_datetime + timedelta(minutes=job.customer.default_duration_minutes)
                        new_job.end_time = end_datetime.time()
                    else:
                        new_job.end_time = job.end_time

                    new_job.recurrence_type = customer_recurrence_type
                    new_job.recurrence_frequency = customer_recurrence_freq
                    new_job.save()
                    new_job.staff.set(job.staff.all())

                    job.recurrence_type = 'none'
                    job.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'new_status': job.status,
            'new_status_display': job.get_status_display(),
        })
    else:
        selected_date_str = job.date.strftime('%Y-%m-%d')
        view_type = request.GET.get('view_type', 'day')
        return redirect(f"/?view_type={view_type}&date={selected_date_str}")
