from django.http import HttpResponse
from django.template import loader
from django.views.generic.edit import FormView

class CustomFormView(FormView):
    success_url = '/schedule/'

    def get(self, request, *args, **kwargs):
        # Store the previous URL in the session
        self.request.session['prev_url'] = self.request.META.get('HTTP_REFERER', '/')
        return super().get(request, *args, **kwargs)
        
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

def error_500(request):
    template = loader.get_template('500.html')
    context = {}
    return HttpResponse(template.render(context, request))