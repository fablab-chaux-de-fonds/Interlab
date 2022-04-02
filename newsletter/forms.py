from django import forms

class RegisterForm(forms.Form):
    email = forms.EmailField(help_text='Your mail', widget=forms.HiddenInput())

def newsletter_context(request):
    return {'newsletter_form':RegisterForm()}