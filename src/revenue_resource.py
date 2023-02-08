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

revenue_ns = Namespace('Revenue', version="1.0", title='Revenue API List', description='Revenue API List')

revenue_list_query_parser = reqparse.RequestParser()
revenue_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
revenue_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
revenue_list_query_parser.add_argument('category', type=int, required=True, help='category : 0: daily, 1: monthly, 2: year')
revenue_list_query_parser.add_argument('startDate', type=str, help='search start date')
revenue_list_query_parser.add_argument('endDate', type=str, help='search end date')
revenue_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')

revenue_goods_list_query_parser = reqparse.RequestParser()
revenue_goods_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
revenue_goods_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
revenue_goods_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: sale date')
revenue_goods_list_query_parser.add_argument('startDate', type=str, help='search start date')
revenue_goods_list_query_parser.add_argument('endDate', type=str, help='search end date')
revenue_goods_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
revenue_goods_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
revenue_goods_list_query_parser.add_argument('sexList', type=int, help='search sex | 0:unisex, 1:male, 2:female', action='append')
revenue_goods_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
revenue_goods_list_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
revenue_goods_list_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
revenue_goods_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
revenue_goods_list_query_parser.add_argument('sellerTypeList', type=int, help='seller type list', action='append')
revenue_goods_list_query_parser.add_argument('sellerTagList', type=int, help='seller tag list', action='append')
revenue_goods_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
revenue_goods_list_query_parser.add_argument('searchContent', type=str, help='search content')

revenue_statistics_list_query_parser = reqparse.RequestParser()
revenue_statistics_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
revenue_statistics_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
revenue_statistics_list_query_parser.add_argument('category', type=int, required=True, help='category : 0: daily, 1: monthly, 2: year')
revenue_statistics_list_query_parser.add_argument('startDate', type=str, help='search start date')
revenue_statistics_list_query_parser.add_argument('endDate', type=str, help='search end date')
revenue_statistics_list_query_parser.add_argument('sellerTypeList', type=int, help='seller type list', action='append')

table_fields = revenue_ns.model('revenue table fields', {
    'column':fields.List(fields.String(description='column name',required=True,example='tag')),
    'rows':fields.List(fields.List(fields.String(description='row data',required=True,example='data')))
})

revenue_list_response_fields = revenue_ns.model('revenue list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'table':fields.Nested(table_fields),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalResult':fields.Integer(description='totalResult',required=True,example=15),
    'totalSold':fields.Integer(description='totalSold',required=True,example=15),
    'totalFirstCost':fields.Integer(description='totalFirstCost',required=True,example=150000),
    'totalSaleCost':fields.Integer(description='totalSaleCost',required=True,example=150000),
    'totalCommissionCost':fields.Integer(description='totalCommissionCost',required=True,example=15000),
    'totalSettlementCost':fields.Integer(description='totalSettlementCost',required=True,example=135000),
    'totalSaleMarginRate':fields.Integer(description='totalSaleMarginRate',required=True,example=15),
    'totalFirstCostMarginRate':fields.Integer(description='totalFirstCostMarginRate',required=True,example=15)
})

revenue_goods_list_response_fields = revenue_ns.model('revenue goods list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'table':fields.Nested(table_fields),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalResult':fields.Integer(description='totalResult',required=True,example=15)
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['revenue_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@revenue_ns.route('')
class revenueApiList(Resource):

    @revenue_ns.expect(revenue_list_query_parser)
    @revenue_ns.response(200, 'OK', revenue_list_response_fields)
    @revenue_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get revenue list 
        '''
        args = revenue_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code


@revenue_ns.route('/goods')
class revenueGoodsApiList(Resource):

    @revenue_ns.expect(revenue_goods_list_query_parser)
    @revenue_ns.response(200, 'OK', revenue_goods_list_response_fields)
    @revenue_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get revenue goods list 
        '''
        args = revenue_goods_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/goods", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@revenue_ns.route('/statistics')
class revenueStatisticsApiList(Resource):

    @revenue_ns.expect(revenue_statistics_list_query_parser)
    @revenue_ns.response(200, 'OK', revenue_list_response_fields)
    @revenue_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get revenue statistics list 
        '''
        args = revenue_statistics_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/statistics", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    