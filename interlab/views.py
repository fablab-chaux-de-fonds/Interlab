from django.http import HttpResponse
from django.template import loader
from django.views.generic.edit import FormView

class CustomFormView(FormView):
    success_url = '/schedule/'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for field in context['form'].fields:
            if not 'class' in context['form'][field].field.widget.attrs:
                context['form'][field].field.widget.attrs['class'] = 'form-control'

            if context['form'][field].widget_type == 'select':
                context['form'][field].field.widget.attrs['class'] += ' form-select'
        return context

    def form_invalid(self, form):
        for field in form.errors:
            if field != '__all__':
                form[field].field.widget.attrs['class'] = 'form-control is-invalid'
        return super().form_invalid(form)

def bootstrap(request):
    template = loader.get_template('bootstrap.html')
    context = {}
    return HttpResponse(template.render(context, request))

def schedule(request):
    template = loader.get_template('vuejs.html')
    context = {}
    return HttpResponse(template.render(context, request))

def error_500(request):
    template = loader.get_template('500.html')
    context = {}
    return HttpResponse(template.render(context, request))