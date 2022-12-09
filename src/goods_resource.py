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

goods_ns = Namespace('Goods', version="1.0", title='Goods API List', description='Goods API List')

goods_query_parser = reqparse.RequestParser()
goods_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
goods_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
goods_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
goods_query_parser.add_argument('startDate', type=str, help='search start date')
goods_query_parser.add_argument('endDate', type=str, help='search end date')
goods_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
goods_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
goods_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
goods_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
goods_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
goods_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
goods_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
goods_query_parser.add_argument('statusList', type=int, help='goods status | 1:scretch, 2:unable sale, 3:discard, 4:normal, 5:lost, 6:waiting for calculate, 7:waiting for distribution, 8:retrieve success, 9:fixing, 10:waiting for return calculate, 11:sold, 12:waiting for move sign, 13:waiting for client return', action='append')
goods_query_parser.add_argument('imageFlag', type=int, help='search image | 0:all, 1:included 2: not included')
goods_query_parser.add_argument('seasonList', type=str, help='search season list', action='append')
goods_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
goods_query_parser.add_argument('searchContent', type=str, help='search content')

first_cost_query_parser = reqparse.RequestParser()
first_cost_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
first_cost_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
first_cost_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
first_cost_query_parser.add_argument('startDate', type=str, help='search start date')
first_cost_query_parser.add_argument('endDate', type=str, help='search end date')
first_cost_query_parser.add_argument('seasonList', type=str, help='search season list', action='append')
first_cost_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
first_cost_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
first_cost_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
first_cost_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
first_cost_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
first_cost_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
first_cost_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
first_cost_query_parser.add_argument('searchContent', type=str, help='search content')

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('files', location='files', type=werkzeug.datastructures.FileStorage, help='file upload', action='append')
upload_parser.add_argument('type', location='args', type=int, help='type | 1: goods image, 2: import certificate images')

goods_list_fields = goods_ns.model('goods list fields', {
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
    'managementCost':fields.Integer(description='management cost',required=True,example=50000)
})

goods_list_response_fields = goods_ns.model('goods list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(goods_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalGoods':fields.Integer(description='totalGoods',required=True,example=15)
})

