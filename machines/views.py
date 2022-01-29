from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import ugettext as _
from django.contrib.admin.views.decorators import staff_member_required


from .models import Training
from .forms import TrainingForm


def trainings_list(request):
    trainings = Training.objects.all()

    return render(request, 'trainings/list.html', {'trainings': trainings})


@staff_member_required
def training_edit(request, pk=None):
    try:
        obj = Training.objects.get(pk=pk)
    except Training.DoesNotExist:  # Creation
        obj = Training()

    if request.method == 'POST':
        # Update
        form = TrainingForm(request.POST, request.FILES, instance=obj)

        if form.is_valid():
            obj = form.save()

            msg = _('Training updated!') if pk else _('Training created!')
            messages.success(request, msg)

            return redirect('machines:trainings.show', obj.pk)

    else:
        form = TrainingForm(instance=obj)

    return render(request, 'trainings/edit.html', {'form': form})


def training_show(request, pk):
    pass

