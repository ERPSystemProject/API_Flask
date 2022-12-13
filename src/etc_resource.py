# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys

import flask
from flask_restx import Api, Resource, Namespace, fields, reqparse
from flask_jwt_extended import jwt_required
import werkzeug
import requests
import json
import yaml

etc_ns = Namespace('ETC', version="1.0", title='ETC API List', description='ETC API List')

keyword_query_parser = reqparse.RequestParser()
keyword_query_parser.add_argument('keyword', type=str, help='search keyword')

drop_box_list_fields = etc_ns.model('drop box fields', {
    'tag':fields.String(description='tag',required=True,example='tag'),
    'name':fields.String(description='name',required=True,example='name')
})

drop_box_list_response_fields = etc_ns.model('drop box response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'name':fields.String(description='name',required=True,example='name'),
    'items':fields.List(fields.Nested(drop_box_list_fields))
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['etc_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@etc_ns.route('/offices')
class officeDropBox(Resource):

    @etc_ns.expect(keyword_query_parser)
    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get office drop box list 
        '''
        args = keyword_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/offices", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@etc_ns.route('/brands')
class brandDropBox(Resource):

    @etc_ns.expect(keyword_query_parser)
    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get brand drop box list 
        '''
        args = keyword_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/brands", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@etc_ns.route('/categories')
class categoryDropBox(Resource):

    @etc_ns.expect(keyword_query_parser)
    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get category drop box list 
        '''
        args = keyword_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/categories", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@etc_ns.route('/origins')
class originDropBox(Resource):

    @etc_ns.expect(keyword_query_parser)
    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get origin drop box list 
        '''
        args = keyword_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/origins", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@etc_ns.route('/suppliers')
class supplierDropBox(Resource):

    @etc_ns.expect(keyword_query_parser)
    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get supplier drop box list 
        '''
        args = keyword_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/suppliers", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@etc_ns.route('/seasons')
class seasonDropBox(Resource):

    @etc_ns.expect(keyword_query_parser)
    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get season drop box list 
        '''
        args = keyword_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/seasons", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@etc_ns.route('/sex')
class sexDropBox(Resource):

    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get sex drop box list 
        '''
        res = requests.get(f"http://{management_url}/sex", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@etc_ns.route('/supplierTypes')
class supplierTypeDropBox(Resource):

    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get supplier type drop box list 
        '''
        res = requests.get(f"http://{management_url}/supplierTypes", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@etc_ns.route('/goodsStatus')
class goodsStatusDropBox(Resource):

    @etc_ns.response(200, 'OK', drop_box_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get goods status drop box list 
        '''
        res = requests.get(f"http://{management_url}/goodsStatus", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code