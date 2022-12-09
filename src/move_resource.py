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

move_ns = Namespace('Move', version="1.0", title='Move API List', description='Move API List')

move_list_query_parser = reqparse.RequestParser()
move_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
move_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
move_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date')
move_list_query_parser.add_argument('startDate', type=str, help='search start date')
move_list_query_parser.add_argument('endDate', type=str, help='search end date')
move_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
move_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
move_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
move_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
move_list_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
move_list_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
move_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
move_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
move_list_query_parser.add_argument('searchContent', type=str, help='search content')

move_approve_list_query_parser = reqparse.RequestParser()
move_approve_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
move_approve_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
move_approve_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
move_approve_list_query_parser.add_argument('startDate', type=str, help='search start date')
move_approve_list_query_parser.add_argument('endDate', type=str, help='search end date')
move_approve_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
move_approve_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
move_approve_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
move_approve_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
move_approve_list_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
move_approve_list_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
move_approve_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
move_approve_list_query_parser.add_argument('searchContent', type=str, help='search content')
move_approve_list_query_parser.add_argument('fromOfficeTagList', type=int, help='from office tag list', action='append')
move_approve_list_query_parser.add_argument('toOfficeTagList', type=int, help='to office tag list', action='append')
move_approve_list_query_parser.add_argument('moveUserName', type=str, help='user name who moved goods')
move_approve_list_query_parser.add_argument('approveUserName', type=str, help='user name who approve movement of goods')

office_move_list_query_parser = reqparse.RequestParser()
office_move_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
office_move_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
office_move_list_query_parser.add_argument('startDate', type=str, help='search start date')
office_move_list_query_parser.add_argument('endDate', type=str, help='search end date')
office_move_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
office_move_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
office_move_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
office_move_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
office_move_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
office_move_list_query_parser.add_argument('searchContent', type=str, help='search content')
office_move_list_query_parser.add_argument('fromOfficeTagList', type=int, help='from office tag list', action='append')
office_move_list_query_parser.add_argument('toOfficeTagList', type=int, help='to office tag list', action='append')
office_move_list_query_parser.add_argument('approve', type=int, help='approve flag | 0: no, 1: yes')

part_number_move_list_query_parser = reqparse.RequestParser()
part_number_move_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
part_number_move_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
part_number_move_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
part_number_move_list_query_parser.add_argument('startDate', type=str, help='search start date')
part_number_move_list_query_parser.add_argument('endDate', type=str, help='search end date')
part_number_move_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
part_number_move_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
part_number_move_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
part_number_move_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
part_number_move_list_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
part_number_move_list_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
part_number_move_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
part_number_move_list_query_parser.add_argument('searchContent', type=str, help='search content')
part_number_move_list_query_parser.add_argument('fromOfficeTagList', type=int, help='from office tag list', action='append')
part_number_move_list_query_parser.add_argument('toOfficeTagList', type=int, help='to office tag list', action='append')
part_number_move_list_query_parser.add_argument('approve', type=int, help='approve flag | 0: no, 1: yes')

office_move_detail_query_parser = reqparse.RequestParser()
office_move_detail_query_parser.add_argument('exportDate', type=str, required=True, help='export date')
office_move_detail_query_parser.add_argument('fromOfficeTag', type=int, required=True, help='from office tag')
office_move_detail_query_parser.add_argument('toOfficeTag', type=int, required=True, help='to office tag')

part_number_move_detail_query_parser = reqparse.RequestParser()
part_number_move_detail_query_parser.add_argument('stockingDate', type=str, required=True, help='stocking date')
part_number_move_detail_query_parser.add_argument('partNumber', type=str, required=True, help='part number')

move_list_fields = move_ns.model('move list fields', {
    'tag':fields.String(description='goods tag',required=True,example='113AB1611120BC149'),
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-02'),
    'importDate':fields.String(description='import date',required=True,example='2022-11-01'),
    'supplierType':fields.String(description='supplier type',required=True,example='type'),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier name'),
    'blNumber':fields.String(description='BL number',required=True,example='-'),
    'season':fields.String(description='season',required=True,example='2022F/W'),
    'imageUrl':fields.String(description='image url',required=True,example='url'),
    'brand':fields.String(description='brand name',required=True,example='A.p.c.'),
    'category':fields.String(description='category name',required=True,example='Bag'),
    'partNumber':fields.String(description='part number',required=True,example='EXAMPLE-001M'),
    'sex':fields.String(description='sex',required=True,example='male'),
    'color':fields.String(description='color',required=True,example='BLACK'),
    'material':fields.String(description='material',required=True,example='100% COTTON'),
    'size':fields.String(description='size',required=True,example='M'),
    'origin':fields.String(description='origin',required=True,example='ITALY'),
    'office':fields.String(description='office name',required=True,example='office'),
    'status':fields.String(description='goods status',required=True,example='status'),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000)
})

