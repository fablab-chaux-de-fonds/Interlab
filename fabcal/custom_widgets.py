from django.forms.widgets import NumberInput
from django.utils.safestring import mark_safe

class NumberInputWithButtons(NumberInput):
    template_name = 'fabcal/widgets/number_input_with_buttons.html'
    
    def __init__(self, attrs=None):
        default_attrs = {'min': '0', 'value': '0'}
        if attrs:
            default_attrs.update(attrs) 
        super().__init__(attrs=default_attrs)