# -*- coding: utf-8 -*-
#!/usr/bin/env python3
  
import logging
import json
import sys
import yaml
import os
import shutil
import traceback

import flask
from flask import request
from flask_api import status

import pymysql

logWriter = None
db_config = None
config_path = "../config/config.yaml"

app = flask.Flask(__name__)

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
    status_code = status.HTTP_200_OK
    try:
        f = open(config_path)
        config = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
        return config, status_code
    except Exception as e:
        result = dict()
        result['message'] = 'Config Load Error.'
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return result, status_code
    
# 상품 리스트 조회
@app.route('/', methods=['GET'])
def saleList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        try:
            params = request.args.to_dict()
            if not 'limit' in params:
                send_data = {"result": "한 페이지당 몇개의 게시물을 표시할지 지정하지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'page' in params:
                send_data = {"result": "현재 페이지를 지정하지 않았습니다"}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            limit = params['limit']
            page = params['page']
            start = (int(page)-1) * int(limit)

            limit_query = f" limit {start}, {limit};"
            condition_query = " WHERE goods.status = 4"

            if 'dateType' in params:
                dateType = int(params['dateType'])
                if dateType < 0 or dateType > 1:
                    send_data = {"result": "날짜 검색 구분이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if dateType == 0:
                    dateString = 'stocking_date'
                else:
                    dateString = 'import_date'
                if 'startDate' in params:
                    startDate = params['startDate']
                    if condition_query:
                        condition_query = condition_query + f" and {dateString} >= '{startDate}'"
                    else:
                        condition_query = f"WHERE {dateString} >= '{startDate}'"
                if 'endDate' in params:
                    endDate = params['endDate']
                    if condition_query:
                        condition_query = condition_query + f" and {dateString} <= '{endDate}'"
                    else:
                       condition_query = f"WHERE {dateString} <= '{endDate}'"
        
            if 'brandTagList' in params:
                brandTags = request.args.getlist('brandTagList')
                brand_query = None
                for brandTag in brandTags:
                    if brand_query:
                        brand_query = brand_query + f" or brand_tag = '{brandTag}'"
                    else:
                        brand_query = f"brand_tag = '{brandTag}'"
                if brand_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({brand_query})"
                    else:
                        condition_query = f"WHERE ({brand_query})"
        
            if 'categoryTagList' in params:
                categoryTags = request.args.getlist('categoryTagList')
                category_query = None
                for categoryTag in categoryTags:
                    if category_query:
                        category_query = category_query + f" or category_tag = '{categoryTag}'"
                    else:
                        category_query = f"category_tag = '{categoryTag}'"
                if category_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({category_query})"
                    else:
                        condition_query = f"WHERE ({category_query})"

            if 'sex' in params:
                sex = int(params['sex'])
                if sex < 0 or sex > 2:
                    send_data = {"result": "성별 구분이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if condition_query:
                    condition_query = condition_query + f" and sex = {sex}"
                else:
                    condition_query = f"WHERE sex = {sex}"

            if 'originList' in params:
                origins = request.args.getlist('originList')
                origin_query = None
                for origin in origins:
                    if origin_query:
                        origin_query = origin_query + f" or origin_name = '{origin}'"
                    else:
                        origin_query = f"origin_name = '{origin}'"
                if origin_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({origin_query})"
                    else:
                        condition_query = f"WHERE ({origin_query})"

            if 'supplierTypeList' in params:
                supplierTypes = request.args.getlist('supplierTypeList')
                supplier_type_query = None
                for supplierType in supplierTypes:
                    if supplier_type_query:
                        supplier_type_query = supplier_type_query + f" or supplier_type = {supplierType}"
                    else:
                        supplier_type_query = f"supplier_type = {supplierType}"
                if supplier_type_query:
                    if condition_query:
                        condition_query = condition_query + f" and supplier_tag IN (SELECT supplier_tag FROM supplier WHERE {supplier_type_query})"
                    else:
                        condition_query = f"WHERE supplier_tag IN (SELECT supplier_tag FROM supplier WHERE {supplier_type_query})"
        
            if 'supplierTagList' in params:
                supplierTags = request.args.getlist('supplierTagList')
                supplier_query = None
                for supplierTag in supplierTags:
                    if supplier_query:
                        supplier_query = supplier_query + f" or supplier_tag = '{supplierTag}'"
                    else:
                        supplier_query = f"supplier_tag = '{supplierTag}'"
                if supplier_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({supplier_query})"
                    else:
                        condition_query = f"WHERE ({supplier_query})"

            if 'officeTagList' in params:
                officeTags = request.args.getlist('officeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or office_tag = '{officeTag}'"
                    else:
                        office_query = f"office_tag = '{officeTag}'"
                if office_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({office_query})"
                    else:
                        condition_query = f"WHERE ({office_query})"
        
            if 'searchType' in params:
                searchType = int(params['searchType'])
                if searchType < 0 or searchType > 4:
                    send_data = {"result": "검색 구분이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if 'searchContent' in params:
                    searchContent = params['searchContent']
                    if searchType == 0:
                        if condition_query:
                            condition_query = condition_query + f" and part_number like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE part_number like '%{searchContent}%'"
                    elif searchType == 1:
                        if condition_query:
                            condition_query = condition_query + f" and goods_tag like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE goods_tag like '%{searchContent}%'"
                    elif searchType == 2:
                        if condition_query:
                            condition_query = condition_query + f" and color like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE color like '%{searchContent}%'"
                    elif searchType == 3:
                        if condition_query:
                            condition_query = condition_query + f" and material like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE material like '%{searchContent}%'"
                    else:
                        if condition_query:
                            condition_query = condition_query + f" and size like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE size like '%{searchContent}%'"
            if condition_query:
                condition_query = condition_query + ' ORDER BY brand'
                query = f"SELECT goods_tag, part_number, bl_number, origin_name, (SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost FROM goods " + condition_query + limit_query + ';'
            else:
                condition_query = ' ORDER BY brand'
                query = f"SELECT goods_tag, part_number, bl_number, origin_name, (SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost FROM goods " + condition_query + limit_query + ';'
            mysql_cursor.execute(query)
            goods_rows = mysql_cursor.fetchall()

            goodsList = list()
            for goods_row in goods_rows:
                data = dict()
                data['tag'] = goods_row[0]
                data['partNumber'] = goods_row[1]
                data['blNumber'] = goods_row[2]
                data['origin'] = goods_row[3]
                data['brand'] = goods_row[4]
                category_tag = goods_row[5]
                office_tag = goods_row[6]
                supplier_tag = goods_row[7]
                data['color'] = goods_row[8]
                data['season'] = goods_row[9]
                sex = goods_row[10]
                data['size'] = goods_row[11]
                data['material'] = goods_row[12]
                data['stockingDate'] = goods_row[13]
                data['importDate'] = goods_row[14]
                data['saleDate'] = goods_row[15]
                data['cost'] = goods_row[16]
                data['regularCost'] = goods_row[17]
                data['saleCost'] = goods_row[18]
                data['discountCost'] = goods_row[19]
                data['managementCost'] = goods_row[20]

                if sex == 0:
                    data['sex'] = '공용'
                elif sex == 1:
                    data['sex'] = '남성'
                else:
                    data['sex'] = '여성'

                query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
                mysql_cursor.execute(query)
                category_row = mysql_cursor.fetchone()
                data['category'] = category_row[0]

                query = f"SELECT office_name FROM office WHERE office_tag = {office_tag};"
                mysql_cursor.execute(query)
                office_row = mysql_cursor.fetchone()
                data['office'] = office_row[0]

                query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = '{supplier_tag}';"
                mysql_cursor.execute(query)
                supplier_row = mysql_cursor.fetchone()
                data['supplierName'] = supplier_row[0]
                #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
                supplier_type = int(supplier_row[1])
                if supplier_type == 1:
                    data['supplierType'] = '위탁'
                elif supplier_type == 2:
                    data['supplierType'] = '사입'
                elif supplier_type == 3:
                    data['supplierType'] = '직수입'
                elif supplier_type == 4:
                    data['supplierType'] = '미입고'

                query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{data['tag']}';"
                mysql_cursor.execute(query)
                image_row = mysql_cursor.fetchone()
                if image_row:
                    data['imageUrl'] = image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
                else:
                    data['imageUrl'] = None

                goodsList.append(data)

            if condition_query:
                query = f"SELECT count(*) FROM goods" + condition_query.replace('ORDER BY brand','') + ';'
            else:
                query = f"SELECT count(*) FROM goods;"
            mysql_cursor.execute(query)
            count_row = mysql_cursor.fetchone()

            send_data['result'] = 'SUCCESS'
            send_data['list'] = goodsList
            send_data['totalPage'] = int(int(count_row[0])/int(limit)) + 1
            send_data['totalMove'] = int(count_row[0])

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#판매 상품 리스트 조회
@app.route('/sold', methods=['GET'])
def soldList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        try:
            params = request.args.to_dict()
            if not 'limit' in params:
                send_data = {"result": "한 페이지당 몇개의 게시물을 표시할지 지정하지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'page' in params:
                send_data = {"result": "현재 페이지를 지정하지 않았습니다"}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            limit = params['limit']
            page = params['page']
            start = (int(page)-1) * int(limit)

            limit_query = f" limit {start}, {limit};"
            condition_query = " WHERE goods.goods_tag = goods_sale.goods_tag and goods.status = 11"

            if 'dateType' in params:
                dateType = int(params['dateType'])
                if dateType < 0 or dateType > 3:
                    send_data = {"result": "날짜 검색 구분이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if dateType == 0:
                    dateString = 'stocking_date'
                elif dateType == 1:
                    dateString = 'import_date'
                elif dateType == 2:
                    dateString = 'register_date'
                else:
                    dateString = 'sale_date'
                if 'startDate' in params:
                    startDate = params['startDate']
                    if condition_query:
                        condition_query = condition_query + f" and {dateString} >= '{startDate}'"
                    else:
                        condition_query = f"WHERE {dateString} >= '{startDate}'"
                if 'endDate' in params:
                    endDate = params['endDate']
                    if condition_query:
                        condition_query = condition_query + f" and {dateString} <= '{endDate}'"
                    else:
                       condition_query = f"WHERE {dateString} <= '{endDate}'"
        
            if 'brandTagList' in params:
                brandTags = request.args.getlist('brandTagList')
                brand_query = None
                for brandTag in brandTags:
                    if brand_query:
                        brand_query = brand_query + f" or brand_tag = '{brandTag}'"
                    else:
                        brand_query = f"brand_tag = '{brandTag}'"
                if brand_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({brand_query})"
                    else:
                        condition_query = f"WHERE ({brand_query})"
        
            if 'categoryTagList' in params:
                categoryTags = request.args.getlist('categoryTagList')
                category_query = None
                for categoryTag in categoryTags:
                    if category_query:
                        category_query = category_query + f" or category_tag = '{categoryTag}'"
                    else:
                        category_query = f"category_tag = '{categoryTag}'"
                if category_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({category_query})"
                    else:
                        condition_query = f"WHERE ({category_query})"

            if 'sex' in params:
                sex = int(params['sex'])
                if sex < 0 or sex > 2:
                    send_data = {"result": "성별 구분이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if condition_query:
                    condition_query = condition_query + f" and sex = {sex}"
                else:
                    condition_query = f"WHERE sex = {sex}"

            if 'originList' in params:
                origins = request.args.getlist('originList')
                origin_query = None
                for origin in origins:
                    if origin_query:
                        origin_query = origin_query + f" or origin_name = '{origin}'"
                    else:
                        origin_query = f"origin_name = '{origin}'"
                if origin_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({origin_query})"
                    else:
                        condition_query = f"WHERE ({origin_query})"

            if 'sellerTypeList' in params:
                sellerTypes = request.args.getlist('sellerTypeList')
                seller_query = None
                for sellerType in sellerTypes:
                    if seller_query:
                        seller_query = seller_query + f" or seller_selling_type.type = {sellerType}"
                    else:
                        seller_query = f"seller_selling_type.type = {sellerType}"
                if seller_query:
                    if condition_query:
                        condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods_sale WHERE seller_tag IN (SELECT seller_tag FROM seller_selling_type WHERE {seller_query}))"
                    else:
                        condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods_sale WHERE seller_tag IN (SELECT seller_tag FROM seller_selling_type WHERE {seller_query}))"

            if 'sellerTagList' in params:
                sellerTags = request.args.getlist('sellerTagList')
                seller_query = None
                for sellerTag in sellerTags:
                    if seller_query:
                        seller_query = seller_query + f" or seller_tag = {sellerTag}"
                    else:
                        seller_query = f"seller_tag = {sellerTag}"
                if seller_query:
                    if condition_query:
                        condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods_sale WHERE {seller_query})"
                    else:
                        condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods_sale WHERE {seller_query})"

            if 'supplierTypeList' in params:
                supplierTypes = request.args.getlist('supplierTypeList')
                supplier_type_query = None
                for supplierType in supplierTypes:
                    if supplier_type_query:
                        supplier_type_query = supplier_type_query + f" or supplier_type = {supplierType}"
                    else:
                        supplier_type_query = f"supplier_type = {supplierType}"
                if supplier_type_query:
                    if condition_query:
                        condition_query = condition_query + f" and supplier_tag IN (SELECT supplier_tag FROM supplier WHERE {supplier_type_query})"
                    else:
                        condition_query = f"WHERE supplier_tag IN (SELECT supplier_tag FROM supplier WHERE {supplier_type_query})"
        
            if 'supplierTagList' in params:
                supplierTags = request.args.getlist('supplierTagList')
                supplier_query = None
                for supplierTag in supplierTags:
                    if supplier_query:
                        supplier_query = supplier_query + f" or supplier_tag = '{supplierTag}'"
                    else:
                        supplier_query = f"supplier_tag = '{supplierTag}'"
                if supplier_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({supplier_query})"
                    else:
                        condition_query = f"WHERE ({supplier_query})"
            
            if 'officeTagList' in params:
                officeTags = request.args.getlist('officeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or office_tag = '{officeTag}'"
                    else:
                        office_query = f"office_tag = '{officeTag}'"
                if office_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({office_query})"
                    else:
                        condition_query = f"WHERE ({office_query})"
                        
            if 'searchType' in params:
                searchType = int(params['searchType'])
                if searchType < 0 or searchType > 4:
                    send_data = {"result": "검색 구분이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if 'searchContent' in params:
                    searchContent = params['searchContent']
                    if searchType == 0:
                        if condition_query:
                            condition_query = condition_query + f" and part_number like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE part_number like '%{searchContent}%'"
                    elif searchType == 1:
                        if condition_query:
                            condition_query = condition_query + f" and goods_tag like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE goods_tag like '%{searchContent}%'"
                    elif searchType == 2:
                        if condition_query:
                            condition_query = condition_query + f" and color like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE color like '%{searchContent}%'"
                    elif searchType == 3:
                        if condition_query:
                            condition_query = condition_query + f" and material like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE material like '%{searchContent}%'"
                    else:
                        if condition_query:
                            condition_query = condition_query + f" and size like '%{searchContent}%'"
                        else:
                            condition_query = f"WHERE size like '%{searchContent}%'"

            if 'saleStartDate' in params:
                saleStartDate = params['saleStartDate']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE sale_date >= '{saleStartDate}')"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE sale_date >= '{saleStartDate}')"

            if 'saleEndDate' in params:
                saleEndDate = params['saleEndDate']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE sale_date <= '{saleEndDate}')"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE sale_date <= '{saleEndDate}')"
            
            if 'orderNumber' in params:
                orderNumber = params['orderNumber']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE order_number like '%{orderNumber}%')"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE order_number like '%{orderNumber}%')"

            if 'invoiceNumber' in params:
                invoiceNumber = params['invoiceNumber']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE invoice_number like '%{invoiceNumber}%')"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE invoice_number like '%{invoiceNumber}%')"

            if 'customer' in params:
                customer = params['customer']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE customer like '%{customer}%')"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE customer like '%{customer}%')"

            if 'receiverName' in params:
                receiverName = params['receiverName']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE receiver_name like '%{receiverName}%')"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE receiver_name like '%{receiverName}%')"

            if 'receiverPhoneNumber' in params:
                receiverPhoneNumber = params['receiverPhoneNumber']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE receiver_phone_number like '%{receiverPhoneNumber}%')"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE receiver_phone_number like '%{receiverPhoneNumber}%')"

            if 'receiverAddress' in params:
                receiverAddress = params['receiverAddress']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE receiver_address like '%{receiverAddress}%')"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE receiver_address like '%{receiverAddress}%')"

            if 'saleRegisterName' in params:
                saleRegisterName = params['saleRegisterName']
                if condition_query:
                    condition_query += f" and goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE user_id IN(SELECT user_id FROM user WHERE user.name like '%{saleRegisterName}%'))"
                else:
                    condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_sale WHERE user_id IN(SELECT user_id FROM user WHERE user.name like '%{saleRegisterName}%'))"

            if condition_query:
                condition_query = condition_query + ' ORDER BY goods_sale.sale_date DESC'
                query = f"SELECT goods_sale.sale_date, (SELECT office_name FROM office WHERE goods.office_tag = office.office_tag) as office, stocking_date, import_date, (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_type, (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_name, bl_number, season, "
                query += f"(SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, (SELECT category_name FROM category WHERE goods.category_tag = category.category_tag) as category, part_number, goods.goods_tag, sex, color, material, "
                query += f"size, origin_name, goods.cost, first_cost, regular_cost, sale_cost, discount_cost, goods_sale.cost, goods_sale.commission_rate, goods_sale.seller_tag, goods_sale.order_number, goods_sale.invoice_number, goods_sale.receiver_name, goods_sale.receiver_phone_number, "
                query += f"goods_sale.receiver_address, goods_sale.description, goods_sale.customer, (SELECT user.name FROM user WHERE goods_sale.user_id = user.user_id) as registerName, register_type FROM goods, goods_sale " + condition_query + limit_query
            else:
                condition_query = ' ORDER BY goods_sale.sale_date DESC'
                query = f"SELECT goods_sale.sale_date, (SELECT office_name FROM office WHERE goods.office_tag = office.office_tag) as office, stocking_date, import_date, (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_type, (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_name, bl_number, season, "
                query += f"(SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, (SELECT category_name FROM category WHERE goods.category_tag = category.category_tag) as category, part_number, goods.goods_tag, sex, color, material, "
                query += f"size, origin_name, goods.cost, first_cost, regular_cost, sale_cost, discount_cost, goods_sale.cost, goods_sale.commission_rate, goods_sale.seller_tag, goods_sale.order_number, goods_sale.invoice_number, goods_sale.receiver_name, goods_sale.receiver_phone_number, "
                query += f"goods_sale.receiver_address, goods_sale.description, goods_sale.customer, (SELECT user.name FROM user WHERE goods_sale.user_id = user.user_id) as registerName, register_type FROM goods, goods_sale " + condition_query + limit_query
            mysql_cursor.execute(query)
            goods_rows = mysql_cursor.fetchall()

            goodsList = list()
            for goods_row in goods_rows:
                data = dict()
                data['saleDate'] = goods_row[0]
                data['status'] = '판매완료'
                data['office'] = goods_row[1]
                data['stockingDate'] = goods_row[2]
                data['importDate'] = goods_row[3]
                data['supplierType'] = goods_row[4]
                data['supplierName'] = goods_row[5]
                data['blNumber'] = goods_row[6]
                data['season'] = goods_row[7]
                data['brand'] = goods_row[8]
                data['category'] = goods_row[9]
                data['partNumber'] = goods_row[10]
                data['tag'] = goods_row[11]
                sex = goods_row[12]
                data['color'] = goods_row[13]
                data['material'] = goods_row[14]
                data['size'] = goods_row[15]
                data['origin'] = goods_row[16]
                data['cost'] = goods_row[17]
                data['firstCost'] = goods_row[18]
                data['regularCost'] = goods_row[19]
                data['saleCost'] = goods_row[20]
                data['discountCost'] = goods_row[21]
                data['realSaleCost'] = goods_row[22]
                data['commissionRate'] = goods_row[23]
                seller_tag = goods_row[24]
                data['orderNumber'] = goods_row[25]
                data['invoiceNumber'] = goods_row[26]
                data['receiverName'] = goods_row[27]
                data['receiverPhoneNumber'] = goods_row[28]
                data['receiverAddress'] = goods_row[29]
                data['description'] = goods_row[30]
                data['customerName'] = goods_row[31]
                data['saleRegisterName'] = goods_row[32]
                register_type = int(goods_row[33])

                data['commissionCost'] = int(data['realSaleCost']*(data['commissionRate']/100)/100)
                data['settlementCost'] = data['realSaleCost']-data['commissionCost']
                data['marginCost'] = data['settlementCost'] - data['firstCost']
                data['discountRate'] = float(data['realSaleCost'])/float(data['regularCost'])*100
                data['saleMarginRate'] = float(data['marginCost'])/float(data['realSaleCost'])*100
                data['firstCostMarginRate'] = float(data['marginCost'])/float(data['firstCost'])*100
                
                if sex == 0:
                    data['sex'] = '공용'
                elif sex == 1:
                    data['sex'] = '남성'
                else:
                    data['sex'] = '여성'

                if register_type == 1:
                    data['registerType'] = '엑셀입력'
                elif register_type == 2:
                    data['registerType'] = '일괄입력'
                else:
                    data['registerType'] = '직접입력'

                query = f"SELECT seller_name FROM seller WHERE seller_tag = {seller_tag};"
                mysql_cursor.execute(query)
                seller_row = mysql_cursor.fetchone()
                data['sellerName'] = seller_row[0]

                query = f"SELECT type FROM seller_selling_type WHERE seller_tag = {seller_tag};"
                mysql_cursor.execute(query)
                seller_type_rows = mysql_cursor.fetchall()
                seller_type_string = None
                for seller_type_row in seller_type_rows:
                    seller_type = int(seller_type_row[0])
                    if seller_type == 1:
                        if seller_type_string:
                            seller_type_string += ', 도매'
                        else:
                            seller_type_string = '도매'
                    if seller_type == 2:
                        if seller_type_string:
                            seller_type_string += ', 소매'
                        else:
                            seller_type_string = '소매'
                    if seller_type == 3:
                        if seller_type_string:
                            seller_type_string += ', 온라인'
                        else:
                            seller_type_string = '온라인'
                    if seller_type == 4:
                        if seller_type_string:
                            seller_type_string += ', 홈쇼핑'
                        else:
                            seller_type_string = '홈쇼핑'
                    if seller_type == 5:
                        if seller_type_string:
                            seller_type_string += ', 기타'
                        else:
                            seller_type_string = '기타'
                data['saleType'] = seller_type_string

                query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{data['tag']}';"
                mysql_cursor.execute(query)
                image_row = mysql_cursor.fetchone()
                if image_row:
                    data['imageUrl'] = image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
                else:
                    data['imageUrl'] = None

                goodsList.append(data)

            if condition_query:
                query = f"SELECT count(*) FROM goods, goods_sale" + condition_query + ';'
            else:
                query = f"SELECT count(*) FROM goods, goods_sale;"
            mysql_cursor.execute(query)
            count_row = mysql_cursor.fetchone()

            send_data['result'] = 'SUCCESS'
            send_data['list'] = goodsList
            send_data['totalPage'] = int(int(count_row[0])/int(limit)) + 1
            send_data['totalResult'] = int(count_row[0])

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#상품 판매 등록
@app.route('/<string:goodsTag>', methods=['POST'])
def registerSaleList(goodsTag):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'POST':
        try:
            request_body = json.loads(request.get_data())
            if not 'registerType' in request_body:
                send_data = {"result": "입력 방식이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'saleDate' in request_body:
                send_data = {"result": "판매일이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'cost' in request_body:
                send_data = {"result": "판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'commissionRate' in request_body:
                send_data = {"result": "수수료율이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'sellerTag' in request_body:
                send_data = {"result": "판매처 tag가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'customerName' in request_body:
                send_data = {"result": "고객명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'orderNumber' in request_body:
                send_data = {"result": "주문번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'invoiceNumber' in request_body:
                send_data = {"result": "송장번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'receiverName' in request_body:
                send_data = {"result": "받는 사람 이름이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'receiverPhoneNumber' in request_body:
                send_data = {"result": "받는 사람 연락처가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'receiverAddress' in request_body:
                send_data = {"result": "받는 사람 주소가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)


            register_type = request_body['registerType']
            sale_date = request_body['saleDate']
            cost = request_body['cost']
            commission_rate = request_body['commissionRate']
            seller_tag = request_body['sellerTag']
            customer = request_body['customerName']
            order_number = request_body['orderNumber']
            invoice_number = request_body['invoiceNumber']
            receiver_name = request_body['receiverName']
            receiver_phone_number = request_body['receiverPhoneNumber']
            receiver_address = request_body['receiverAddress']
            description = request_body['description']
            user_id = request_body['userId']

            
            query = f"INSERT INTO goods_sale (goods_tag, sale_date, cost, commission_rate, seller_tag, description, customer, order_number, invoice_number, receiver_name, receiver_phone_number, receiver_address, user_id, register_date, register_type) "
            query += f" VALUES ('{goodsTag}', '{sale_date}', {cost}, {commission_rate}, {seller_tag}, '{description}', '{customer}', '{order_number}', '{invoice_number}', '{receiver_name}', '{receiver_phone_number}', '{receiver_address}', '{user_id}', CURRENT_TIMESTAMP, {register_type});"
            mysql_cursor.execute(query)
                
            query = f"select MAX(goods_history_index) FROM goods_history WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)
            index_row = mysql_cursor.fetchone()
            if not index_row:
                index = 1
            elif not index_row[0]:
                index = 1 
            else:
                index = index_row[0] + 1

            query = f"INSERT INTO goods_history(goods_tag, goods_history_index, name, status, update_method, user_id, update_date) "
            query += f" VALUES ('{goodsTag}',{index},'판매처리',11,{register_type},'{user_id}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            query = f"UPDATE goods SET goods.status = 11, sale_date = '{sale_date}' WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)

            send_data['result'] = "SUCCESS"
            send_data['tag'] = goodsTag

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#판매 상품 반품
@app.route('/return/<string:goodsTag>', methods=['PUT'])
def returnSaleList(goodsTag):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'PUT':
        try:
            request_body = json.loads(request.get_data())
            if not 'registerType' in request_body:
                send_data = {"result": "입력 방식이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'reason' in request_body:
                send_data = {"result": "반품 이유가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            register_type = request_body['registerType']
            reason = request_body['reason']
            user_id = request_body['userId']

            query = f"UPDATE goods_sale SET return_flag = 1, return_reason = '{reason}' WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)
                
            query = f"select MAX(goods_history_index) FROM goods_history WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)
            index_row = mysql_cursor.fetchone()
            if not index_row:
                index = 1
            elif not index_row[0]:
                index = 1 
            else:
                index = index_row[0] + 1

            query = f"INSERT INTO goods_history(goods_tag, goods_history_index, name, status, update_method, user_id, update_date "
            query += f"VALUES ('{goodsTag}',{index},'반품처리',4,{register_type},'{user_id}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            query = f"UPDATE goods SET goods.status = 4, sale_date = NULL, return_date = CURRENT_TIMESTAMP WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)


def setup_api_server():

    global logWriter, db_config

    try:
        #config와 LogPath 불러오기
        config, status_code = load_config()
        if status_code != status.HTTP_200_OK:
            sys.exit(config)
        log_config = config['LOG']
        process_config = config['sale_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"sale_management.log"
        log_format = log_config['format']
        log_level = log_config['level']
        if log_level == 'CRITICAL':
            log_level = logging.CRITICAL
        elif log_level == 'ERROR':
            log_level = logging.ERROR
        elif log_level == 'WARNING':
            log_level = logging.WARNING
        elif log_level == 'INFO':
            log_level = logging.INFO
        elif log_level == 'DEBUG':
            log_level = logging.DEBUG
        else:
            log_level = logging.NOTSET

        logging.basicConfig(filename = log_filename,
                            filemode = "w",
                            format = log_format,
                            level = log_level)
        logWriter = logging.getLogger()

        #api 서버 시작
        server_ip = process_config['ip']
        server_port = process_config['port']

        app.run(host=server_ip, port=server_port)

    except Exception as e:
        sys.exit(f"Api setting failed...\n{e}")

if __name__ == '__main__':

    # api_gw로부터 메세지 수신을 위한 api server 동작
    setup_api_server()