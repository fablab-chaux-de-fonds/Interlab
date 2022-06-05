import dateparser

from distutils.command.clean import clean
from tkinter import Widget
from django.forms import ModelForm
from .models import OpeningSlot
from tempus_dominus.widgets import DateTimePicker

options={
    'icons':{
        'time': 'bi bi-clock',
        'date': 'bi bi-calendar',
        'up': 'bi bi-arrow-up',
        'down': 'bi bi-arrow-down',
        'previous': 'bi bi-chevron-left',
        'next': 'bi bi-chevron-right',
        'today': 'bi bi-calendar-check-o',
        'clear': 'bi bi-trash',
        'close': 'bi bi-times'  

    },
    'viewMode': 'times',
    'format': "dddd D MMMM HH:mm"
} 

class CreateOpeningForm(ModelForm):

    class Meta:
        model = OpeningSlot
        fields = ['opening', 'start', 'end', 'comment']
        widgets = {
            'start': DateTimePicker(options=options),
            'end': DateTimePicker(options=options)
        }
        