from django import template

register = template.Library()

@register.filter
def number_format(value):
    try:
        # Convert the value to a float and format with commas and 2 decimal places
        return "{:,.2f}".format(float(value)).replace(".", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value
