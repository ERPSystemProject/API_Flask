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

consignment_ns = Namespace('Consignment', version="1.0", title='Consignment API List', description='Consignment API List')

consignment_query_parser = reqparse.RequestParser()
consignment_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
consignment_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
consignment_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date, 3: return date')
consignment_query_parser.add_argument('startDate', type=str, help='search start date')
consignment_query_parser.add_argument('endDate', type=str, help='search end date')
consignment_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
consignment_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
consignment_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
consignment_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
consignment_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
consignment_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
consignment_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
consignment_query_parser.add_argument('statusList', type=int, help='goods status | 1:scretch, 2:unable sale, 3:discard, 4:normal, 5:lost, 6:waiting for calculate, 7:waiting for distribution, 8:retrieve success, 9:fixing, 10:waiting for return calculate, 11:sold, 12:waiting for move sign, 13:waiting for client return', action='append')
consignment_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
consignment_query_parser.add_argument('searchContent', type=str, help='search content')

consignment_calculate_query_parser = reqparse.RequestParser()
consignment_calculate_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
consignment_calculate_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
consignment_calculate_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
consignment_calculate_query_parser.add_argument('startDate', type=str, help='search start date')
consignment_calculate_query_parser.add_argument('endDate', type=str, help='search end date')
consignment_calculate_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
consignment_calculate_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
consignment_calculate_query_parser.add_argument('searchContent', type=str, help='search content')

consignment_calculate_detail_query_parser = reqparse.RequestParser()
consignment_calculate_detail_query_parser.add_argument('type', type=int, required=True, default=1, help='type | 1: stock detail, 2: sale detail, 3: return detail, 4: remain detail')
consignment_calculate_detail_query_parser.add_argument('startDate', type=str, help='search start date')
consignment_calculate_detail_query_parser.add_argument('endDate', type=str, help='search end date')

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('files', location='files', type=werkzeug.datastructures.FileStorage, help='file upload', action='append')
upload_parser.add_argument('type', location='args', type=int, help='type | 1: goods image, 2: import certificate images')

consignment_list_fields = consignment_ns.model('consignment list fields', {
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
    'saleDate':fields.String(description='sale date',required=True,example='2022-11-10'),
    'office':fields.String(description='office name',required=True,example='office'),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000),
    'returnUser':fields.String(description='return user',required=True,example='admin'),
    'returnDate':fields.String(description='return date',required=True,example='2022-11-30')
})

consignment_list_response_fields = consignment_ns.model('consignment response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(consignment_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalConsignment':fields.Integer(description='total consignment',required=True,example=15)
})

consignment_register_fields = consignment_ns.model('consignment register fields', {
    'registerType':fields.Integer(description='register type | 1: excel, 2: batch, 3: handwork',required=True,example=1),
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-02'),
    'importDate':fields.String(description='import date',required=True,example='2022-11-01'),
    'supplierTag':fields.Integer(description='supplier tag',required=True,example=1),
    'officeTag':fields.Integer(description='office tag',required=True,example=1),
    'partNumber':fields.String(description='part number',required=True,example='EXAMPLE-001M'),
    'brandTag':fields.String(description='brand Tag',required=True,example='AP'),
    'categoryTag':fields.String(description='category Tag',required=True,example='BAG'),
    'origin':fields.String(description='origin',required=True,example='ITALY'),
    'sex':fields.Integer(description='sec | 0:unisex, 1:male, 2:female',required=True,example=1),
    'color':fields.String(description='color',required=True,example='BLACK'),
    'size':fields.String(description='size',required=True,example='M'),
    'material':fields.String(description='material',required=True,example='100% COTTON'),
    'season':fields.String(description='season',required=True,example='2022F/W'),
    'blNumber':fields.String(description='BL number',required=True,example='-'),
    'description':fields.String(description='description',required=True,example='memo'),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'eventCost':fields.Integer(description='event cost',required=True,example=0),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000),
    'managementCostRate':fields.Float(description='management cost rate',required=True,example=50.5),
    'departmentStoreCost':fields.Integer(description='department store cost',required=True,example=800000),
    'outletCost':fields.Integer(description='outlet cost',required=True,example=800000),
    'firstCost':fields.Integer(description='first cost',required=True,example=700000),
    'userId':fields.String(description='user ID',required=True,example='admin')
})