goods_register_fields = goods_ns.model('goods register fields', {
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

goods_modify_fields = goods_ns.model('goods modify fields', {
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

goods_register_response_fields = goods_ns.model('goods register response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'tag':fields.String(description='goods tag',required=True,example='GOODSTAG')
})

goods_base_information_fields = goods_ns.model('goods base information fields', {
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

goods_cost_information_fields = goods_ns.model('goods cost information fields',{
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

goods_image_fields = goods_ns.model('goods image fields', {
    'imageIndex':fields.Integer(description='image index',required=True,example=1),
    'imagePath':fields.String(description='image path',required=True,example='/path/to/image'),
    'imageType':fields.String(description='image type',required=True,example='jpg'),
    'imageName':fields.String(description='image name',required=True,example='test.jpg'),
    'imageUrl':fields.String(description='image url',required=True,example='url')
})

goods_sold_information_fields = goods_ns.model('goods sold information fields', {
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

goods_history_fields = goods_ns.model('goods history fields', {
    'date':fields.String(description='date',required=True,example='2022-11-01 00:00:00'),
    'jobName':fields.String(description='job name',required=True,example='register goods'),
    'officeName':fields.String(description='office name',required=True,example='office'),
    'status':fields.String(description='status',required=True,example='status'),
    'updateValue':fields.String(description='update value',required=True,example='value'),
    'updateMethod':fields.String(description='update method',required=True,example='method'),
    'userName':fields.String(description='user name',required=True,example='admin')
})

get_goods_detail_fields = goods_ns.model('goods detail get fields', {
    'baseInformation':fields.Nested(goods_base_information_fields),
    'costInformation':fields.Nested(goods_cost_information_fields),
    'importCertificateImages':fields.List(fields.Nested(goods_image_fields)),
    'goodsImages':fields.List(fields.Nested(goods_image_fields)),
    'soldInformation':fields.Nested(goods_sold_information_fields),
    'goodsHistory':fields.List(fields.Nested(goods_history_fields))
})

goods_first_cost_fields = goods_ns.model('goods first cost fields', {
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-01'),
    'supplierType':fields.String(description='supplier type',required=True,example='direct import'),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier'),
    'supplierTag':fields.Integer(description='supplier tag',required=True,example=1),
    'blNumber':fields.String(description='BL number',required=True,example='11111111'),
    'stockCount':fields.Integer(description='stock count',required=True,example=100),
    'totalStockCost':fields.Integer(description='total stock cost',required=True,example=1000000000),
    'registerName':fields.String(description='register Name',required=True,example='admin'),
    'totalManagementCost':fields.Integer(description='total management cost',required=True,example=1000000000),
    'averageManagementCostRate':fields.Float(description='average management cost',required=True,example=100.0)
})

goods_first_cost_response_fields = goods_ns.model('goods first cost response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(goods_first_cost_fields)),
    'totalSearchResult':fields.Integer(description='search result total',required=True,example=123),
    'totalStockCount':fields.Integer(description='total stock count',required=True,example=12345),
    'totalstockCost':fields.Integer(description='total stock first cost',required=True,example=123456789),
    'totalManagementCost':fields.Integer(description='total management first cost',required=True,example=12345678),
    'averageManagementCostRate':fields.Float(description='average management cost',required=True,example=100.0),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10)
})

goods_first_cost_detail_fields = goods_ns.model('goods first cost detail fields', {
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
    'managementCost':fields.Integer(description='management cost',required=True,example=50000)
})

goods_first_cost_detail_response_fields = goods_ns.model('goods first cost detail response fields',{
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-01'),
    'stockCount':fields.Integer(description='stock count',required=True,example=100),
    'totalStockCost':fields.Integer(description='total stock cost',required=True,example=1000000000),
    'registerName':fields.String(description='register Name',required=True,example='admin'),
    'totalManagementCost':fields.Integer(description='total management cost',required=True,example=1000000000),
    'averageManagementCostRate':fields.Float(description='average management cost',required=True,example=100.0),
    'list':fields.List(fields.Nested(goods_first_cost_detail_fields))
})

management_cost_adjust_response_fields = goods_ns.model('management cost adjust response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS')
})

management_cost_adjust_request_fields = goods_ns.model('management cost adjust request fields', {
    'totalManagemnetCost':fields.Integer(description='total management cost',required=True,example=10000000)
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['goods_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@goods_ns.route('')
class goodsApiList(Resource):

    @goods_ns.expect(goods_query_parser)
    @goods_ns.response(200, 'OK', goods_list_response_fields)
    @goods_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get goods list 
        '''
        args = goods_query_parser.parse_args()
        res = requests.get(f"http://{management_url}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@goods_ns.route('/<string:goodsTag>')
class goodsDetailApiList(Resource):

    @goods_ns.response(200, 'OK', get_goods_detail_fields)
    @goods_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,goodsTag):
        '''
        get goods Detail
        '''
        res = requests.get(f"http://{management_url}/{goodsTag}", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @goods_ns.expect(goods_modify_fields)
    @goods_ns.response(200, 'OK', goods_register_response_fields)
    @goods_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,goodsTag):
        '''
        adjust goods information
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/{goodsTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @goods_ns.expect(goods_register_fields)
    @goods_ns.response(201, 'OK', goods_register_response_fields)
    @goods_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self,goodsTag):
        '''
        register goods
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/{goodsTag}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @goods_ns.doc(responses={204: 'OK'})
    @jwt_required()
    def delete(self,goodsTag):
        '''
        delete goods
        '''
        res = requests.delete(f"http://{management_url}/{goodsTag}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@goods_ns.route('/<string:goodsTag>/image')
class goodsImageApiList(Resource):

    @goods_ns.expect(upload_parser)
    @goods_ns.response(201, 'OK', goods_register_response_fields)
    @goods_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def post(self,goodsTag):
        '''
        register goods image
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

@goods_ns.route('/<string:goodsTag>/image/<int:imageIndex>')
class goodsImageDetailApiList(Resource):
    
    @goods_ns.doc(responses={204: 'OK'})
    @jwt_required()
    def delete(self,goodsTag,imageIndex):
        '''
        delete goods image
        '''
        res = requests.delete(f"http://{management_url}/{goodsTag}/image/{imageIndex}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@goods_ns.route('/firstCost')
class goodsFirstCostApiList(Resource):

    @goods_ns.expect(first_cost_query_parser)
    @goods_ns.response(200, 'OK', goods_first_cost_response_fields)
    @goods_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get goods first cost list 
        '''
        args = first_cost_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/firstCost", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@goods_ns.route('/firstCost/<int:supplierTag>/<string:stockingDate>')
class goodsFirstCostDetailApiList(Resource):

    @goods_ns.response(200, 'OK', goods_first_cost_detail_response_fields)
    @goods_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,supplierTag,stockingDate):
        '''
        get goods first cost Detail 
        '''
        res = requests.get(f"http://{management_url}/firstCost/{supplierTag}/{stockingDate}", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @goods_ns.expect(management_cost_adjust_request_fields)
    @goods_ns.response(200, 'OK', management_cost_adjust_response_fields)
    @goods_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def put(self,supplierTag,stockingDate):
        '''
        adjust management first cost
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.get(f"http://{management_url}/firstCost/{supplierTag}/{stockingDate}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code
