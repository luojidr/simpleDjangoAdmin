from django import template
from auditlog.models import LogEntry

register = template.Library()


class AuditLogNode(template.Node):
    def __init__(self, limit, varname, user):
        self.limit, self.varname, self.user = limit, varname, user

    def __repr__(self):
        return "<AuditLog Node>"

    def render(self, context):
        if self.user is None:
            entries = LogEntry.objects.all()
        else:
            actor_id = self.user

            if not actor_id.isdigit():
                actor_id = context[self.user].pk
            entries = LogEntry.objects.filter(actor__pk=actor_id)

        actions = {
            LogEntry.Action.CREATE: "创建",
            LogEntry.Action.UPDATE: "修改",
            LogEntry.Action.DELETE: "删除",
            LogEntry.Action.ACCESS: "访问",
        }
        queryset = entries.select_related("content_type", "actor")[:int(self.limit)]

        for entry in queryset:
            entry.action_cn = actions[entry.action]

        context[self.varname] = queryset
        return ""


@register.tag
def get_audit_log(parser, token):
    """
    Populate a template variable with the audit log for the given criteria.

    Usage::

        {% get_audit_log [limit] as [varname] for_user [context_var_with_user_obj] %}

    Examples::

        {% get_admin_log 10 as audit_log for_user 23 %}
        {% get_admin_log 10 as audit_log for_user user %}
        {% get_admin_log 10 as audit_log %}

    Note that ``context_var_containing_user_obj`` can be a hard-coded integer
    (user ID) or the name of a template context variable containing the user
    object whose ID you want.
    """
    tokens = token.contents.split()
    if len(tokens) < 4:
        raise template.TemplateSyntaxError(
            "'audit_log' statements require two arguments"
        )
    if not tokens[1].isdigit():
        raise template.TemplateSyntaxError(
            "First argument to 'audit_log' must be an integer"
        )
    if tokens[2] != "as":
        raise template.TemplateSyntaxError(
            "Second argument to 'audit_log' must be 'as'"
        )
    if len(tokens) > 4:
        if tokens[4] != "for_user":
            raise template.TemplateSyntaxError(
                "Fourth argument to 'audit_log' must be 'for_user'"
            )
    return AuditLogNode(
        limit=tokens[1],
        varname=tokens[3],
        user=(tokens[5] if len(tokens) > 5 else None),
    )