consignment_modify_fields = consignment_ns.model('consignment modify fields', {
    'goodsTag':fields.String(description='goods tag',required=True,example='tag'),
    'registerType':fields.Integer(description='register type | 1: excel, 2: batch, 3: handwork',required=True,example=1),
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-02'),
    'importDate':fields.String(description='import date',required=True,example='2022-11-01'),
    'supplierTag':fields.Integer(description='supplier tag',required=True,example=1),
    'officeTag':fields.Integer(description='office tag',required=True,example=1),
    'partNumber':fields.String(description='part number',required=True,example='EXAMPLE-001M'),
    'brandTag':fields.String(description='brand Tag',required=True,example='AP'),
    'categoryTag':fields.String(description='category Tag',required=True,example='BAG'),
    'origin':fields.String(description='origin',required=True,example='ITALY'),
    'sex':fields.Integer(description='sec | 0:unisex, 1:male, 2:female',required=True,example=1),
    'color':fields.String(description='color',required=True,example='BLACK'),
    'size':fields.String(description='size',required=True,example='M'),
    'material':fields.String(description='material',required=True,example='100% COTTON'),
    'season':fields.String(description='season',required=True,example='2022F/W'),
    'blNumber':fields.String(description='BL number',required=True,example='-'),
    'description':fields.String(description='description',required=True,example='memo'),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'eventCost':fields.Integer(description='event cost',required=True,example=0),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000),
    'managementCostRate':fields.Float(description='management cost rate',required=True,example=50.5),
    'departmentStoreCost':fields.Integer(description='department store cost',required=True,example=800000),
    'outletCost':fields.Integer(description='outlet cost',required=True,example=800000),
    'firstCost':fields.Integer(description='first cost',required=True,example=700000),
    'userId':fields.String(description='user ID',required=True,example='admin')
})

consignment_register_response_fields = consignment_ns.model('consignment register response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'tag':fields.String(description='goods tag',required=True,example='GOODSTAG')
})

consignment_base_information_fields = consignment_ns.model('consignment base information fields', {
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-02'),
    'importDate':fields.String(description='import date',required=True,example='2022-11-01'),
    'registerDate':fields.String(description='register date',required=True,example='2022-11-03'),
    'supplier':fields.String(description='supplier',required=True,example='supplier'),
    'office':fields.String(description='office',required=True,example='office'),
    'partNumber':fields.String(description='part number',required=True,example='EXAMPLE-001M'),
    'brand':fields.String(description='brand Tag',required=True,example='AP'),
    'category':fields.String(description='category Tag',required=True,example='BAG'),
    'origin':fields.String(description='origin',required=True,example='ITALY'),
    'sex':fields.String(description='sex',required=True,example='male'),
    'color':fields.String(description='color',required=True,example='BLACK'),
    'size':fields.String(description='size',required=True,example='M'),
    'material':fields.String(description='material',required=True,example='100% COTTON'),
    'season':fields.String(description='season',required=True,example='2022F/W'),
    'blNumber':fields.String(description='BL number',required=True,example='-'),
    'description':fields.String(description='description',required=True,example='memo')
})

consignment_cost_information_fields = consignment_ns.model('consignment cost information fields',{
    'cost':fields.Integer(description='cost',required=True,example=0),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'eventCost':fields.Integer(description='event cost',required=True,example=0),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000),
    'managementCostRate':fields.Float(description='management cost rate',required=True,example=50.5),
    'departmentStoreCost':fields.Integer(description='department store cost',required=True,example=800000),
    'outletCost':fields.Integer(description='outlet cost',required=True,example=800000),
    'firstCost':fields.Integer(description='first cost',required=True,example=700000)
})

consignment_image_fields = consignment_ns.model('consignment image fields', {
    'imageIndex':fields.Integer(description='image index',required=True,example=1),
    'imagePath':fields.String(description='image path',required=True,example='/path/to/image'),
    'imageType':fields.String(description='image type',required=True,example='jpg'),
    'imageName':fields.String(description='image name',required=True,example='test.jpg'),
    'imageUrl':fields.String(description='image url',required=True,example='url')
})

