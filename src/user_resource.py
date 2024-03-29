# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys

import flask
from flask_restx import Api, Resource, Namespace, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity

import requests
import json
import yaml

user_ns = Namespace('User', version="1.0", title='User API List', description='User API List')

user_authority_fields = user_ns.model('user authority',{
    'community_board_flag':fields.Integer(description='community board authority', required=True, example=1),
    'community_board_1_flag':fields.Integer(description='community board 1 authority', required=True, example=1),
    'community_board_2_flag':fields.Integer(description='community board 2 authority', required=True, example=1),
    'goods_management_flag':fields.Integer(description='goods management authority', required=True, example=1),
    'goods_management_1_flag':fields.Integer(description='goods management 1 authority', required=True, example=1),
    'goods_management_2_flag':fields.Integer(description='goods management 2 authority', required=True, example=1),
    'goods_management_3_flag':fields.Integer(description='goods management 3 authority', required=True, example=1),
    'consignment_management_flag':fields.Integer(description='consignment management authority', required=True, example=1),
    'consignment_management_1_flag':fields.Integer(description='consignment management 1 authority', required=True, example=1),
    'consignment_management_2_flag':fields.Integer(description='consignment management 2 authority', required=True, example=1),
    'consignment_management_3_flag':fields.Integer(description='consignment management 3 authority', required=True, example=1),
    'move_management_flag':fields.Integer(description='move management authority', required=True, example=1),
    'move_management_1_flag':fields.Integer(description='move management 1 authority', required=True, example=1),
    'move_management_2_flag':fields.Integer(description='move management 2 authority', required=True, example=1),
    'move_management_3_flag':fields.Integer(description='move management 3 authority', required=True, example=1),
    'move_management_4_flag':fields.Integer(description='move management 4 authority', required=True, example=1),
    'sell_management_flag':fields.Integer(description='sell management authority', required=True, example=1),
    'sell_management_1_flag':fields.Integer(description='sell management 1 authority', required=True, example=1),
    'sell_management_2_flag':fields.Integer(description='sell management 2 authority', required=True, example=1),
    'remain_management_flag':fields.Integer(description='remain management authority', required=True, example=1),
    'remain_management_1_flag':fields.Integer(description='remain management 1 authority', required=True, example=1),
    'remain_management_2_flag':fields.Integer(description='remain management 2 authority', required=True, example=1),
    'remain_management_3_flag':fields.Integer(description='remain management 3 authority', required=True, example=1),
    'remain_management_4_flag':fields.Integer(description='remain management 4 authority', required=True, example=1),
    'remain_management_5_flag':fields.Integer(description='remain management 5 authority', required=True, example=1),
    'remain_management_6_flag':fields.Integer(description='remain management 6 authority', required=True, example=1),
    'sale_management_flag':fields.Integer(description='sale management authority', required=True, example=1),
    'sale_management_1_flag':fields.Integer(description='sale management 1 authority', required=True, example=1),
    'sale_management_2_flag':fields.Integer(description='sale management 2 authority', required=True, example=1),
    'sale_management_3_flag':fields.Integer(description='sale management 3 authority', required=True, example=1),
    'system_management_flag':fields.Integer(description='system management authority', required=True, example=1),
    'system_management_1_flag':fields.Integer(description='system management 1 authority', required=True, example=1),
    'system_management_2_flag':fields.Integer(description='system management 2 authority', required=True, example=1),
    'system_management_3_flag':fields.Integer(description='system management 3 authority', required=True, example=1),
    'system_management_4_flag':fields.Integer(description='system management 4 authority', required=True, example=1),
    'system_management_5_flag':fields.Integer(description='system management 5 authority', required=True, example=1),
    'system_management_6_flag':fields.Integer(description='system management 6 authority', required=True, example=1),
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

token_response_fields = user_ns.model('token Response Body', {
    'result':fields.String(description='login result', required=True, example='SUCCESS'),
    'userId':fields.String(description='user id',required=True,example='admin'),
    'authority':fields.Nested(user_authority_fields)})

user_info_response_fields = user_ns.model('user information Response Body', {
    'result':fields.String(description='login result', required=True, example='SUCCESS'),
    'name':fields.String(description='user name',required=True,example='name'),
    'department':fields.String(description='user department',required=True,example='department'),
    'phoneNumber':fields.String(description='user phone number',required=True,example='010-1111-1111'),
    'email':fields.String(description='user email',required=True,example='email'),
    'office':fields.String(description='user office name',required=True,example='office'),
    'registerDate':fields.String(description='user register date',required=True,example='2022-11-01 00:00:00')})

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

@user_ns.route('/token')
class token(Resource):

    @user_ns.response(200, 'OK', token_response_fields)
    @user_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get user information by token request
        '''
        id = get_jwt_identity()
        res = requests.get(f"http://{management_url}/{id}", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@user_ns.route('/information')
class information(Resource):

    @user_ns.response(200, 'OK', user_info_response_fields)
    @user_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get user detail information by token request
        '''
        id = get_jwt_identity()
        res = requests.get(f"http://{management_url}/information/{id}", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code