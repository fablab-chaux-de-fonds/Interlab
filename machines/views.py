import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.contrib.admin.views.decorators import staff_member_required


from .models import Training, ToolTraining
from fabcal.models import TrainingSlot


def trainings_list(request):
    trainings = Training.objects.all()

    return render(request, 'trainings/list.html', {'trainings': trainings})

def training_show(request, pk):
    training = get_object_or_404(Training, pk=pk)

    training_slots = TrainingSlot.objects.filter(training__pk = pk, start__gte=datetime.datetime.now())
    tools = [tool_training.tool for tool_training in ToolTraining.objects.filter(training__pk=pk).order_by('sort')]

    context = {
        'training': training,
        'training_slots': training_slots,
        'machines': training.machines_list,
        'tools': tools
        }

    return render(request, 'trainings/show.html', context)

