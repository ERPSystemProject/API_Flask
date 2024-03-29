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

import pymysql

system_ns = Namespace('System', version="1.0", title='System API List', description='System API List')

brand_query_parser = reqparse.RequestParser()
brand_query_parser.add_argument('sort', type=int, default=0, help='sort type | 0:tag, 1:name')
brand_query_parser.add_argument('useFlag', type=int, default=0, help='use flag | 0:all, 1:use, 2:not use')
brand_query_parser.add_argument('name', type=str, help='brand name')
brand_query_parser.add_argument('tag', type=str, help='tag name')

category_query_parser = reqparse.RequestParser()
category_query_parser.add_argument('sort', type=int, default=0, help='sort type | 0:tag, 1:name')
category_query_parser.add_argument('useFlag', type=int, default=0, help='use flag | 0:all, 1:use, 2:not use')
category_query_parser.add_argument('name', type=str, help='category name')
category_query_parser.add_argument('tag', type=str, help='tag name')

origin_query_parser = reqparse.RequestParser()
origin_query_parser.add_argument('useFlag', type=int, default=0, help='use flag | 0:all, 1:use, 2:not use')
origin_query_parser.add_argument('name', type=str, help='origin name')

supplier_query_parser = reqparse.RequestParser()
supplier_query_parser.add_argument('sort', type=int, default=0, help='sort type | 0:tag, 1:name')
supplier_query_parser.add_argument('type', type=int, default=0, help='supplier type | 0:all, 1:consignment, 2:buying, 3:direct import, 4:not in stock')
supplier_query_parser.add_argument('useFlag', type=int, default=0, help='use flag | 0:all, 1:use, 2:not use')
supplier_query_parser.add_argument('name', type=str, help='supplier name')
supplier_query_parser.add_argument('tag', type=str, help='tag name')

office_query_parser = reqparse.RequestParser()
office_query_parser.add_argument('type', type=int, default=0, help='office type | 0:all, 1:wholesale, 2:consignment, 3:direct management, 4:event, 5:retail sale, 6:online, 7:home shopping')
office_query_parser.add_argument('useFlag', type=int, default=0, help='use flag | 0:all, 1:use, 2:not use')
office_query_parser.add_argument('officeName', type=str, help='office name')
office_query_parser.add_argument('registrationName', type=str, help='registration name')
office_query_parser.add_argument('phoneNumber', type=str, help='phone number')

seller_query_parser = reqparse.RequestParser()
seller_query_parser.add_argument('type', type=int, default=0, help='seller type | 0:all, 1:wholesale, 2:retail sale, 3:online, 4:home shopping, 5:etc')
seller_query_parser.add_argument('useFlag', type=int, default=0, help='use flag | 0:all, 1:use, 2:not use')
seller_query_parser.add_argument('sellerName', type=str, help='seller name')
seller_query_parser.add_argument('registrationName', type=str, help='registration name')
seller_query_parser.add_argument('phoneNumber', type=str, help='phone number')

result_fields = system_ns.model('system request result', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'tag':fields.String(description='tag',required=True,example='1')
})

