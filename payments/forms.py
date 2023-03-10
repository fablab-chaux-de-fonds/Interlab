from django import forms

class CreateCheckoutSessionForm(forms.Form):
    category_id = forms.IntegerField(required=True)