consignment_sold_information_fields = consignment_ns.model('consignment sold information fields', {
    'saleDate':fields.String(description='sale date',required=True,example='2022-11-20'),
    'type':fields.String(description='sale type', required=True,example='home shopping'),
    'cost':fields.Integer(description='sale price',required=True,example=750000),
    'commissionRate':fields.Float(description='commissionRate',required=True,example=15.5),
    'sellerName':fields.String(description='seller name',required=True,example='seller'),
    'customer':fields.String(description='customer name/number',required=True,example='customer'),
    'orderNumber':fields.String(description='order number',required=True,example='order number'),
    'invoiceNumber':fields.String(description='invoice number',required=True,example='invoice number'),
    'receiverName':fields.String(description='receiver name',required=True,example='receiver'),
    'receiverPhoneNumber':fields.String(description='receiver phone number',required=True,example='010-1111-1111'),
    'receiverAddress':fields.String(description='receiver address',required=True,example='address')
})

consignment_history_fields = consignment_ns.model('consignment history fields', {
    'date':fields.String(description='date',required=True,example='2022-11-01 00:00:00'),
    'jobName':fields.String(description='job name',required=True,example='register goods'),
    'officeName':fields.String(description='office name',required=True,example='office'),
    'status':fields.String(description='status',required=True,example='status'),
    'updateValue':fields.String(description='update value',required=True,example='value'),
    'updateMethod':fields.String(description='update method',required=True,example='method'),
    'userName':fields.String(description='user name',required=True,example='admin')
})

get_consignment_detail_fields = consignment_ns.model('consignment detail get fields', {
    'baseInformation':fields.Nested(consignment_base_information_fields),
    'costInformation':fields.Nested(consignment_cost_information_fields),
    'importCertificateImages':fields.List(fields.Nested(consignment_image_fields)),
    'goodsImages':fields.List(fields.Nested(consignment_image_fields)),
    'soldInformation':fields.Nested(consignment_sold_information_fields),
    'goodsHistory':fields.List(fields.Nested(consignment_history_fields))
})

consignment_calculate_fields = consignment_ns.model('consignment calculate fields', {
    'index':fields.Integer(description='index',required=True,example=1),
    'supplierTag':fields.Integer(description='supplier tag',required=True,example=1),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier'),
    'stockCount':fields.Integer(description='total stock count',required=True,example=100),
    'saleCount':fields.Integer(description='total sale count',required=True,example=100),
    'returnCount':fields.Integer(description='total return count',required=True,example=100),
    'remainCount':fields.Integer(description='total remain count',required=True,example=100),
    'stockCost':fields.Integer(description='total stock cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='total sale cost',required=True,example=1000000),
    'returnCost':fields.Integer(description='total return cost',required=True,example=1000000),
    'remainCost':fields.Integer(description='total remain cost',required=True,example=1000000),
    'calculateCost':fields.Integer(description='total calculate cost',required=True,example=1000000)
})

consignment_calculate_response_fields = consignment_ns.model('consignment calculate response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(consignment_calculate_fields)),
    'totalSearchResult':fields.Integer(description='search result total',required=True,example=123),
    'totalStockCount':fields.Integer(description='total stock count',required=True,example=100),
    'totalSaleCount':fields.Integer(description='total sale count',required=True,example=100),
    'totalReturnCount':fields.Integer(description='total return count',required=True,example=100),
    'totalRemainCount':fields.Integer(description='total remain count',required=True,example=100),
    'totalStockCost':fields.Integer(description='total stock cost',required=True,example=1000000),
    'totalSaleCost':fields.Integer(description='total sale cost',required=True,example=1000000),
    'totalReturnCost':fields.Integer(description='total return cost',required=True,example=1000000),
    'totalRemainCost':fields.Integer(description='total remain cost',required=True,example=1000000),
    'totalCalculateCost':fields.Integer(description='total calculate cost',required=True,example=1000000),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10)
})

consignment_calculate_detail_fields = consignment_ns.model('consignment calculate detail fields', {
    'tag':fields.String(description='goods tag',required=True,example='113AB1611120BC149'),
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-02'),
    'importDate':fields.String(description='import date',required=True,example='2022-11-01'),
    'registerDate':fields.String(description='register date',required=True,example='2022-11-03'),
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
    'saleDate':fields.String(description='sale date',required=True,example='2022-11-10'),
    'office':fields.String(description='office name',required=True,example='office'),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'firstCost':fields.Integer(description='first cost',required=True,example=800000),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000),
    'description':fields.String(description='description',required=True,example='description')
})

