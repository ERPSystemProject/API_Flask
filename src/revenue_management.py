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

#매출 리스트 조회
@app.route('/', methods=['GET'])
def revenueList():
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
            condition_query = " WHERE goods.status = 11 and goods.goods_tag = goods_sale.goods_tag"

            if not 'category' in params:
                send_data = {"result": "일별, 월별, 연별을 선택해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            category = int(params['category'])

            if category == 0:
                date_format = "'%Y-%m-%d'"
            elif category == 1:
                date_format = "'%Y-%m'"
            elif category == 2:
                date_format = "'%Y'"
            else:
                send_data = {"result": "일별, 월별, 연별을 선택이 잘못되었습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            if 'startDate' in params:
                startDate = params['startDate']
                if condition_query:
                    condition_query = condition_query + f" and goods_sale.sale_date >= '{startDate}'"
                else:
                    condition_query = f"WHERE goods_sale.sale_date >= '{startDate}'"
            if 'endDate' in params:
                endDate = params['endDate']
                if condition_query:
                    condition_query = condition_query + f" and goods_sale.sale_date <= '{endDate}'"
                else:
                   condition_query = f"WHERE goods_sale.sale_date <= '{endDate}'"

            if 'officeTagList' in params:
                officeTags = request.args.getlist('officeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or goods.office_tag = '{officeTag}'"
                    else:
                        office_query = f"goods.office_tag = '{officeTag}'"
                if office_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({office_query})"
                    else:
                        condition_query = f"WHERE ({office_query})"

            group_query = f" GROUP BY goods.office_tag, date ORDER BY date desc"
            query = f"SELECT (SELECT office_name FROM office WHERE office.office_tag = goods.office_tag), DATE_FORMAT(goods.sale_date,{date_format}) date, count(*), SUM(goods.first_cost), SUM(goods_sale.cost), SUM(goods_sale.cost*(goods_sale.commission_rate/100)) FROM goods, goods_sale " + condition_query + group_query + limit_query + ';'
            mysql_cursor.execute(query)
            rows = mysql_cursor.fetchall()
            print(query)

            send_data['table'] = dict()
            send_data['table']['column'] = ['번호','영업소명','날짜','판매총계','원가총계','매출통계','수수료합계','순매출통계','마진합계','마진율(매출)','마진율(원가)']
            send_data['table']['rows'] = list()

            for index, row in enumerate(rows):
                data = list()
                data.append(start+index+1)
                data.append(row[0])
                data.append(row[1])
                data.append(row[2])
                data.append(row[3])
                data.append(row[4])
                data.append(int(row[5]))
                origin = row[4]-int(row[5])
                data.append(origin)
                margin = origin - row[3]
                data.append(margin)
                saleMarginRate = float(margin)/float(row[4])*100
                firstMarginRate = float(margin)/float(row[3])*100
                data.append(saleMarginRate)
                data.append(firstMarginRate)
                send_data['table']['rows'].append(data)

            query = f"SELECT (SELECT office_name FROM office WHERE office.office_tag = goods.office_tag), DATE_FORMAT(goods.sale_date,{date_format}) date, count(*), SUM(goods.first_cost), SUM(goods_sale.cost), SUM(goods_sale.cost*(goods_sale.commission_rate/100)) FROM goods, goods_sale " + condition_query + group_query + ';'
            mysql_cursor.execute(query)
            total_rows = mysql_cursor.fetchall()

            send_data['result'] = 'SUCCESS'
            send_data['totalPage'] = int(len(total_rows)/int(limit)) + 1
            send_data['totalResult'] = len(total_rows)
            send_data['totalSold'] = 0
            send_data['totalFirstCost'] = 0
            send_data['totalSaleCost'] = 0
            send_data['totalCommissionCost'] = 0
            send_data['totalSettlementCost'] = 0
            send_data['totalSaleMarginRate'] = 0
            send_data['totalFirstCostMarginRate'] = 0
            if len(total_rows) > 0:
                for row in total_rows:
                    send_data['totalSold'] += row[2]
                    send_data['totalFirstCost'] += row[3]
                    send_data['totalSaleCost'] += row[4]
                    send_data['totalCommissionCost'] += int(row[5])
                send_data['totalSettlementCost'] = send_data['totalSaleCost'] - send_data['totalCommissionCost']
                margin = send_data['totalSettlementCost'] - send_data['totalFirstCost']
                send_data['totalSaleMarginRate'] = float(margin)/float(send_data['totalSaleCost'])*100
                send_data['totalFirstCostMarginRate'] =float(margin)/float(send_data['totalFirstCost'])*100

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code) 

#판매 상품 리스트 조회
@app.route('/goods', methods=['GET'])
def revenueGoodsList():
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
                if dateType < 0 or dateType > 2:
                    send_data = {"result": "날짜 검색 구분이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if dateType == 0:
                    dateString = 'stocking_date'
                elif dateType == 1:
                    dateString = 'import_date'
                else:
                    dateString = 'goods_sale.sale_date'
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

            if 'sexList' in params:
                sexList = request.args.getlist('sexList')
                sex_query = None
                for sex in sexList:
                    if sex < 0 or sex > 2:
                        send_data = {"result": "성별 구분이 올바르지 않습니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if sex_query:
                        sex_query = sex_query + f" or sex = {sex}"
                    else:
                        sex_query = f"sex = {sex}"
                if sex_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({sex_query})"
                    else:
                        condition_query = f"WHERE ({sex_query})"

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
                        condition_query = condition_query + f" and goods.goods_tag IN (SELECT goods_tag FROM goods_sale WHERE seller_tag IN (SELECT seller_tag FROM seller_selling_type WHERE {seller_query}))"
                    else:
                        condition_query = f"WHERE goods.goods_tag IN (SELECT goods_tag FROM goods_sale WHERE seller_tag IN (SELECT seller_tag FROM seller_selling_type WHERE {seller_query}))"

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
                        condition_query = condition_query + f" and goods.goods_tag IN (SELECT goods_tag FROM goods_sale WHERE {seller_query})"
                    else:
                        condition_query = f"WHERE goods.goods_tag IN (SELECT goods_tag FROM goods_sale WHERE {seller_query})"

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
                condition_query = condition_query + ' ORDER BY goods_sale.sale_date DESC'
                query = f"SELECT goods_sale.sale_date, (SELECT office_name FROM office WHERE goods.office_tag = office.office_tag) as office, stocking_date, import_date, (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_type, (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_name, bl_number, season, "
                query += f"(SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, (SELECT category_name FROM category WHERE goods.category_tag = category.category_tag) as category, part_number, goods.goods_tag, sex, color, material, "
                query += f"size, origin_name, goods.cost, first_cost, regular_cost, sale_cost, discount_cost, goods_sale.cost, goods_sale.commission_rate, goods_sale.seller_tag, goods_sale.order_number, goods_sale.invoice_number, goods_sale.receiver_name, goods_sale.receiver_phone_number, "
                query += f"goods_sale.receiver_address, goods_sale.description, goods_sale.customer, (SELECT user.name FROM user WHERE goods_sale.user_id = user.user_id) as registerName, register_type, TIMESTAMPDIFF(DAY, goods.stocking_date, goods.sale_date) FROM goods, goods_sale " + condition_query + limit_query
            else:
                condition_query = ' ORDER BY goods_sale.sale_date DESC'
                query = f"SELECT goods_sale.sale_date, (SELECT office_name FROM office WHERE goods.office_tag = office.office_tag) as office, stocking_date, import_date, (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_type, (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_name, bl_number, season, "
                query += f"(SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, (SELECT category_name FROM category WHERE goods.category_tag = category.category_tag) as category, part_number, goods.goods_tag, sex, color, material, "
                query += f"size, origin_name, goods.cost, first_cost, regular_cost, sale_cost, discount_cost, goods_sale.cost, goods_sale.commission_rate, goods_sale.seller_tag, goods_sale.order_number, goods_sale.invoice_number, goods_sale.receiver_name, goods_sale.receiver_phone_number, "
                query += f"goods_sale.receiver_address, goods_sale.description, goods_sale.customer, (SELECT user.name FROM user WHERE goods_sale.user_id = user.user_id) as registerName, register_type, TIMESTAMPDIFF(DAY, goods.stocking_date, goods.sale_date) FROM goods, goods_sale " + condition_query + limit_query
            mysql_cursor.execute(query)
            goods_rows = mysql_cursor.fetchall()

            send_data['table'] = dict()
            send_data['table']['column'] = ['검색 번호','판매일','입고일','입력방식','판매유형','판매처','상품상태','영업처','시즌','이미지','브랜드','상품종류','품번','Tag_no','공급처유형','공급처','성별','색상','소재','사이즈', '원산지', 'COST', '원가', '정상판매가', '실제판매가', '판매가','특별할인가', '할인금액', '할인률', '수수료', '수수료율', '정산액', '마진', '마진율(매출)', '마진율(원가)', '판매처리자', '메모', '재고일수']
            send_data['table']['rows'] = list()

            for index, goods_row in enumerate(goods_rows):
                data = list()
                data.append(start+index+1)
                data.append(goods_row[0])
                data.append(goods_row[2])
                register_type = int(goods_row[33])
                if register_type == 1:
                    data.append('엑셀입력')
                elif register_type == 2:
                    data.append('일괄입력')
                else:
                    data.append('직접입력')

                seller_tag = goods_row[24]
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
                data.append(seller_type_string)

                query = f"SELECT seller_name FROM seller WHERE seller_tag = {seller_tag};"
                mysql_cursor.execute(query)
                seller_row = mysql_cursor.fetchone()
                data.append(seller_row[0])

                data.append('판매완료')
                data.append(goods_row[1])
                data.append(goods_row[7])

                goodsTag = goods_row[11]

                query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{goodsTag}';"
                mysql_cursor.execute(query)
                image_row = mysql_cursor.fetchone()
                if image_row:
                    data.append(image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/'))
                else:
                    data.append(None)

                data.append(goods_row[8])
                data.append(goods_row[9])
                data.append(goods_row[10])
                data.append(goodsTag)
                data.append(goods_row[4])
                data.append(goods_row[5])

                sex = goods_row[12]
                if sex == 0:
                    data.append('공용')
                elif sex == 1:
                    data.append('남성')
                else:
                    data.append('여성')

                data.append(goods_row[13])
                data.append(goods_row[14])
                data.append(goods_row[15])
                data.append(goods_row[16])
                data.append(goods_row[17])
                
                firstCost = goods_row[18]
                regularCost = goods_row[19]
                saleCost = goods_row[20]
                discountCost = goods_row[21]
                realSaleCost = goods_row[22]
                commissionRate = goods_row[23]
                commissionCost = int(realSaleCost*(commissionRate/100)/100)
                settlementCost = realSaleCost-commissionCost
                marginCost = settlementCost - firstCost
                saleMarginRate = float(marginCost)/float(realSaleCost)*100
                firstCostMarginRate = float(marginCost)/float(firstCost)*100

                data.append(firstCost)
                data.append(regularCost)
                data.append(realSaleCost)
                data.append(saleCost)
                data.append(discountCost)
                data.append(regularCost-realSaleCost)
                data.append(float(float(regularCost-realSaleCost)/float(regularCost))*100)
                data.append(commissionCost)
                data.append(commissionRate)
                data.append(settlementCost)
                data.append(marginCost)
                data.append(saleMarginRate)
                data.append(firstCostMarginRate)
                data.append(goods_row[32])
                data.append(goods_row[30])
                data.append(goods_row[34])

                send_data['table']['rows'].append(data)

            if condition_query:
                query = f"SELECT count(*) FROM goods, goods_sale" + condition_query + ';'
            else:
                query = f"SELECT count(*) FROM goods, goods_sale;"
            mysql_cursor.execute(query)
            count_row = mysql_cursor.fetchone()

            send_data['result'] = 'SUCCESS'
            send_data['totalPage'] = int(int(count_row[0])/int(limit)) + 1
            send_data['totalResult'] = int(count_row[0])

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#매출 리스트 조회
@app.route('/statistics', methods=['GET'])
def revenueStatisticsList():
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
            condition_query = " WHERE goods.status = 11 and goods.goods_tag = goods_sale.goods_tag"

            if not 'category' in params:
                send_data = {"result": "일별, 월별, 연별을 선택해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            category = int(params['category'])

            if category == 0:
                date_format = "'%Y-%m-%d'"
            elif category == 1:
                date_format = "'%Y-%m'"
            elif category == 2:
                date_format = "'%Y'"
            else:
                send_data = {"result": "일별, 월별, 연별을 선택이 잘못되었습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            if 'startDate' in params:
                startDate = params['startDate']
                if condition_query:
                    condition_query = condition_query + f" and goods.sale_date >= '{startDate}'"
                else:
                    condition_query = f"WHERE goods.sale_date >= '{startDate}'"
            if 'endDate' in params:
                endDate = params['endDate']
                if condition_query:
                    condition_query = condition_query + f" and goods.sale_date <= '{endDate}'"
                else:
                   condition_query = f"WHERE goods.sale_date <= '{endDate}'"

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
                        condition_query = condition_query + f" and goods.goods_tag IN (SELECT goods_sale.goods_tag FROM goods_sale WHERE seller_tag IN (SELECT seller_tag FROM seller_selling_type WHERE {seller_query}))"
                    else:
                        condition_query = f"WHERE goods.goods_tag IN (SELECT goods_sale.goods_tag FROM goods_sale WHERE seller_tag IN (SELECT seller_tag FROM seller_selling_type WHERE {seller_query}))"

            group_query = f" GROUP BY date ORDER BY date desc"
            query = f"SELECT DATE_FORMAT(goods.sale_date,{date_format}) date, count(*), SUM(goods.first_cost), SUM(goods_sale.cost), SUM(goods_sale.cost*(goods_sale.commission_rate/100)) FROM goods, goods_sale " + condition_query + group_query + limit_query + ';'
            mysql_cursor.execute(query)
            rows = mysql_cursor.fetchall()

            send_data['table'] = dict()
            send_data['table']['column'] = ['번호','날짜','판매총계','원가총계','매출통계','수수료합계','순매출통계','마진합계','마진율(매출)','마진율(원가)']
            send_data['table']['rows'] = list()

            for index, row in enumerate(rows):
                data = list()
                data.append(start+index+1)
                data.append(row[0])
                data.append(row[1])
                data.append(row[2])
                data.append(row[3])
                data.append(int(row[4]))
                origin = row[3]-int(row[4])
                data.append(origin)
                margin = origin - row[2]
                data.append(margin)
                saleMarginRate = float(margin)/float(row[3])*100
                firstMarginRate = float(margin)/float(row[2])*100
                data.append(saleMarginRate)
                data.append(firstMarginRate)
                send_data['table']['rows'].append(data)

            query = f"SELECT DATE_FORMAT(goods.sale_date,{date_format}) date, count(*), SUM(goods.first_cost), SUM(goods_sale.cost), SUM(goods_sale.cost*(goods_sale.commission_rate/100)) FROM goods, goods_sale " + condition_query + group_query + ';'
            mysql_cursor.execute(query)
            total_rows = mysql_cursor.fetchall()

            send_data['result'] = 'SUCCESS'
            send_data['totalPage'] = int(len(total_rows)/int(limit)) + 1
            send_data['totalResult'] = len(total_rows)
            send_data['totalSold'] = 0
            send_data['totalFirstCost'] = 0
            send_data['totalSaleCost'] = 0
            send_data['totalCommissionCost'] = 0
            send_data['totalSettlementCost'] = 0
            send_data['totalSaleMarginRate'] = 0
            send_data['totalFirstCostMarginRate'] = 0
            if len(total_rows) > 0:
                for row in total_rows:
                    send_data['totalSold'] += row[1]
                    send_data['totalFirstCost'] += row[2]
                    send_data['totalSaleCost'] += row[3]
                    send_data['totalCommissionCost'] += int(row[4])
                send_data['totalSettlementCost'] = send_data['totalSaleCost'] - send_data['totalCommissionCost']
                margin = send_data['totalSettlementCost'] - send_data['totalFirstCost']
                send_data['totalSaleMarginRate'] = float(margin)/float(send_data['totalSaleCost'])*100
                send_data['totalFirstCostMarginRate'] =float(margin)/float(send_data['totalFirstCost'])*100

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
        process_config = config['revenue_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"revenue_management.log"
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