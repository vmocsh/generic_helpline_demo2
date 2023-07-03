from django import template
from register_helper.models import Helper
register = template.Library()

@register.simple_tag
def helpline_name(request):
    helper = Helper.objects.filter(user=request.user)