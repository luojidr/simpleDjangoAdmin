import json
from json.decoder import JSONDecodeError
from django import template

register = template.Library()


class SetVarNode(template.Node):
    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            # tuple or dict
            values = [s.strip() for s in self.var_value.split(',') if s.strip()]
            var_value = ", ".join(values).replace('(', '[').replace(')', ']')

            try:
                value = json.loads(var_value)
            except JSONDecodeError:
                value = ""

        context[self.var_name] = value
        return u""


@register.tag('set')
def do_set(parser, token):
    """
     Usage::
        {% set <var_name>=<var_value> %}

    Examples::
        {% set name='Daniel' %}
        {% set age=1000 %}
        {% set age=1000.23 %}
        {% set user=("name", 102, 1002.3) %}
        {% set user={"age": 200, "name": "mxy"} %}
    """
    bits = token.split_contents()
    parts = [s.strip() for s in "".join(bits[1:]).split('=') if s.strip()]

    if len(parts) < 2:
        raise template.TemplateSyntaxError("'set' tag must be of the form: {% set <var_name>=<var_value> %}")
    return SetVarNode(parts[0], parts[1])
