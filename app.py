""" A flask server that implements Json Web Token authorization.
    Includes endpoints to get/revoke tokens and search through
    the MongoDB database.
"""
import os
import uuid
import requests
from bson import json_util
from dotenv import load_dotenv
from database import connection
from flask_sqlalchemy import SQLAlchemy
from flask import (Flask, make_response,
                   request, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                jwt_required, get_jwt, JWTManager)


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config["JWT_ALGORITHM"] = "HS256"

jwt = JWTManager(app)
db = SQLAlchemy(app)
_conf = connection.MongoDB()


class RevokedTokenModel(db.Model):
    """ This class checks if the token currently used is blacklisted.
        The token is blacklisted after it has been revoked.
    """

    __tablename__ = 'revoked_tokens'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self) -> None:
        """ Adds the token to the DB when called
        """
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        # Query the created SQLAlchemy db containing the revoked tokens
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)


class User():
    """ This class created a Used object.
        The user is the one who can generate a token
        to be able to use the API
    """
    def __init__(self, public_id, name, password) -> None:
        self.public_id = public_id
        self.name = name
        self.password = password

    def __dict__(self) -> dict:
        return {
            "public_id": self.public_id,
            "name": self.name,
            "password": self.password
        }


@app.before_first_request
def create_tables():
    """ Before the first request, after the server is started,
        this functions creates the Tokens db in instance/app.db
    """
    db.create_all()


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload) -> RevokedTokenModel:
    # returns whether the token is blackliset or not after checking in the db
    # upon each request
    jti = jwt_payload['jti']
    return RevokedTokenModel.is_jti_blacklisted(jti)


@app.route('/submit-urls', methods=['POST'])
@jwt_required()
def submit():
    urls = request.json[0]['urls']
    if urls:
        if not os.path.exists('urls.txt'):
            os.mkdir('url.txt')

        with open('urls.txt', 'w') as f:
            for url in urls:
                f.write(f'{url}\n')

        return make_response('Saved URLs to urls.txt', 200,
                             {'message': "Success"})
    else:
        return make_response('No URLs were sent', 400,
                             {'message': 'Please send URLs'})


@app.route("/scrape")
@jwt_required()
def scrape():
    params = {
        'spider_name': 'news_crawler',
        'start_requests': 'true'
    }
    response = requests.get('http://localhost:9080/crawl.json', params=params)
    return make_response(f'{response}', 200,
                         {'message': "Success"})


@app.route('/api/get-all')
@jwt_required()
def get_all():

    client = _conf.connect_to_DB()
    db = client.BBC
    collection = db.articles
    document_cursor = collection.find()
    result = list(document_cursor)
    client.close()
    if result:
        return make_response(json_util.dumps({'data': result},
                                             indent=4,
                                             ensure_ascii=False),
                             200, {'message': 'Success'})
    else:
        return make_response('Result not found', 404,
                             {'message': 'Collection is empy'})


@app.route('/api/filter-by-date')
@jwt_required()
def filter_by_date():
    args = request.args
    year = args.get("year")
    month = args.get("month")
    day = args.get("day")
    if year and month and day:
        query = {
            "created_at.year": int(year),
            "created_at.month": int(month),
            "created_at.day": int(day)
        }
    elif year and month:
        query = {
            "created_at.year": int(year),
            "created_at.month": int(month),
        }
    elif year:
        query = {
            "created_at.year": int(year),
        }
    else:
        return make_response(
            'You can only search by: year, year-month, or year-month-day.',
            400, {'message': 'Wrong request format'}
        )

    client = _conf.connect_to_DB()
    db = client.BBC
    collection = db.articles
    document_cursor = collection.find(query)
    result = list(document_cursor)
    client.close()
    if result:
        return make_response(json_util.dumps({'data': result},
                                             indent=4,
                                             ensure_ascii=False),
                             200, {'message': 'Success'})
    else:
        return make_response('Result not found', 404,
                             {'message': 'No records match the query'})


@app.route('/api/search-by-tags')
@jwt_required()
def search_by_tags():
    args = request.args
    tags = args.get("tags")
    tags_list = tags.split(',') if tags else []
    if not tags_list:
        return make_response(
            'Specify comma seperated values',
            400, {'message': 'Wrong request format'}
        )

    result = []

    client = _conf.connect_to_DB()
    db = client.BBC
    collection = db.articles
    for tag in tags_list:
        query = {"tags": {
                    '$regex': tag,
                    '$options': 'i'
                }
            }
        document_cursor = collection.find(query)
        list_cursor = list(document_cursor)
        [result.append(rec) for rec in list(list_cursor)]
    client.close()
    if result:
        return make_response(json_util.dumps({'data': result},
                                             indent=4,
                                             ensure_ascii=False),
                             200, {'message': 'Success'})
    else:
        return make_response('Result not found', 404,
                             {'message': 'No records match the query'})


@app.route('/api/search-by-keywords')
@jwt_required()
def search_by_keywords():
    args = request.args
    keywords = args.get("keywords")
    keywords_list = keywords.split(',') if keywords else []
    if not keywords_list:
        return make_response(
            'Specify comma seperated values',
            400, {'message': 'Wrong request format'}
        )

    result = []

    client = _conf.connect_to_DB()
    db = client.BBC
    collection = db.articles
    for keyword in keywords_list:
        query = {"text": {
                    '$regex': keyword,
                    '$options': 'i'
                }
            }
        document_cursor = collection.find(query)
        list_cursor = list(document_cursor)
        [result.append(rec) for rec in list(list_cursor)]
    client.close()
    if result:
        return make_response(json_util.dumps({'data': result},
                                             indent=4,
                                             ensure_ascii=False),
                             200, {'message': 'Success'})
    else:
        return make_response('Result not found', 404,
                             {'message': 'No records match the query'})


@app.route('/token/generate', methods=['POST'])
def token_generate():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401,
                             {'WWW-Authenticate': 'Login required!'})

    client = _conf.connect_to_DB()
    db = client.BBC
    collection = db.Users
    query = {
             "name": auth.username
             }
    document_cursor = collection.find(query)
    user = list(document_cursor)
    client.close()
    if not user:
        return make_response('Could not verify', 401,
                             {'WWW-Authenticate': 'Login required!'})

    if check_password_hash(user[0]['password'], auth.password):
        access_token = create_access_token(identity=user[0]['public_id'])
        refresh_token = create_refresh_token(identity=user[0]['public_id'])

        return jsonify({
            'message': 'Logged in as {}'.format(user[0]['name']),
            'access_token': access_token,
            'refresh_token': refresh_token
        })

    return make_response('Could not verify', 401,
                         {'WWW-Authenticate': 'Login required!'})


@app.route('/token/revoke', methods=['POST'])
@jwt_required()
def token_revoke():
    jti = get_jwt()['jti']
    try:
        revoked_token = RevokedTokenModel(jti=jti)
        revoked_token.add()
        return {'message': 'Access token has been revoked'}
    except Exception as e:
        return {'message': 'Something went wrong'}, 500


@app.route('/user/register', methods=['POST'])
@jwt_required()
def create_user():
    client = _conf.connect_to_DB()
    db = client.BBC
    collection = db.Users

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()),
                    name=data['name'],
                    password=hashed_password).__dict__()
    query = {
             "name": new_user['name']
             }
    document_cursor = collection.find(query)

    if list(document_cursor):
        client.close()
        return make_response('Could not register', 409,
                             {"name": "name already exists!"})

    collection.insert_one(new_user)

    client.close()

    return jsonify({'message': 'New user created!'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
