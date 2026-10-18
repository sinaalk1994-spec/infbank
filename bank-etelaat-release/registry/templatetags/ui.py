from django import template
register=template.Library()
@register.filter
def fa(value): return str(value).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
@register.filter
def money(value):
    try: return fa(f'{int(value):,}')
    except (TypeError,ValueError): return '—'
@register.filter
def initials(value): return ''.join(p[0] for p in str(value).split()[:2])
