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

inventory_ns = Namespace('Inventory', version="1.0", title='Inventory API List', description='Inventory API List')

goods_list_query_parser = reqparse.RequestParser()
goods_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
goods_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
goods_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
goods_list_query_parser.add_argument('startDate', type=str, help='search start date')
goods_list_query_parser.add_argument('endDate', type=str, help='search end date')
goods_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
goods_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
goods_list_query_parser.add_argument('statusList', type=int, help='goods status | 1:scretch, 2:unable sale, 3:discard, 4:normal, 5:lost, 6:waiting for calculate, 7:waiting for distribution, 8:retrieve success, 9:fixing, 10:waiting for return calculate, 11:sold, 12:waiting for move sign, 13:waiting for client return', action='append')
goods_list_query_parser.add_argument('seasonList', type=str, help='search season list', action='append')
goods_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
goods_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
goods_list_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
goods_list_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
goods_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
goods_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
goods_list_query_parser.add_argument('searchContent', type=str, help='search content')

part_number_inventory_list_query_parser = reqparse.RequestParser()
part_number_inventory_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
part_number_inventory_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
part_number_inventory_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
part_number_inventory_list_query_parser.add_argument('startDate', type=str, help='search start date')
part_number_inventory_list_query_parser.add_argument('endDate', type=str, help='search end date')
part_number_inventory_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
part_number_inventory_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
part_number_inventory_list_query_parser.add_argument('statusList', type=int, help='goods status | 1:scretch, 2:unable sale, 3:discard, 4:normal, 5:lost, 6:waiting for calculate, 7:waiting for distribution, 8:retrieve success, 9:fixing, 10:waiting for return calculate, 11:sold, 12:waiting for move sign, 13:waiting for client return', action='append')
part_number_inventory_list_query_parser.add_argument('seasonList', type=str, help='search season list', action='append')
part_number_inventory_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
part_number_inventory_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
part_number_inventory_list_query_parser.add_argument('supplierTypeList', type=int, help='supplier type list | 1:consignment, 2:buying, 3:direct import, 4:not in stock', action='append')
part_number_inventory_list_query_parser.add_argument('supplierTagList', type=int, help='supplier tag list', action='append')
part_number_inventory_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
part_number_inventory_list_query_parser.add_argument('soldOutFlag', type=int, help='sold out flag | 0: not include, 1: include')
part_number_inventory_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
part_number_inventory_list_query_parser.add_argument('searchContent', type=str, help='search content')

part_number_inventory_detail_query_parser = reqparse.RequestParser()
part_number_inventory_detail_query_parser.add_argument('stockingDate', required=True, type=str, help='stocking date')
part_number_inventory_detail_query_parser.add_argument('supplierTag', required=True, type=int, help='supplier tag')

brand_inventory_list_query_parser = reqparse.RequestParser()
brand_inventory_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
brand_inventory_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
brand_inventory_list_query_parser.add_argument('date', type=str, help='search date')
brand_inventory_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
brand_inventory_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
brand_inventory_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')

brand_inventory_list_detail_query_parser = reqparse.RequestParser()
brand_inventory_list_detail_query_parser.add_argument('date', type=str, help='search date')
brand_inventory_list_detail_query_parser.add_argument('categoryTag', required=True, type=str, help='search category tag')
brand_inventory_list_detail_query_parser.add_argument('officeTag', required=True, type=int, help='office tag')

office_inventory_list_query_parser = reqparse.RequestParser()
office_inventory_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
office_inventory_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
office_inventory_list_query_parser.add_argument('date', type=str, help='search date')
office_inventory_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
office_inventory_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
office_inventory_list_query_parser.add_argument('officeTagList', type=int, help='office tag list', action='append')
office_inventory_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
office_inventory_list_query_parser.add_argument('searchContent', type=str, help='search content')

