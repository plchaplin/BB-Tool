from django.shortcuts import render
from .models import Job
from datetime import date, datetime

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
    jobs = Job.objects.filter(start_time__date=selected_date).order_by('start_time')

    context = {
        'jobs': jobs,
        'selected_date': selected_date,
    }
    return render(request, 'core/dashboard.html', context)
