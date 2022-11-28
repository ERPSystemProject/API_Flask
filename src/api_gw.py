# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys

# flask module
#from flask import Flask, request, jsonify, make_response
import flask
from flask_restx import Api, Resource, Namespace
from flask_cors import CORS, cross_origin
#import flask_cors CORS, cross_origin

import logging
import logging.config
import logging.handlers as handlers

import requests
import json
import yaml
from multiprocessing import Process
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import JWTManager
from flask_jwt_extended import set_access_cookies

import user_resource
import community_resource
import system_resource
import goods_resource
import etc_resource
from datetime import datetime
from datetime import timedelta
from datetime import timezone

flask_app = flask.Flask(__name__)
CORS(flask_app)
authorizations = {
    'JWT' : {
        'type' : 'apiKey',
        'in' : 'header',
        'name' : 'Authorization'
    }
}
api = Api(app=flask_app,
          version='0.1',
          title='ERP System API Server',
          description='ERP System API List Description',
          terms_url='/ERPSystem/v1.0',
          contact='tjwnsgh34@gmail.com',
          license='MIT',
          authorizations=authorizations,
          security='JWT')
flask_app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
flask_app.config.update(
			DEBUG = True,
			JWT_SECRET_KEY = "WATERIN"
		)

jwt = JWTManager(flask_app)

api.add_namespace(user_resource.user_ns, path='/ERPSystem/v1.0/users')
api.add_namespace(community_resource.community_ns, path='/ERPSystem/v1.0/community')
api.add_namespace(goods_resource.goods_ns, path='/ERPSystem/v1.0/goods')
api.add_namespace(system_resource.system_ns, path='/ERPSystem/v1.0/system')
api.add_namespace(etc_resource.etc_ns, path='/ERPSystem/v1.0/etc')

# Using an `after_request` callback, we refresh any token that is within 30
# minutes of expiring. Change the timedeltas to match the needs of your application.
@flask_app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=15))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response

def setup_api_server():
    try:
        # config 파일 읽기
        f = open('../config/config.yaml')
        config = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
        process_config = config['api_gw']
        log_config = config['LOG']

        #LogWriter 설정
        log_filename = log_config['filepath'] + "api_gw.log"
        log_format = log_config['format']
        log_level = log_config['level']
        if log_level == 'CRITICAL':
            log_level = logging.CRITICAL
        elif log_level == 'ERROR':
            log_level = logging.ERROR
        elif log_level == 'WARNING':
            log_level = logging.WARNING
        elif log_level == 'INFO':
            log_level = logging.INFO
        elif log_level == 'DEBUG':
            log_level = logging.DEBUG
        else:
            log_level = logging.NOTSET

        logging.basicConfig(filename = log_filename,
                            filemode = "w",
                            format = log_format,
                            level = log_level)
        logWriter = logging.getLogger()

        #api 서버 시작
        server_ip = process_config['ip']
        server_port = process_config['port']

        flask_app.run(debug=True, host=server_ip, port=server_port)

    except Exception as e:
        sys.exit(f"Api setting failed...\n{e}")

if __name__ == '__main__':

    setup_api_server()