consignment_calculate_detail_response_fields = consignment_ns.model('consignment calculate detail response fields',{
    'supplier':fields.String(description='supplier name',required=True,example='supplier'),
    'totalCount':fields.Integer(description='total count',required=True,example=100),
    'list':fields.List(fields.Nested(consignment_calculate_detail_fields))
})

consignment_return_response_fields = consignment_ns.model('consignment return response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'tag':fields.String(description='goods tag',required=True,example='tag')
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['consignment_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@consignment_ns.route('')
class consignmentApiList(Resource):

    @consignment_ns.expect(consignment_query_parser)
    @consignment_ns.response(200, 'OK', consignment_list_response_fields)
    @consignment_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get consignment list 
        '''
        args = consignment_query_parser.parse_args()
        res = requests.get(f"http://{management_url}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@consignment_ns.route('/<string:goodsTag>')
class consignmentDetailApiList(Resource):

    @consignment_ns.response(200, 'OK', get_consignment_detail_fields)
    @consignment_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,goodsTag):
        '''
        get consignment Detail
        '''
        res = requests.get(f"http://{management_url}/{goodsTag}", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @consignment_ns.expect(consignment_modify_fields)
    @consignment_ns.response(200, 'OK', consignment_register_response_fields)
    @consignment_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,goodsTag):
        '''
        adjust consignment information
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/{goodsTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @consignment_ns.expect(consignment_register_fields)
    @consignment_ns.response(201, 'OK', consignment_register_response_fields)
    @consignment_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self,goodsTag):
        '''
        register consignment
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/{goodsTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @consignment_ns.doc(responses={204: 'OK'})
    @jwt_required()
    def delete(self,goodsTag):
        '''
        delete consignment
        '''
        res = requests.delete(f"http://{management_url}/{goodsTag}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@consignment_ns.route('/<string:goodsTag>/image')
class consignmentImageApiList(Resource):

    @consignment_ns.expect(upload_parser)
    @consignment_ns.response(201, 'OK', consignment_register_response_fields)
    @consignment_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self,goodsTag):
        '''
        register consignment image
        '''
        id = get_jwt_identity()
        args = upload_parser.parse_args()
        args['userId'] = id
        file_list = list()
        for upload_file_info in flask.request.files:
            upload_files = flask.request.files.getlist(upload_file_info)
            for upload_file in upload_files:
                filename = upload_file.filename
                file_ = upload_file.read()
                type_ = upload_file.content_type
                file_list.append(('files',(filename,file_,type_)))
        res = requests.post(f"http://{management_url}/{goodsTag}/image", files=file_list, params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@consignment_ns.route('/<string:goodsTag>/return')
class consignmentReturnApiList(Resource):

    @consignment_ns.response(200, 'OK', consignment_return_response_fields)
    @consignment_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,goodsTag):
        '''
        return consignment
        '''
        id = get_jwt_identity()
        args = dict()
        args['userId'] = id
        res = requests.put(f"http://{management_url}/{goodsTag}/return", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@consignment_ns.route('/<string:goodsTag>/image/<int:imageIndex>')
class consignmentImageDetailApiList(Resource):
    
    @consignment_ns.doc(responses={204: 'OK'})
    @jwt_required()
    def delete(self,goodsTag,imageIndex):
        '''
        delete consignment image
        '''
        res = requests.delete(f"http://{management_url}/{goodsTag}/image/{imageIndex}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@consignment_ns.route('/calculate')
class consignmentCalculateApiList(Resource):

    @consignment_ns.expect(consignment_calculate_query_parser)
    @consignment_ns.response(200, 'OK', consignment_calculate_response_fields)
    @consignment_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get consignment calculate list 
        '''
        args = consignment_calculate_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/firstCost", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@consignment_ns.route('/calculate/<int:supplierTag>')
class consignmentCalculateDetailApiList(Resource):

    @consignment_ns.expect(consignment_calculate_detail_query_parser)
    @consignment_ns.response(200, 'OK', consignment_calculate_detail_response_fields)
    @consignment_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,supplierTag):
        '''
        get consignment calculate Detail 
        '''
        args = consignment_calculate_detail_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/firstCost/{supplierTag}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code