move_list_response_fields = move_ns.model('move list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(move_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalMove':fields.Integer(description='total move',required=True,example=15)
})

move_request_fields = move_ns.model('move request fields', {
    'requestType':fields.Integer(description='register type | 1: excel, 2: batch, 3: handwork',required=True,example=1),
    'fromOfficeTag':fields.Integer(description='start officee tag',required=True,example=1),
    'toOfficeTag':fields.Integer(descripiton='to office tag',required=True,example=2),
    'goodsTagList':fields.List(fields.String(description='goodsTag',required=True,example='goods Tag')),
    'exportDate':fields.String(description='export date',required=True,example='2022-12-01'),
    'description':fields.String(description='memo',required=True,example='memo'),
    'approverName':fields.String(description='approver name',required=True,example='approver'),
    'moverName':fields.String(description='move user name',required=True,eaxmple='admin')
})

move_request_response_fields = move_ns.model('move request response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'tags':fields.List(fields.String(description='goods fields',required=True,example='tag'))
})

move_wait_approve_list_fields = move_ns.model('waiting move approve list fields', {
    'exportDate':fields.String(description='export date',required=True,example='2022-12-01'),
    'fromOffice':fields.String(description='from office name',required=True,example='from office'),
    'toOffice':fields.String(description='to office name',required=True,example='to office'),
    'tag':fields.String(description='goods tag',required=True,example='113AB1611120BC149'),
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-02'),
    'importDate':fields.String(description='import date',required=True,example='2022-11-01'),
    'supplierType':fields.String(description='supplier type',required=True,example='type'),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier name'),
    'blNumber':fields.String(description='BL number',required=True,example='-'),
    'season':fields.String(description='season',required=True,example='2022F/W'),
    'imageUrl':fields.String(description='image url',required=True,example='url'),
    'brand':fields.String(description='brand name',required=True,example='A.p.c.'),
    'category':fields.String(description='category name',required=True,example='Bag'),
    'partNumber':fields.String(description='part number',required=True,example='EXAMPLE-001M'),
    'sex':fields.String(description='sex',required=True,example='male'),
    'color':fields.String(description='color',required=True,example='BLACK'),
    'material':fields.String(description='material',required=True,example='100% COTTON'),
    'size':fields.String(description='size',required=True,example='M'),
    'origin':fields.String(description='origin',required=True,example='ITALY'),
    'status':fields.String(description='goods status',required=True,example='status'),
    'registerType':fields.String(description='register type',required=True,example='excel'),
    'moverName':fields.String(description='mover name',required=True,example='mover'),
    'approverName':fields.String(description='approver name',required=True,example='approver'),
    'description':fields.String(description='memo',required=True,example='memo'),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000)
})

move_status_list_fields = move_ns.model('move status list fields', {
    'exportDate':fields.String(description='export date',required=True,example='2022-12-01'),
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-01'),
    'importDate':fields.String(description='import date',required=True,example='2022-11-01'),
    'imageUrl':fields.String(description='image url',required=True,example='url'),
    'season':fields.String(description='season',required=True,example='22F/W'),
    'partNumber':fields.String(description='part number',required=True,example='part number'),
    'goodsTag':fields.String(description='goods tag',required=True,example='tag'),
    'brand':fields.String(description='brand',required=True,example='A.P.C.'),
    'category':fields.String(description='category',required=True,example='Bag'),
    'sex':fields.String(description='sex',required=True,example='sex'),
    'color':fields.String(description='color',required=True,example='black'),
    'material':fields.String(description='material',required=True,example='material'),
    'size':fields.String(description='size',required=True,example='XL'),
    'origin':fields.String(description='origin',required=True,example='ITALY'),
    'supplierType':fields.String(description='supplier type',required=True,example='supplier type'),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier name'),
    'fromOffice':fields.String(description='from office',required=True,example='office1'),
    'toOffice':fields.String(description='to office',required=True,example='office2'),
    'status':fields.String(description='origin',required=True,example='status'),
    'cost':fields.Integer(description='cost',required=True,example=100000),
    'firstCost':fields.Integer(description='first cost',required=True,example=100000),
    'regularcost':fields.Integer(description='regular cost',required=True,example=100000),
    'departmentStoreCost':fields.Integer(description='department store cost',required=True,example=100000),
    'eventCost':fields.Integer(description='event cost',required=True,example=100000),
    'outletCost':fields.Integer(description='outlet cost',required=True,example=100000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=100000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=100000),
    'description':fields.String(description='memo',required=True,example='memo'),
    'moveRequestUser':fields.String(description='move request user',required=True,example='user1'),
    'approve':fields.String(description='approve',required=True,example='YES'),
    'approveUser':fields.String(description='approve user',required=True,example='user2'),
    'registerDate':fields.String(description='register date',required=True,example='2022-11-01'),
})

