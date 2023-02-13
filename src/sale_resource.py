# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys

import flask
from flask_restx import Api, Resource, Namespace, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
import werkzeug
import requests
import json
import yaml

sale_ns = Namespace('Sale', version="1.0", title='Sale API List', description='Sale API List')

goods_list_query_parser = reqparse.RequestParser()
goods_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
goods_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
goods_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
goods_list_query_parser.add_argument('startDate', type=str, help='search start date')
goods_list_query_parser.add_argument('endDate', type=str, help='search end date')
goods_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
goods_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
goods_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
goods_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
goods_list_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
goods_list_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
goods_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
goods_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
goods_list_query_parser.add_argument('searchContent', type=str, help='search content')

sale_list_query_parser = reqparse.RequestParser()
sale_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
sale_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
sale_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date, 3: sale date')
sale_list_query_parser.add_argument('startDate', type=str, help='search start date')
sale_list_query_parser.add_argument('endDate', type=str, help='search end date')
sale_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
sale_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
sale_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
sale_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
sale_list_query_parser.add_argument('sellerTypeList', type=int, help='seller type list | 1:wholesale, 2:retail sale, 3:online, 4:home shopping, 5:etc', action='append')
sale_list_query_parser.add_argument('sellerTagList', type=int, help='seller tag list', action='append')
sale_list_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
sale_list_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
sale_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
sale_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
sale_list_query_parser.add_argument('searchContent', type=str, help='search content')
sale_list_query_parser.add_argument('saleStartDate', type=str, help='sale start date')
sale_list_query_parser.add_argument('saleEndDate', type=str, help='sale end date')
sale_list_query_parser.add_argument('orderNumber', type=str, help='order number')
sale_list_query_parser.add_argument('invoiceNumber', type=str, help='invoice number')
sale_list_query_parser.add_argument('customer', type=str, help='customer')
sale_list_query_parser.add_argument('receiverName', type=str, help='receiver name')
sale_list_query_parser.add_argument('receiverPhoneNumber', type=str, help='receiver phone number')
sale_list_query_parser.add_argument('receiverAddress', type=str, help='receiver address')
sale_list_query_parser.add_argument('saleRegisterName', type=str, help='sale register name')

table_fields = sale_ns.model('sale table fields', {
    'column':fields.List(fields.String(description='column name',required=True,example='tag')),
    'rows':fields.List(fields.List(fields.String(description='row data',required=True,example='data')))
})

goods_list_response_fields = sale_ns.model('sale goods list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'table':fields.Nested(table_fields),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalMove':fields.Integer(description='total move',required=True,example=15)
})

sale_register_fields = sale_ns.model('sale register fields', {
    'registerType':fields.Integer(description='register type | 1: excel, 2: batch, 3: handwork',required=True,example=1),
    'saleDate':fields.String(descripiton='sale date',required=True,example='2022-11-01'),
    'cost':fields.Integer(description='sale cost',required=True,example=1000000),
    'commissionRate':fields.Float(description='commission rate',required=True,example=10.5),
    'sellerTag':fields.Integer(description='seller tag',required=True,example=1),
    'customerName':fields.String(description='customer name',required=True,eaxmple='customer name'),
    'orderNumber':fields.String(description='order number',required=True,example='order number'),
    'invoiceNumber':fields.String(description='invoice number',required=True,example='invoice number'),
    'receiverName':fields.String(description='receiver name',required=True,example='receiver name'),
    'receiverPhoneNumber':fields.String(description='receiver phone number',required=True,example='010-1111-1111'),
    'receiverAddress':fields.String(description='receiver address',required=True,example='address'),
    'description':fields.String(description='memo',required=True,example='memo')
})

sale_register_response_fields = sale_ns.model('sale register response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'tag':fields.String(description='goods tag',required=True,example='tag')
})

sale_list_response_fields = sale_ns.model('sale list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'totalResult':fields.Integer(description='total result',required=True,example=1000),
    'totalPage':fields.Integer(description='total page',required=True,example=10),
    'table':fields.Nested(table_fields)
})

sale_return_request_fields = sale_ns.model('sale return request fields',{
    'registerType':fields.Integer(description='register type | 1: excel, 2: batch, 3: handwork',required=True,example=1),
    'reason':fields.String(description='return reason',required=True,example='reason')
})

sale_return_response_fields = sale_ns.model('sale return response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'tag':fields.String(description='goods tag',required=True,example='goods tag')
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['sale_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@sale_ns.route('')
class saleApiList(Resource):

    @sale_ns.expect(goods_list_query_parser)
    @sale_ns.response(200, 'OK', goods_list_response_fields)
    @sale_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get goods list for sale
        '''
        args = goods_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@sale_ns.route('/<string:goodsTag>')
class saleRegisterApiList(Resource):

    @sale_ns.expect(sale_register_fields)
    @sale_ns.response(201, 'OK', sale_register_response_fields)
    @sale_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self,goodsTag):
        '''
        register goods sale
        '''
        id = get_jwt_identity()
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        request_body['userId'] = id
        res = requests.post(f"http://{management_url}/{goodsTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@sale_ns.route('/sold')
class soldApiList(Resource):

    @sale_ns.expect(sale_list_query_parser)
    @sale_ns.response(200, 'OK', sale_list_response_fields)
    @sale_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get sold goods list 
        '''
        args = sale_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/sold", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@sale_ns.route('/return/<string:goodsTag>')
class soldRetuenApiList(Resource):

    @sale_ns.expect(sale_return_request_fields)
    @sale_ns.response(201, 'OK', sale_return_response_fields)
    @sale_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,goodsTag):
        '''
        return goods
        '''
        id = get_jwt_identity()
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        request_body['userId'] = id
        res = requests.put(f"http://{management_url}/return/{goodsTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code