office_inventory_list_detail_query_parser = reqparse.RequestParser()
office_inventory_list_detail_query_parser.add_argument('date', type=str, help='search date')
office_inventory_list_detail_query_parser.add_argument('partNumber', required=True, type=str, help='part number')

sold_out_list_query_parser = reqparse.RequestParser()
sold_out_list_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
sold_out_list_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
sold_out_list_query_parser.add_argument('dateType', type=int, default=0, help='date type : 0:stocking date, 1:import date, 2: register date')
sold_out_list_query_parser.add_argument('startDate', type=str, help='search start date')
sold_out_list_query_parser.add_argument('endDate', type=str, help='search end date')
sold_out_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
sold_out_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
sold_out_list_query_parser.add_argument('sex', type=int, help='search sex | 0:unisex, 1:male, 2:female')
sold_out_list_query_parser.add_argument('originList', type=str, help='search origin name list', action='append')
sold_out_list_query_parser.add_argument('searchType', type=int, help='search type | 0:part_number, 1:tag, 2:color, 3:material, 4:size')
sold_out_list_query_parser.add_argument('searchContent', type=str, help='search content')
sold_out_list_query_parser.add_argument('soldOutStartDate', type=str, help='search sold out start date')
sold_out_list_query_parser.add_argument('soldOutEndDate', type=str, help='search end date')

receipt_payment_list_query_parser = reqparse.RequestParser()
receipt_payment_list_query_parser.add_argument('startDate', type=str, required=True, help='search start date')
receipt_payment_list_query_parser.add_argument('endDate', type=str, required=True, help='search end date')
receipt_payment_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
receipt_payment_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')

receipt_payment_detail_list_query_parser = reqparse.RequestParser()
receipt_payment_detail_list_query_parser.add_argument('startDate', type=str, required=True, help='search start date')
receipt_payment_detail_list_query_parser.add_argument('endDate', type=str, required=True, help='search end date')
receipt_payment_detail_list_query_parser.add_argument('brandTagList', type=str, help='search brand tag list', action='append')
receipt_payment_detail_list_query_parser.add_argument('categoryTagList', type=str, help='search category tag list', action='append')
receipt_payment_detail_list_query_parser.add_argument('item', type=int, help='search item | empty: total, 1: baseInventory, 2: stokcing, 3: sale, 4: inventorySetting, 5: consignment return')

goods_list_fields = inventory_ns.model('inventory goods list fields', {
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
    'status':fields.String(description='goods status',required=True,example='normal'),
    'firstCost':fields.Integer(description='first cost',required=True,example=100000),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000),
    'inventoryDays':fields.Integer(description='inventory days',required=True,example=100)
})

goods_list_response_fields = inventory_ns.model('inventory goods list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(goods_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalResult':fields.Integer(description='total result',required=True,example=15)
})

part_number_inventory_list_fields = inventory_ns.model('part number inventory list fields',{
    'supplierType':fields.String(description='supplier type',required=True,example='type'),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier name'),
    'supplierTag':fields.Integer(description='supplier tag',required=True,example=1),
    'brand':fields.String(description='brand name',required=True,example='A.p.c.'),
    'category':fields.String(description='category name',required=True,example='Bag'),
    'imageUrl':fields.String(description='image url',required=True,example='url'),
    'season':fields.String(description='season',required=True,example='2022F/W'),
    'partNumber':fields.String(description='part number',required=True,example='EXAMPLE-001M'),
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-11-02'),
    'sex':fields.String(description='sex',required=True,example='male'),
    'color':fields.String(description='color',required=True,example='BLACK'),
    'material':fields.String(description='material',required=True,example='100% COTTON'),
    'origin':fields.String(description='origin',required=True,example='ITALY'),
    'inventoryCount':fields.Integer(description='inventory count',required=True,example=100),
    'officeAndInventoryCount':fields.String(description='office / inventory count',required=True,example='office\t/ 1\noffice2\t 2'),
    'stockingCount':fields.Integer(description='total stocking count',required=True,example=200),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'firstCost':fields.Integer(description='first cost',required=True,example=100000),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000)
})

