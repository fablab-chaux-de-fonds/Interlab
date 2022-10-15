import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _


from .models import Training, ToolTraining
from fabcal.models import TrainingSlot


def trainings_list(request):
    trainings = Training.objects.all()

    return render(request, 'trainings/list.html', {'trainings': trainings})

def training_show(request, pk):
    training = get_object_or_404(Training, pk=pk)

    if request.user.is_authenticated:
        notification = training.notification.filter(user = request.user).exists()
        if request.method == 'POST':
            if notification:
                # user has already the notification and want to unsuscribe
                training.notification.remove(request.user.profile)
                messages.success(request, _("Oh no! you unsubsribe from notification"))
            else:
                training.notification.add(request.user.profile)
                messages.success(request, _("Thanks for interest, we will contact you as soon as possible"))
            
            #update notification variable 
            notification = training.notification.filter(user = request.user).exists()

    else: 
        notification = False

    training_slots = TrainingSlot.objects.filter(training__pk = pk, start__gte=datetime.datetime.now())
    tools = [tool_training.tool for tool_training in ToolTraining.objects.filter(training__pk=pk).order_by('sort')]

    context = {
        'training': training,
        'training_slots': training_slots,
        'machines': training.machines_list,
        'tools': tools,
        'notification': notification
        }

    return render(request, 'trainings/show.html', context)

