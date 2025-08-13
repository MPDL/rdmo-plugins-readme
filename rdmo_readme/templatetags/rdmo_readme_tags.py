from django import template

register = template.Library()

@register.inclusion_tag('plugins/dataset_block.html', takes_context=True)
def render_dataset_block(context, dataset, language_code):
    context['dataset'] = dataset
    context['language_code'] = language_code
    return context