brand_fields = system_ns.model('brand system fields', {
    'tag':fields.String(description='brand tag', required=True, example='AP'),
    'name':fields.String(description='brand name', required=True, example='A.p.c.'),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

brand_response_fields = system_ns.model('brand system list response', {
    'result':fields.String(description='result', required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(brand_fields))
})

category_fields = system_ns.model('category system fields', {
    'tag':fields.String(description='category tag', required=True, example='AC'),
    'name':fields.String(description='category name', required=True, example='Acc'),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

category_response_fields = system_ns.model('category system list response', {
    'result':fields.String(description='result', required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(category_fields))
})

origin_fields = system_ns.model('origin system fields', {
    'name':fields.String(description='origin name', required=True, example='ARMENIA'),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

origin_response_fields = system_ns.model('origin system list response', {
    'result':fields.String(description='result', required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(origin_fields))
})

supplier_fields = system_ns.model('supplier system fields', {
    'tag':fields.Integer(description='supplier tag', required=True, example=1),
    'name':fields.String(description='supplier name', required=True, example='supplier'),
    'type':fields.Integer(description='supplier type', required=True, example=1),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

supplier_response_fields = system_ns.model('supplier system list response', {
    'result':fields.String(description='result', required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(supplier_fields))
})

supplier_request_fields = system_ns.model('supplier system register fields', {
    'name':fields.String(description='supplier name', required=True, example='supplier'),
    'type':fields.Integer(description='supplier type', required=True, example=1),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

office_fields = system_ns.model('office system fields', {
    'tag':fields.Integer(description='office tag', required=True, example=1),
    'name':fields.String(description='office name', required=True, example='office'),
    'sellingType':fields.List(fields.Integer(description='selling type | 1:wholesale, 2:consignment, 3:direct management, 4:event, 5:retail sale, 6:online, 7:home shopping', required=True, example=1)),
    'costType':fields.List(fields.Integer(description='cost type | 1:euro, 2:sale cost, 3: discount cost, 4: event cost, 5: department store cost, 6: outlet cost, 7: regular cost, 8: first cost', required=True, example=1)),
    'registrationName':fields.String(description='registration name', required=True, example='registration name'),
    'registrationNumber':fields.String(description='registration number',required=True,example='111-11-11111'),
    'representative':fields.String(description='representative', required=True,example='representative'),
    'phoneNumber':fields.String(description='phone number', required=True, example='010-1111-1111'),
    'faxNumber':fields.String(description='FAX number', required=True, example='02-1111-1111'),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'address':fields.String(description='address', required=True, example='address'),
    'businessStatus':fields.String(description='business status', required=True, example='status'),
    'businessItem':fields.String(description='business item', required=True, example='item'),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

office_response_fields = system_ns.model('office system list response', {
    'result':fields.String(description='result', required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(office_fields))
})

office_request_fields = system_ns.model('office system register fields', {
    'name':fields.String(description='office name', required=True, example='office'),
    'registrationName':fields.String(description='registration name', required=True, example='registration name'),
    'registrationNumber':fields.String(description='registration number',required=True,example='111-11-11111'),
    'sellingType':fields.List(fields.Integer(description='selling type | 1:wholesale, 2:consignment, 3:direct management, 4:event, 5:retail sale, 6:online, 7:home shopping', required=True, example=1)),
    'costType':fields.List(fields.Integer(description='cost type | 1:euro, 2:sale cost, 3: discount cost, 4: event cost, 5: department store cost, 6: outlet cost, 7: regular cost, 8: first cost', required=True, example=1)),
    'representative':fields.String(description='representative', required=True,example='representative'),
    'phoneNumber':fields.String(description='phone number', required=True, example='010-1111-1111'),
    'faxNumber':fields.String(description='FAX number', required=True, example='02-1111-1111'),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'address':fields.String(description='address', required=True, example='address'),
    'businessStatus':fields.String(description='business status', required=True, example='status'),
    'businessItem':fields.String(description='business item', required=True, example='item'),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

seller_fields = system_ns.model('seller system fields', {
    'tag':fields.Integer(description='seller tag', required=True, example=1),
    'name':fields.String(description='seller name', required=True, example='Acc'),
    'sellingType':fields.List(fields.Integer(description='selling type | 1:wholesale, 2:retail sale, 3:online, 4:home shopping, 5:ETC', required=True, example=1)),
    'registrationName':fields.String(description='registration name', required=True, example='registrationName'),
    'registrationNumber':fields.String(description='registration number',required=True,example='111-11-11111'),
    'representative':fields.String(description='representative', required=True,example='representative'),
    'phoneNumber':fields.String(description='phone number', required=True, example='010-1111-1111'),
    'faxNumber':fields.String(description='FAX number', required=True, example='02-1111-1111'),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'address':fields.String(description='address', required=True, example='address'),
    'businessStatus':fields.String(description='business status', required=True, example='status'),
    'businessItem':fields.String(description='business item', required=True, example='item'),
    'couponDiscount':fields.Float(description='coupon Discount rate', required=True, example=0),
    'cardDiscount':fields.Float(description='card Discount rate', required=True, example=0),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

seller_response_fields = system_ns.model('seller system list response', {
    'result':fields.String(description='result', required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(seller_fields))
})

seller_request_fields = system_ns.model('seller system request fields', {
    'name':fields.String(description='seller name', required=True, example='Acc'),
    'sellingType':fields.List(fields.Integer(description='selling type | 1:wholesale, 2:retail sale, 3:online, 4:home shopping, 5:ETC', required=True, example=1)),
    'registrationName':fields.String(description='registration name', required=True, example='registrationName'),
    'registrationNumber':fields.String(description='registration number',required=True,example='111-11-11111'),
    'representative':fields.String(description='representative', required=True,example='representative'),
    'phoneNumber':fields.String(description='phone number', required=True, example='010-1111-1111'),
    'faxNumber':fields.String(description='FAX number', required=True, example='02-1111-1111'),
    'useFlag':fields.Integer(description='use flag', required=True, example=1),
    'description':fields.String(description='memo', required=True, example='memo'),
    'address':fields.String(description='address', required=True, example='address'),
    'businessStatus':fields.String(description='business status', required=True, example='status'),
    'businessItem':fields.String(description='business item', required=True, example='item'),
    'userId':fields.String(description='register ID', required=True, example='admin')
})

seller_cost_fields = system_ns.model('seller cost fields', {
    'registerDate':fields.String(description='register date', required=True, example='2022-11-01 00:00:00'),
    'couponDiscount':fields.Float(description='coupon discount rate', required=True, example=0.00),
    'cardDiscount':fields.Float(description='card discount rate', required=True, example=0.00),
    'advertisementCost':fields.Integer(description='marketing cost',required=True, example=10000000),
    'partnerLevy':fields.Integer(description='partner levy',required=True,example=1000000),
    'productMaintenanceCost':fields.Integer(description='product maintenance cost',required=True,example=2000000),
    'penaltyCost':fields.Integer(description='penalty cost',required=True,example=200000),
    'deliveryCost':fields.Integer(description='delivery cost',required=True,example=5000)
})

seller_register_cost_fields = system_ns.model('seller cost register fields', {
    'userId':fields.String(description='register ID', required=True, example='admin'),
    'couponDiscount':fields.Float(description='coupon discount rate', required=True, example=0.00),
    'cardDiscount':fields.Float(description='card discount rate', required=True, example=0.00),
    'advertisementCost':fields.Integer(description='marketing cost',required=True, example=10000000),
    'partnerLevy':fields.Integer(description='partner levy',required=True,example=1000000),
    'productMaintenanceCost':fields.Integer(description='product maintenance cost',required=True,example=2000000),
    'penaltyCost':fields.Integer(description='penalty cost',required=True,example=200000),
    'deliveryCost':fields.Integer(description='delivery cost',required=True,example=5000)
})

seller_cost_response_fields = system_ns.model('seller cost response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(seller_cost_fields))
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['system_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])
db_config = None

# DB 접속
def connect_mysql():
    status_code = status.HTTP_200_OK
    try:
        mysql_conn = pymysql.connect(user=db_config['user'], password=db_config['password'],
                                 host=db_config['host'], port=db_config['port'], database=db_config['database'],
                                 charset='utf8', autocommit=True)
        mysql_cursor = mysql_conn.cursor()

        return mysql_cursor, status_code
    except Exception as e:
        result = dict()
        result['message'] = 'DB Connection Error.'
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return result, status_code

#config 파일 읽어오기
def load_config():
    global db_config
    status_code = status.HTTP_200_OK
    try:
        f = open(config_path)
        config = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
        db_config = config['DB']['mysql']
        return config, status_code
    except Exception as e:
        result = dict()
        result['message'] = 'Config Load Error.'
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return result, status_code

@system_ns.route('/brand')
class brandApiList(Resource):

    @system_ns.expect(brand_query_parser)
    @system_ns.response(200, 'OK', brand_response_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get brand list
        '''
        args = brand_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/brand", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.expect(brand_fields)
    @system_ns.response(201, 'OK', result_fields)
    @system_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self):
        '''
        post brand
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/brand", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/brand/<string:brandTag>')
class brandDetailApiList(Resource):
    @system_ns.expect(brand_fields)
    @system_ns.response(200, 'OK', result_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,brandTag):
        '''
        adjust brand
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/brand/{brandTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.doc(responses={204:'OK'})
    @jwt_required()
    def delete(self,brandTag):
        '''
        delete brand
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        res = requests.delete(f"http://{management_url}/brand/{brandTag}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/category')
class categoryApiList(Resource):

    @system_ns.expect(category_query_parser)
    @system_ns.response(200, 'OK', category_response_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get category list
        '''
        args = category_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/category", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.expect(category_fields)
    @system_ns.response(201, 'OK', result_fields)
    @system_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self):
        '''
        post category
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/category", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/category/<string:categoryTag>')
class categoryDetailApiList(Resource):

    @system_ns.expect(category_fields)
    @system_ns.response(200, 'OK', result_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,categoryTag):
        '''
        adjust category
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/category/{categoryTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.doc(responses={204:'OK'})
    @jwt_required()
    def delete(self,categoryTag):
        '''
        delete category
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        res = requests.delete(f"http://{management_url}/category/{categoryTag}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/origin')
class originApiList(Resource):

    @system_ns.expect(origin_query_parser)
    @system_ns.response(200, 'OK', origin_response_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get origin list
        '''
        args = origin_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/origin", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.expect(origin_fields)
    @system_ns.response(201, 'OK', result_fields)
    @system_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self):
        '''
        post origin
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/origin", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/origin/<string:originName>')
class originDetailApiList(Resource):

    @system_ns.expect(origin_fields)
    @system_ns.response(200, 'OK', result_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,originName):
        '''
        adjust origin
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/origin/{originName}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.doc(responses={204:'OK'})
    @jwt_required()
    def delete(self,originName):
        '''
        delete origin
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        res = requests.delete(f"http://{management_url}/origin/{originName}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/supplier')
class supplierApiList(Resource):

    @system_ns.expect(supplier_query_parser)
    @system_ns.response(200, 'OK', supplier_response_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get supplier list
        '''
        args = supplier_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/supplier", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.expect(supplier_request_fields)
    @system_ns.response(201, 'OK', result_fields)
    @system_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self):
        '''
        post supplier
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/supplier", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/supplier/<int:supplierTag>')
class supplierDetailApiList(Resource):

    @system_ns.expect(supplier_fields)
    @system_ns.response(200, 'OK', result_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,supplierTag):
        '''
        adjust supplier
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/supplier/{supplierTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.doc(responses={204:'OK'})
    @jwt_required()
    def delete(self,supplierTag):
        '''
        delete supplier
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        res = requests.delete(f"http://{management_url}/supplier/{supplierTag}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/seller')
class sellerApiList(Resource):

    @system_ns.expect(seller_query_parser)
    @system_ns.response(200, 'OK', seller_response_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get seller list
        '''
        args = seller_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/seller", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code
    
    @system_ns.expect(seller_request_fields)
    @system_ns.response(201, 'OK', result_fields)
    @system_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self):
        '''
        post seller
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/seller", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/seller/<int:sellerTag>')
class sellerDetailApiList(Resource):

    @system_ns.expect(seller_request_fields)
    @system_ns.response(200, 'OK', result_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,sellerTag):
        '''
        adjust seller
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/seller/{sellerTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.doc(responses={204:'OK'})
    @jwt_required()
    def delete(self,sellerTag):
        '''
        delete seller
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        res = requests.delete(f"http://{management_url}/seller/{sellerTag}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/seller/<int:sellerTag>/cost')
class sellerDetailApiList(Resource):

    @system_ns.response(200, 'OK', seller_cost_response_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,sellerTag):
        '''
        get seller cost list
        '''
        res = requests.get(f"http://{management_url}/seller/{sellerTag}/cost", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.expect(seller_register_cost_fields)
    @system_ns.response(201, 'OK', result_fields)
    @system_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self,sellerTag):
        '''
        post seller cost
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/seller/{sellerTag}/cost", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/office')
class officeApiList(Resource):

    @system_ns.expect(office_query_parser)
    @system_ns.response(200, 'OK', office_response_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get office list
        '''
        args = office_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/office", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.expect(office_request_fields)
    @system_ns.response(201, 'OK', result_fields)
    @system_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self):
        '''
        post office
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/office", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@system_ns.route('/office/<int:officeTag>')
class officeDetailApiList(Resource):

    @system_ns.expect(office_request_fields)
    @system_ns.response(200, 'OK', result_fields)
    @system_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,officeTag):
        '''
        adjust office
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/office/{officeTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @system_ns.doc(responses={204:'OK'})
    @jwt_required()
    def delete(self,officeTag):
        '''
        delete office
        '''
        mysql_cursor, connect_code = connect_mysql()
        id = get_jwt_identity()
        query = f"SELECT authority_id FROM user where user_id = '{id}';"
        mysql_cursor.execute(query)
        a_id_row = mysql_cursor.fetchone()
        a_id = a_id_row[0]
        if a_id != 'admin':
            return 'Not Authirity Id', 400
        res = requests.delete(f"http://{management_url}/office/{officeTag}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code