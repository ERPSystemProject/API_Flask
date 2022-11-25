# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys

import flask
from flask_restx import Api, Resource, Namespace, fields, reqparse

import requests
import json
import yaml

user_ns = Namespace('User', version="1.0", title='User API List', description='User API List')

user_authority_fields = user_ns.model('user authority',{
    'community_board_flag':fields.Integer(description='community board authority', required=True, example=1),
    'goods_management_flag':fields.Integer(description='goods management authority', required=True, example=1),
    'consignment_management_flag':fields.Integer(description='consignment management authority', required=True, example=1),
    'move_management_flag':fields.Integer(description='move management authority', required=True, example=1),
    'sell_management_flag':fields.Integer(description='sell management authority', required=True, example=1),
    'remain_management_flag':fields.Integer(description='remain management authority', required=True, example=1),
    'sale_management_flag':fields.Integer(description='sale management authority', required=True, example=1),
    'system_management_flag':fields.Integer(description='system management authority', required=True, example=1),
    'user_authority_management_flag':fields.Integer(description='user authority management authority', required=True, example=1)
})

user_login_response_fields = user_ns.model('Login Response Body', {
    'result':fields.String(description='login result', required=True, example='SUCCESS'),
    'userId':fields.String(description='user id',required=True,example='admin'),
    'token':fields.String(description='JWT token',required=True,example='token'),
    'authority':fields.Nested(user_authority_fields)})

user_login_request_fields = user_ns.model('Login Request Body',{
    'id':fields.String(description='user id', required=True, example='admin'),
    'password':fields.String(description='user password', required=True, example='0000')
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['user_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@user_ns.route('/login')
class login(Resource):

    @user_ns.doc(body=user_login_request_fields)
    @user_ns.response(201, 'OK', user_login_response_fields)
    @user_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def post(self):
        '''
        login request
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/login", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code