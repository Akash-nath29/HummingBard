from flask import Flask, render_template, url_for, session, flash, redirect 
from models import db, User, Post
import secrets
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from os import environ as env
from urllib.parse import quote_plus, urlencode

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)

app.config.update({
    'SECRET_KEY': secrets.token_hex(16),
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///database.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'UPLOAD_FOLDER': 'static/uploads',
    # 'MAX_CONTENT_LENGTH': 16 * 1024 * 1024
})

db.init_app(app)
with app.app_context():
    db.create_all()
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    redirect_uri=env.get("AUTH0_CALLBACK_URL"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)
#AUTH
@app.route('/login')
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )
    
@app.route('/callback')
def callback():
    try:
        token = oauth.auth0.authorize_access_token()
        userinfo = oauth.auth0.parse_id_token(token, nonce=session.get('nonce'))
        session["user"] = userinfo
        print(userinfo)
        print(session["user"])
        print(userinfo)

        # Check if the user already exists in the local database
        user = User.query.filter_by(email=userinfo['email']).first()

        if not user:
            # If the user doesn't exist, create a new user in the local database
            user = User(username=userinfo['nickname'], email=userinfo['email'], profile_picture=userinfo['picture'])
            db.session.add(user)
            db.session.commit()

        # Store the user information in the session
        session['user'] = userinfo
        user_id = userinfo['sub']

        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error during callback: {str(e)}', 'danger')
        return redirect('/')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
