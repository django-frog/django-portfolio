"""Project-wide custom template tags and filters."""

from __future__ import annotations

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
import markdown as _markdown

from core.models import Skill

register = template.Library()


@register.simple_tag
def skill_layers(skills):
    """Group a queryset/list of ``Skill`` instances by technical-stack layer.

    Returns a list of dicts ``{"key", "label", "icon", "skills"}`` in the
    prescribed display order. Empty layers are omitted so the template
    never renders an empty card.
    """
    grouped: dict[str, list] = {}
    for skill in skills:
        layer_key = skill.get_layer()
        grouped.setdefault(layer_key, []).append(skill)

    layers = []
    for key in Skill.LAYER_ORDER:
        members = grouped.get(key)
        if not members:
            continue
        layers.append(
            {
                "key": key,
                "label": Skill.LAYER_LABELS[key],
                "icon": Skill.LAYER_ICONS[key],
                "skills": members,
            }
        )
    return layers


@register.filter(name="markdown")
def markdown_filter(value):
    """Render a Markdown string to safe HTML.

    Uses the ``markdown`` library to convert Markdown to HTML, then
    escapes any raw HTML embedded inside the source so the result is
    safe to mark as safe in templates. This produces native lists,
    bold/italic and links without allowing untrusted raw HTML through.

    Usage:
        {{ experience.description|markdown|safe }}
    """
    if not value:
        return ""

    safe_source = escape(str(value))

    html = _markdown.markdown(
        safe_source,
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html5",
    )

    return mark_safe(html)


@register.filter(name="get_item")
def get_item(dictionary, key):
    """Allow dictionary lookups with a variable key in templates.

    Usage:
        {{ my_dict|get_item:my_key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""
