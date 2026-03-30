from jinja2 import Environment, FileSystemLoader
from app.config import settings

env = Environment(loader=FileSystemLoader("templates/email"))


def render_email_template(template_name, context):
    template = env.get_template(template_name)
    return template.render(context)


def render_telegram_card(template_name, **kwargs):
    # This could be extended for Telegram specific formats later
    # For now, it's just a placeholder
    return f"Card template: {template_name}"
