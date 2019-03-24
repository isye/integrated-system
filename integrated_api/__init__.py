import os
from flask import Flask
from flask_cors import CORS

def create_app(config_file = 'config.py'):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile(config_file)
    app.secret_key = os.getenv("SECRET_KEY","")
    allow_origins = os.getenv("ALLOW_ORIGIN",'')
    CORS(app, resources={r"/api/*": {"origins": allow_origins}})

    app.secret_key = os.getenv("API_SECRET_KEY","")
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    try:
        os.makedirs(app.instance_path)
        print('makedir')
    except OSError:
        pass

    @app.route('/')
    def index():
        return 'API'

    from integrated_api import event
    app.register_blueprint(event.bp)

    app.add_url_rule('/persons/', endpoint='persons')
    app.add_url_rule('/persons/<string:personID>', endpoint='retrieve_person')

    app.add_url_rule('/calendars/', endpoint='calendars')
    app.add_url_rule('/scheduled_events/', endpoint='scheduled_events')

    from integrated_api import landingPage
    app.register_blueprint(landingPage.bp)
    app.add_url_rule('/live-events/<string:eventType>', endpoint='live_events')
    app.add_url_rule('/email-verification/', endpoint='email_verification')

    return app

app = create_app()