part_number_inventory_list_response_fields = inventory_ns.model('part number inventory list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'totalStockingCount':fields.Integer(description='total stocking count',required=True,example=10000),
    'totalInventoryCount':fields.Integer(description='total inventory count',required=True,example=5000),
    'totalCost':fields.Integer(description='cost',required=True,example=0),
    'totalFirstCost':fields.Integer(description='first cost',required=True,example=100000),
    'totalRegularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'totalSaleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'totalDiscountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'totalManagementCost':fields.Integer(description='management cost',required=True,example=50000),
    'list':fields.List(fields.Nested(part_number_inventory_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalResult':fields.Integer(description='total result',required=True,example=15)
})

inventory_detail_list_fields = inventory_ns.model('inventory goods detail list fields', {
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
    'status':fields.String(description='goods status',required=True,example='normal'),
    'firstCost':fields.Integer(description='first cost',required=True,example=100000),
    'cost':fields.Integer(description='cost',required=True,example=0),
    'regularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'saleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'discountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'managementCost':fields.Integer(description='management cost',required=True,example=50000)
})

part_number_inventory_detail_list_response_fields = inventory_ns.model('part number inventory goods detail list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'partNumber':fields.String(description='part number',required=True,example='part number'),
    'stockingDate':fields.String(description='stocking date',required=True,example='2022-12-01'),
    'supplierName':fields.String(description='supplier name',required=True,example='supplier name'),
    'firstCost':fields.Integer(description='first cost',required=True,example=100000),
    'totalInventoryCount':fields.Integer(description='total inventory count',required=True,example=100),
    'totalStockingCount':fields.Integer(description='total stocking count',required=True,example=200),
    'brand':fields.String(description='brand',required=True,example='A.P.C'),
    'category':fields.String(description='category',required=True,example='Bag'),
    'list':fields.List(fields.Nested(inventory_detail_list_fields))
})

brand_inventory_list_fields = inventory_ns.model('brand inventory list fields',{
    'index':fields.Integer(description='index',required=True,example=1),
    'brand':fields.String(description='brand',required=True,example='A.P.C'),
    'brandTag':fields.String(description='brand tag',required=True,example='AP'),
    'category':fields.String(description='category',required=True,example='Bag'),
    'categoryTag':fields.String(description='category tag',required=True,example='BG'),
    'office':fields.String(description='office',required=True,example='office name'),
    'officeTag':fields.Integer(description='office tag',required=True,example=2),
    'inventoryCount':fields.Integer(description='inventory count',required=True,example=10),
    'totalCost':fields.Integer(description='cost',required=True,example=0),
    'totalFirstCost':fields.Integer(description='first cost',required=True,example=100000),
    'totalRegularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'totalSaleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'totalDiscountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'totalManagementCost':fields.Integer(description='management cost',required=True,example=50000)
})

brand_inventory_list_response_fields = inventory_ns.model('brand inventory list response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(brand_inventory_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalResult':fields.Integer(description='total result',required=True,example=15)
})

brand_inventory_detail_list_response_fields = inventory_ns.model('brand inventory goods detail list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'totalInventoryCount':fields.Integer(description='total inventory count',required=True,example=100),
    'totalStockingCount':fields.Integer(description='total stocking count',required=True,example=200),
    'totalCost':fields.Integer(description='cost',required=True,example=0),
    'totalFirstCost':fields.Integer(description='first cost',required=True,example=100000),
    'totalRegularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'totalSaleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'totalDiscountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'totalManagementCost':fields.Integer(description='management cost',required=True,example=50000),
    'date':fields.String(description='search date',required=True,example='2022-12-01'),
    'brand':fields.String(description='brand',required=True,example='A.P.C'),
    'category':fields.String(description='category',required=True,example='Bag'),
    'office':fields.String(description='office',required=True,example='office name'),
    'list':fields.List(fields.Nested(inventory_detail_list_fields))
})

