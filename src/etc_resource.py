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

office_list_fields = etc_ns.model('office drop box fields', {
    'officeTag':fields.Integer(description='office tag',required=True,example=1),
    'officeName':fields.String(description='office name',required=True,example='name')
})

office_list_response_fields = etc_ns.model('office drop box response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(office_list_fields))
})

brand_list_fields = etc_ns.model('brand drop box fields', {
    'index':fields.Integer(description='index',required=True,example=1),
    'brandTag':fields.String(description='brand tag',required=True,example='AP'),
    'brandName':fields.String(description='brand name',required=True,example='A.P.C.')
})

brand_list_response_fields = etc_ns.model('brand drop box response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(brand_list_fields))
})

category_list_fields = etc_ns.model('category drop box fields', {
    'index':fields.Integer(description='index',required=True,example=1),
    'categoryTag':fields.String(description='category tag',required=True,example='BAG'),
    'categoryName':fields.String(description='category name',required=True,example='bag')
})

category_list_response_fields = etc_ns.model('category drop box response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(category_list_fields))
})

origin_list_fields = etc_ns.model('origin drop box fields', {
    'index':fields.Integer(description='index',required=True,example=1),
    'origin':fields.String(description='origin name',required=True,example='ITALY')
})

origin_list_response_fields = etc_ns.model('origin drop box response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(origin_list_fields))
})

supplier_list_fields = etc_ns.model('supplier drop box fields', {
    'supplierTag':fields.Integer(description='supplier tag',required=True,example=1),
    'supplierName':fields.String(description='supplier name',required=True,example='name')
})

supplier_list_response_fields = etc_ns.model('supplier drop box response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(supplier_list_fields))
})

season_list_fields = etc_ns.model('season drop box fields', {
    'index':fields.Integer(description='index',required=True,example=1),
    'season':fields.String(description='season name',required=True,example='2022 F/W')
})

season_list_response_fields = etc_ns.model('season drop box response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(season_list_fields))
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
    @etc_ns.response(200, 'OK', office_list_response_fields)
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
    @etc_ns.response(200, 'OK', brand_list_response_fields)
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
    @etc_ns.response(200, 'OK', category_list_response_fields)
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
    @etc_ns.response(200, 'OK', origin_list_response_fields)
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
    @etc_ns.response(200, 'OK', supplier_list_response_fields)
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
    @etc_ns.response(200, 'OK', season_list_response_fields)
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