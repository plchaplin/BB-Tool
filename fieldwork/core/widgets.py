from django import forms
from datetime import time, timedelta, datetime, date

class TimeSelectWidget(forms.Select):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.choices = self.generate_time_choices()

    def generate_time_choices(self):
        choices = []
        current_time = time(8, 0)
        end_time = time(18, 0)

        while current_time <= end_time:
            choices.append((current_time.strftime('%H:%M'), current_time.strftime('%H:%M')))
            current_time = (datetime.combine(date.today(), current_time) + timedelta(minutes=15)).time()

        return choices