office_inventory_list_fields = inventory_ns.model('office inventory list fields', {
    'index':fields.Integer(description='index',required=True,example=1),
    'office':fields.String(description='office name',required=True,example='office name'),
    'officeTag':fields.Integer(description='office tag',required=True,example=2),
    'brand':fields.String(description='brand name',required=True,example='A.P.C'),
    'category':fields.String(description='category name',required=True,example='Bag'),
    'partNumber':fields.String(description='part number',required=True,example='part number'),
    'totalCost':fields.Integer(description='cost',required=True,example=0),
    'totalFirstCost':fields.Integer(description='first cost',required=True,example=100000),
    'totalRegularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'totalSaleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'totalDiscountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'totalManagementCost':fields.Integer(description='management cost',required=True,example=50000),
    'inventorycount':fields.Integer(description='inventory count',required=True,example=100)
})

office_inventory_list_response_fields = inventory_ns.model('office inventory list response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(office_inventory_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalResult':fields.Integer(description='total result',required=True,example=15)
})

office_inventory_detail_list_response_fields = inventory_ns.model('office inventory goods detail list response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'totalInventoryCount':fields.Integer(description='total inventory count',required=True,example=100),
    'totalStockingCount':fields.Integer(description='total stocking count',required=True,example=200),
    'totalCost':fields.Integer(description='cost',required=True,example=0),
    'totalFirstCost':fields.Integer(description='first cost',required=True,example=100000),
    'totalRegularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'totalSaleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'totalDiscountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'totalManagementCost':fields.Integer(description='management cost',required=True,example=50000),
    'date':fields.String(description='search date',required=True,example='2022-12-01'),
    'brand':fields.String(description='brand',required=True,example='A.P.C'),
    'category':fields.String(description='category',required=True,example='Bag'),
    'office':fields.String(description='office',required=True,example='office name'),
    'list':fields.List(fields.Nested(inventory_detail_list_fields))
})

sold_out_list_fields = inventory_ns.model('sold out list fields', {
    'soldOutDate':fields.String(description='sold out date',required=True,example='2022-11-01'),
    'partNumber':fields.String(description='part number',required=True,example='part number'),
    'season':fields.String(description='season',required=True,example='2022F/W'),
    'brand':fields.String(description='brand',required=True,example='A.P.C'),
    'category':fields.String(description='category',required=True,example='Bag'),
    'color':fields.String(descripiton='color',required=True,example='black'),
    'size':fields.String(description='size',required=True,example='S'),
    'origin':fields.String(description='origin',required=True,example='Italy'),
    'material':fields.String(description='material',required=True,example='wool')
})

sold_out_list_response_fields = inventory_ns.model('sold out list response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(sold_out_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10),
    'totalResult':fields.Integer(description='total result',required=True,example=15)
})

receipt_payment_list_fields = inventory_ns.model('receipt and payment list fields',{
    'office':fields.String(description='office name',required=True,example='office'),
    'officeTag':fields.Integer(description='office tag',required=True,example=2),
    'baseInventoryCount':fields.Integer(description='base inventory count',required=True,example=1000),
    'stockingCount':fields.Integer(description='stocking count',required=True,example=100),
    'saleCount':fields.Integer(description='sale count',required=True,example=50),
    'inventorySettingCount':fields.Integer(description='inventory setting count',required=True,example=0),
    'consignmentReturnCount':fields.Integer(description='consignment return count',required=True,example=-10),
    'totalInventoryCount':fields.Integer(description='total inventory count',required=True,example=1060)
})

receipt_payment_list_response_fields = inventory_ns.model('receipt and payment list response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(receipt_payment_list_fields))
})