move_wait_approve_list_response_fields = move_ns.model('wait move approve list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(move_wait_approve_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalWaiting':fields.Integer(description='total waiting count',required=True,example=15)
})

move_approve_fields = move_ns.model('move approve fields', {
    'approveType':fields.Integer(description='register type | 1: excel, 2: batch, 3: handwork',required=True,example=1),
    'goodsTagList':fields.List(fields.String(description='goodsTag',required=True,example='goods tag'))
})

move_approve_response_fields = move_ns.model('move approve response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'tags':fields.List(fields.String(description='goods fields',required=True,example='tag'))
})

office_move_list_fields = move_ns.model('office move list fields' ,{
    'exportDate':fields.String(description='export date',required=True,example='2022-12-01'),
    'fromOffice':fields.String(description='from office name',required=True,example='from office'),
    'fromOfficeTag':fields.Integer(description='from office tag',required=True,example=1),
    'toOffice':fields.String(descriptoon='to office name',required=True,example='to office'),
    'toOfficeTag':fields.Integer(description='to office tag',required=True,example=2),
    'moveCount':fields.Integer(description='move count',required=True,example=10),
    'approveCount':fields.Integer(description='approve count',required=True,example=7),
    'unApproveCount':fields.Integer(description='unapprove count',required=True,example=3)
})

office_move_list_response_fields = move_ns.model('office move list response fields', {
    'totalResult':fields.Integer(description='total result',required=True,example=120),
    'totalMove':fields.Integer(description='total move',required=True,example=3000),
    'totalApprove':fields.Integer(description='total approve',required=True,example=2000),
    'totalUnapprove':fields.Integer(description='total unapprove',required=True,example=1000),
    'totalPage':fields.Integer(description='total page',required=True,example=10),
    'list':fields.List(fields.Nested(office_move_list_fields))
})

office_move_detail_response_fields = move_ns.model('office move detail response fields', {
    'exportDate':fields.String(description='export date',required=True,example='2022-12-01'),
    'fromOffice':fields.String(description='from office name',required=True,example='from office'),
    'toOffice':fields.String(description='to office name',required=True,example='to office'),
    'totalMove':fields.Integer(description='total move',required=True,example=3000),
    'totalApprove':fields.Integer(description='total approve',required=True,example=2000),
    'totalUnapprove':fields.Integer(description='total unapprove',required=True,example=1000),
    'list':fields.List(fields.Nested(move_status_list_fields))
})

part_number_move_list_fields = move_ns.model('part number move list fields' ,{
    'supplierType':fields.String(description='supplier type',required=True,example='supplier type'),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier name'),
    'brand':fields.String(description='brand',required=True,example='A.P.C'),
    'category':fields.String(description='category',required=True,example='bag'),
    'imageUrl':fields.String(description='image url',required=True,example='url'),
    'partNumber':fields.String(description='part number',required=True,example='part number'),
    'importDate':fields.String(description='import date',required=True,example='2022-12-01'),
    'color':fields.String(description='color',required=True,example='black'),
    'material':fields.String(description='material',required=True,example='material'),
    'origin':fields.String(description='origin',required=True,example='Italy'),
    'moveCount':fields.Integer(description='move count',required=True,example=3),
    'fromOffice':fields.String(description='from office and count',required=True,example='office\t/ 1\noffice2\t/ 2'),
    'approveCount':fields.Integer(description='approve count',required=True,example=2),
    'toOfficeApprove':fields.String(description='to office and count',required=True,example='office3\t/ 2'),
    'unApproveCount':fields.Integer(description='unapprove count',required=True,example=1),
    'toOfficeUnapprove':fields.String(description='to office and count',required=True,example='office4\t/ 1'),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'firstCost':fields.Integer(description='first cost',required=True,example=700000),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'departmentStoreCost':fields.Integer(description='department store cost',required=True,example=800000),
    'eventCost':fields.Integer(description='event cost',required=True,example=0),
    'outletCost':fields.Integer(description='outlet cost',required=True,example=800000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000)
})

