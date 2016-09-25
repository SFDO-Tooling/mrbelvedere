from django import template
from django.conf import settings

register = template.Library()

@register.inclusion_tag('site_logo.html')
def site_logo_header():
    return {
        'logo_image': settings.SITE_LOGO_IMAGE_URL,
        'logo_url': settings.SITE_LOGO_LINK_URL,
        'logo_alt': settings.SITE_LOGO_ALT_TEXT,
    }