receipt_payment_detail_list_response_fields = inventory_ns.model('receipt and payment detail list response fields',{
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'totalCost':fields.Integer(description='cost',required=True,example=0),
    'totalFirstCost':fields.Integer(description='first cost',required=True,example=100000),
    'totalRegularCost':fields.Integer(description='regular cost',required=True,example=1000000),
    'totalSaleCost':fields.Integer(description='sale cost',required=True,example=900000),
    'totalDiscountCost':fields.Integer(description='discount cost',required=True,example=850000),
    'totalManagementCost':fields.Integer(description='management cost',required=True,example=50000),
    'office':fields.String(description='office',required=True,example='office name'),
    'item':fields.String(description='search item name',required=True,example='baseInventory'),
    'list':fields.List(fields.Nested(inventory_detail_list_fields))
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['inventory_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@inventory_ns.route('')
class inventoryApiList(Resource):

    @inventory_ns.expect(goods_list_query_parser)
    @inventory_ns.response(200, 'OK', goods_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get goods list for inventory
        '''
        args = goods_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/partNumber')
class partNumberInventoryApiList(Resource):

    @inventory_ns.expect(part_number_inventory_list_query_parser)
    @inventory_ns.response(200, 'OK', part_number_inventory_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get inventory list by part number
        '''
        args = part_number_inventory_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/partNumber", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/partNumber')
class partNumberInventoryApiList(Resource):

    @inventory_ns.expect(part_number_inventory_list_query_parser)
    @inventory_ns.response(200, 'OK', part_number_inventory_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get inventory list by part number
        '''
        args = part_number_inventory_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/partNumber", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/partNumber/<string:partNumber>')
class partNumberInventoryDetailApiList(Resource):

    @inventory_ns.expect(part_number_inventory_detail_query_parser)
    @inventory_ns.response(200, 'OK', part_number_inventory_detail_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,partNumber):
        '''
        get detail inventory list by part number
        '''
        args = part_number_inventory_detail_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/partNumber/{partNumber}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/brand')
class brandInventoryApiList(Resource):

    @inventory_ns.expect(brand_inventory_list_query_parser)
    @inventory_ns.response(200, 'OK', brand_inventory_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get inventory list by brand
        '''
        args = brand_inventory_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/brand", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/brand/<string:brandTag>')
class brandInventoryDetailApiList(Resource):

    @inventory_ns.expect(brand_inventory_list_detail_query_parser)
    @inventory_ns.response(200, 'OK', brand_inventory_detail_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,brandTag):
        '''
        get detail inventory list by brand
        '''
        args = brand_inventory_list_detail_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/brand/{brandTag}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/office')
class officeInventoryApiList(Resource):

    @inventory_ns.expect(office_inventory_list_query_parser)
    @inventory_ns.response(200, 'OK', office_inventory_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get inventory list by office
        '''
        args = office_inventory_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/office", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/office/<int:officeTag>')
class officeInventoryDetailApiList(Resource):

    @inventory_ns.expect(office_inventory_list_detail_query_parser)
    @inventory_ns.response(200, 'OK', office_inventory_detail_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,officeTag):
        '''
        get detail inventory list by office
        '''
        args = office_inventory_list_detail_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/office/{officeTag}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/soldOut')
class soldOutApiList(Resource):

    @inventory_ns.expect(sold_out_list_query_parser)
    @inventory_ns.response(200, 'OK', sold_out_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get sold out list
        '''
        args = sold_out_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/soldOut", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/receiptPayment')
class receiptPaymentApiList(Resource):

    @inventory_ns.expect(receipt_payment_list_query_parser)
    @inventory_ns.response(200, 'OK', receipt_payment_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get receipt and payment list
        '''
        args = receipt_payment_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/receiptPayment", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@inventory_ns.route('/receiptPayment/<int:officeTag>')
class receiptPaymentDetailApiList(Resource):

    @inventory_ns.expect(receipt_payment_detail_list_query_parser)
    @inventory_ns.response(200, 'OK', receipt_payment_detail_list_response_fields)
    @inventory_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self,officeTag):
        '''
        get receipt and payment detail list
        '''
        args = receipt_payment_detail_list_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/receiptPayment/{officeTag}", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code