part_number_move_list_response_fields = move_ns.model('part number move list response fields', {
    'totalResult':fields.Integer(description='total result',required=True,example=120),
    'totalPage':fields.Integer(description='total page',required=True,example=10),
    'totalMove':fields.Integer(description='total move',required=True,example=3000),
    'totalApprove':fields.Integer(description='total approve',required=True,example=2000),
    'totalUnapprove':fields.Integer(description='total unapprove',required=True,example=1000),
    'totalCost':fields.Integer(description='cost',required=True,example=0),
    'totalFirstCost':fields.Integer(description='first cost',required=True,example=700000),
    'totalRegularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'totalDepartmentStoreCost':fields.Integer(description='department store cost',required=True,example=800000),
    'totalEventCost':fields.Integer(description='event cost',required=True,example=0),
    'totalOutletCost':fields.Integer(description='outlet cost',required=True,example=800000),
    'totalSaleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'totalDiscountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'totalManagementCost':fields.Integer(description='management cost',required=True,example=50000),
    'list':fields.List(fields.Nested(part_number_move_list_fields))
})

part_number_move_detail_response_fields = move_ns.model('part number move detail response fields', {
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-12-01'),
    'partNumber':fields.String(description='part number',required=True,example='partnumber'),
    'totalMove':fields.Integer(description='total move',required=True,example=3000),
    'totalApprove':fields.Integer(description='total approve',required=True,example=2000),
    'totalUnapprove':fields.Integer(description='total unapprove',required=True,example=1000),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier name'),
    'brand':fields.String(description='brand name',required=True,example='A.p.c.'),
    'category':fields.String(description='category name',required=True,example='Bag'),
    'list':fields.List(fields.Nested(move_status_list_fields))
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['move_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@move_ns.route('')
class moveApiList(Resource):

    @move_ns.expect(move_list_query_parser)
    @move_ns.response(200, 'OK', move_list_response_fields)
    @move_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get move list 
        '''
        args = move_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @move_ns.expect(move_request_fields)
    @move_ns.response(201, 'OK', move_request_response_fields)
    @move_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self,goodsTag):
        '''
        request move goods
        '''
        id = get_jwt_identity()
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        request_body['userId'] = id
        res = requests.post(f"http://{management_url}/{goodsTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@move_ns.route('/approve')
class approveApiList(Resource):

    @move_ns.expect(move_approve_list_query_parser)
    @move_ns.response(200, 'OK', move_wait_approve_list_response_fields)
    @move_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get waiting move approve list 
        '''
        args = move_approve_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/approve", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @move_ns.expect(move_approve_fields)
    @move_ns.response(201, 'OK', move_approve_response_fields)
    @move_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self,goodsTag):
        '''
        approve move goods
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/approve/{goodsTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@move_ns.route('/status/office')
class statusOfficeApiList(Resource):

    @move_ns.expect(office_move_list_query_parser)
    @move_ns.response(200, 'OK', office_move_list_response_fields)
    @move_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get status movement of office
        '''
        args = office_move_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/status/office", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@move_ns.route('/status/office/detail')
class statusOfficeDetailApiList(Resource):

    @move_ns.expect(office_move_detail_query_parser)
    @move_ns.response(200, 'OK', office_move_detail_response_fields)
    @move_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get status movement detail of office
        '''
        args = office_move_detail_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/status/office/detail", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@move_ns.route('/status/partNumber')
class statusPartNumberApiList(Resource):

    @move_ns.expect(part_number_move_list_query_parser)
    @move_ns.response(200, 'OK', part_number_move_list_response_fields)
    @move_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get status movement of part number
        '''
        args = part_number_move_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/status/partNumber", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@move_ns.route('/status/partNumber/detail')
class statusPartNumberDetailApiList(Resource):

    @move_ns.expect(part_number_move_detail_query_parser)
    @move_ns.response(200, 'OK', part_number_move_detail_response_fields)
    @move_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get status movement detail of part number
        '''
        args = part_number_move_detail_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/status/partNumber/detail", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code