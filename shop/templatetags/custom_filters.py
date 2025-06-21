from django import template

register = template.Library()

@register.filter
def div(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    try:
        return int(value) * int(arg)
    except ValueError:
        return 0
    

@register.filter(name='dict_get')
def dict_get(dictionary, key):
    """Lug‘atdan kalit bo‘yicha qiymat olish"""
    return dictionary.get(key, 0) 

@register.filter
def mul(value, arg):
    """ Template filter for multiplying two numbers """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    


@register.filter
def human_format(value):
    try:
        value = float(value)
        if value >= 1_000_000_000:
            return f'{value / 1_000_000_000:.1f}mlrd'
        elif value >= 1_000_000:
            return f'{value / 1_000_000:.1f}mln'
        elif value >= 1_000:
            return f'{value / 1_000:.1f}ming'
        else:
            return str(value)
    except (ValueError, TypeError):
        return value