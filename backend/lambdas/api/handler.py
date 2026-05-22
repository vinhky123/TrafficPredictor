from aws_lambda_wsgi import response
from backend.app import create_app
from backend.app.config import Settings

settings = Settings.from_env()
app = create_app(settings)


def handler(event, context):
    return response(app, event, context)
