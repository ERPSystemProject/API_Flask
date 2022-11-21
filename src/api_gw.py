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

import user_resource
import community_resource
import system_resource

flask_app = flask.Flask(__name__)
CORS(flask_app)
api = Api(app=flask_app,
          version='0.1',
          title='ERP System API Server',
          description='ERP System API List Description',
          terms_url='/ERPSystem/v1.0',
          contact='tjwnsgh34@gmail.com',
          license='MIT')
flask_app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

api.add_namespace(user_resource.user_ns, path='/ERPSystem/v1.0/users')
api.add_namespace(community_resource.community_ns, path='/ERPSystem/v1.0/community')
api.add_namespace(system_resource.system_ns, path='/ERPSystem/v1.0/system')

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