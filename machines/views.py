from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.contrib.admin.views.decorators import staff_member_required


from .models import Faq, Training


def trainings_list(request):
    trainings = Training.objects.all()

    return render(request, 'trainings/list.html', {'trainings': trainings})

def training_show(request, pk):
    obj = get_object_or_404(Training, pk=pk)

    return render(request, 'trainings/show.html', {'obj': obj})

