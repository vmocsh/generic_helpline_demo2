from django import forms
#from management.models import HelperCategory
#from ivr.models import Language
from .service import convert_queryset_to_list_of_tuples

#LANGUAGE_CHOICES = convert_queryset_to_list_of_tuples(Language.objects.all())
#CATEGORY_CHOICES = convert_queryset_to_list_of_tuples(HelperCategory.objects.all())


class ContactForm(forms.Form):
    name = forms.CharField(label='name', max_length=100, required=True)
    otp = forms.CharField(label='otp', max_length=10, required=True)
    contact = forms.CharField(label='phone', max_length=15, required=False)
    location = forms.CharField(label='location', max_length=100, required=True)
    #language = forms.ChoiceField(label='language', required=True, widget=forms.RadioSelect,
    #                             choices=LANGUAGE_CHOICES)
    #category = forms.ChoiceField(label='category', required=True, widget=forms.RadioSelect,
    #                             choices=CATEGORY_CHOICES)
    previous_messages = forms.CharField(label='previous_messages', required=False, max_length=1000)
    message = forms.CharField(label='message', max_length=100, required=True)
    files = forms.ImageField(label='files', required=False, allow_empty_file=True)
