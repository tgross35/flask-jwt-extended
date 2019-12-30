import pytest
from flask import Flask
from flask import jsonify

from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user
from flask_jwt_extended import get_current_user
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from tests.utils import get_jwt_manager
from tests.utils import make_headers


@pytest.fixture(scope="function")
def app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "foobarbaz"
    JWTManager(app)

    @app.route("/get_user1", methods=["GET"])
    @jwt_required()
    def get_user1():
        return jsonify(foo=get_current_user()["username"])

    @app.route("/get_user2", methods=["GET"])
    @jwt_required()
    def get_user2():
        return jsonify(foo=current_user["username"])

    return app


@pytest.mark.parametrize("url", ["/get_user1", "/get_user2"])
def test_load_valid_user(app, url):
    jwt = get_jwt_manager(app)

    @jwt.user_loader_callback_loader
    def user_load_callback(identity):
        return {"username": identity}

    test_client = app.test_client()
    with app.test_request_context():
        access_token = create_access_token("username")

    response = test_client.get(url, headers=make_headers(access_token))
    assert response.status_code == 200
    assert response.get_json() == {"foo": "username"}


@pytest.mark.parametrize("url", ["/get_user1", "/get_user2"])
def test_load_invalid_user(app, url):
    jwt = get_jwt_manager(app)

    @jwt.user_loader_callback_loader
    def user_load_callback(identity):
        return None

    test_client = app.test_client()
    with app.test_request_context():
        access_token = create_access_token("username")

    response = test_client.get(url, headers=make_headers(access_token))
    assert response.status_code == 401
    assert response.get_json() == {"msg": "Error loading the user username"}


@pytest.mark.parametrize("url", ["/get_user1", "/get_user2"])
def test_custom_user_loader_errors(app, url):
    jwt = get_jwt_manager(app)

    @jwt.user_loader_callback_loader
    def user_load_callback(identity):
        return None

    @jwt.user_loader_error_loader
    def user_loader_error(identity):
        return jsonify(foo="bar"), 201

    test_client = app.test_client()
    with app.test_request_context():
        access_token = create_access_token("username")

    response = test_client.get(url, headers=make_headers(access_token))
    assert response.status_code == 201
    assert response.get_json() == {"foo": "bar"}
