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
    
#상품 리스트 조회
@app.route('/', methods=['GET'])
def getGoodsList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

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
        condition_query = " WHERE goods.status != 11"

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
                dateString = 'register_date'
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
                    office_query = office_query + f" or office_tag = {officeTag}"
                else:
                    office_query = f"office_tag = {officeTag}"
            if office_query:
                if condition_query:
                    condition_query = condition_query + f" and ({office_query})"
                else:
                    condition_query = f"WHERE ({office_query})"

        if 'statusList' in params:
            statuses = request.args.getlist('statusList')
            status_query = None
            for goods_status in statuses:
                if status_query:
                    status_query = status_query + f" or status = {goods_status}"
                else:
                    status_query = f"status = {goods_status}"
            if status_query:
                if condition_query:
                    condition_query = condition_query + f" and ({status_query})"
                else:
                    condition_query = f"WHERE ({status_query})"

        if 'seasonList' in params:
            seasons = request.args.getlist('seasonList')
            season_query = None
            for season in seasons:
                if season_query:
                    season_query = season_query + f" or season = '{season}'"
                else:
                    season_query = f"season = '{season}'"
            if season_query:
                if condition_query:
                    condition_query = condition_query + f" and ({season_query})"
                else:
                    condition_query = f"WHERE ({season_query})"
        
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
            query = f"SELECT goods_tag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, goods.status, first_cost, TIMESTAMPDIFF(DAY, stocking_date, CURRENT_TIMESTAMP) FROM goods" + condition_query + limit_query + ';'
        else:
            query = f"SELECT goods_tag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, goods.status, first_cost, TIMESTAMPDIFF(DAY, stocking_date, CURRENT_TIMESTAMP) FROM goods" + limit_query + ';'
        print(query)
        mysql_cursor.execute(query)
        goods_rows = mysql_cursor.fetchall()

        goodsList = list()
        for goods_row in goods_rows:
            data = dict()
            data['tag'] = goods_row[0]
            data['partNumber'] = goods_row[1]
            data['blNumber'] = goods_row[2]
            data['origin'] = goods_row[3]
            brand_tag = goods_row[4]
            category_tag = goods_row[5]
            office_tag = goods_row[6]
            supplier_tag = goods_row[7]
            data['color'] = goods_row[8]
            data['season'] = goods_row[9]
            sex = int(goods_row[10])
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
            goods_status = int(goods_row[21])
            data['firstCost'] = goods_row[22]
            data['inventoryDays'] = goods_row[23]

            if sex == 0:
                data['sex'] = '공용'
            elif sex == 1:
                data['sex'] = '남성'
            else:
                data['sex'] = '여성'

            query = f"SELECT brand_name FROM brand WHERE brand_tag = '{brand_tag}';"
            mysql_cursor.execute(query)
            brand_row = mysql_cursor.fetchone()
            data['brand'] = brand_row[0]

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

            if goods_status == 1:
                data['status'] = '스크래치'
            elif goods_status == 2:
                data['status'] = '판매불가'
            elif goods_status == 3:
                data['status'] = '폐기'
            elif goods_status == 4:
                data['status'] = '정상재고'
            elif goods_status == 5:
                data['status'] = '분실'
            elif goods_status == 6:
                data['status'] = '정산대기'
            elif goods_status == 7:
                data['status'] = '분배대기'
            elif goods_status == 8:
                data['status'] = '회수완료'
            elif goods_status == 9:
                data['status'] = '수선중'
            elif goods_status == 10:
                data['status'] = '반품정산대기'
            elif goods_status == 11:
                data['status'] = '판매완료'
            elif goods_status == 12:
                data['status'] = '출고승인대기'
            else:
                data['status'] = '고객반송대기'

            query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{data['tag']}';"
            mysql_cursor.execute(query)
            image_row = mysql_cursor.fetchone()
            if image_row:
                data['imageUrl'] = image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
            else:
                data['imageUrl'] = None
            goodsList.append(data)

        if condition_query:
            query = f"SELECT count(*) FROM goods" + condition_query + ';'
        else:
            query = f"SELECT count(*) FROM goods;"
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

#품번 재고 현황 조회
@app.route('/partNumber', methods=['GET'])
def getPartNumberInventoryList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

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
        condition_query = None

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
                dateString = 'register_date'
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
                    office_query = office_query + f" or office_tag = {officeTag}"
                else:
                    office_query = f"office_tag = {officeTag}"
            if office_query:
                if condition_query:
                    condition_query = condition_query + f" and ({office_query})"
                else:
                    condition_query = f"WHERE ({office_query})"

        if 'statusList' in params:
            statuses = request.args.getlist('statusList')
            status_query = None
            for goods_status in statuses:
                if status_query:
                    status_query = status_query + f" or status = {goods_status}"
                else:
                    status_query = f"status = {goods_status}"
            if status_query:
                if condition_query:
                    condition_query = condition_query + f" and ({status_query})"
                else:
                    condition_query = f"WHERE ({status_query})"


        if 'seasonList' in params:
            seasons = request.args.getlist('seasonList')
            season_query = None
            for season in seasons:
                if season_query:
                    season_query = season_query + f" or season = '{season}'"
                else:
                    season_query = f"season = '{season}'"
            if season_query:
                if condition_query:
                    condition_query = condition_query + f" and ({season_query})"
                else:
                    condition_query = f"WHERE ({season_query})"
        
        soldOutFlag = True
        if 'soldOutFlag' in params:
            if int(params['soldOutFlag']) == 1:
                soldOutFlag = False

        if soldOutFlag:
            if condition_query:
                condition_query = condition_query + f" and goods.status != 11"
            else:
                condition_query = f"WHERE goods.status != 11"
        
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
            goods_condition_query = condition_query + f" GROUP BY part_number, supplier_tag, stocking_date "
            query = f"SELECT (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), supplier_tag, part_number, stocking_date, any_value(brand_tag), any_value(category_tag), any_value(season), any_value(sex), any_value(color), any_value(material), any_value(origin_name), count(case when goods.status != 11 then 1 end) as inventoryCount, count(*), AVG(cost), AVG(first_cost), AVG(regular_cost), AVG(sale_cost), AVG(discount_cost), AVG(management_cost) FROM goods " + goods_condition_query + limit_query + ';'
        else:
            goods_condition_query = f" GROUP BY part_number, supplier_tag, stocking_date "
            query = f"SELECT (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), supplier_tag, part_number, stocking_date, any_value(brand_tag), any_value(category_tag), any_value(season), any_value(sex), any_value(color), any_value(material), any_value(origin_name), count(case when goods.status != 11 then 1 end) as inventoryCount, count(*), AVG(cost), AVG(first_cost), AVG(regular_cost), AVG(sale_cost), AVG(discount_cost), AVG(management_cost) FROM goods " + goods_condition_query + limit_query + ';'
        mysql_cursor.execute(query)
        goods_rows = mysql_cursor.fetchall()

        goodsList = list()
        for goods_row in goods_rows:
            data = dict()
            supplier_type = int(goods_row[0])
            data['supplierName'] = goods_row[1]
            data['supplierTag'] = goods_row[2]
            data['partNumber'] = goods_row[3]
            data['stockingDate'] = goods_row[4]
            brand_tag = goods_row[5]
            category_tag = goods_row[6]
            data['season'] = goods_row[7]
            sex = int(goods_row[8])
            data['color'] = goods_row[9]
            data['material'] = goods_row[10]
            data['origin'] = goods_row[11]
            data['inventoryCount'] = goods_row[12]
            data['stockingCount'] = goods_row[13]
            data['cost'] = goods_row[14]
            data['firstCost'] = goods_row[15]
            data['regularCost'] = goods_row[16]
            data['saleCost'] = goods_row[17]
            data['discountCost'] = goods_row[18]
            data['managementCost'] = goods_row[19]

            if sex == 0:
                data['sex'] = '공용'
            elif sex == 1:
                data['sex'] = '남성'
            else:
                data['sex'] = '여성'

            query = f"SELECT brand_name FROM brand WHERE brand_tag = '{brand_tag}';"
            mysql_cursor.execute(query)
            brand_row = mysql_cursor.fetchone()
            data['brand'] = brand_row[0]

            query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
            mysql_cursor.execute(query)
            category_row = mysql_cursor.fetchone()
            data['category'] = category_row[0]

            #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
            if supplier_type == 1:
                data['supplierType'] = '위탁'
            elif supplier_type == 2:
                data['supplierType'] = '사입'
            elif supplier_type == 3:
                data['supplierType'] = '직수입'
            elif supplier_type == 4:
                data['supplierType'] = '미입고'

            if condition_query:
                check_condition = condition_query + f" and supplier_tag = {data['supplierTag']} and part_number = '{data['partNumber']}' and goods.status != 11;"
            else:
                check_condition = f" WHERE supplier_tag = {data['supplierTag']} and part_number = '{data['partNumber']}' and goods.status != 11;"
            query = f"SELECT goods_tag, (SELECT office_name FROM office WHERE office.office_tag = goods.office_tag) as officeName FROM goods " + check_condition
            print(query)
            mysql_cursor.execute(query)
            office_rows = mysql_cursor.fetchall()
            office_dict = dict()

            for office_row in office_rows:
                goods_tag = office_row[0]
                office_name = office_row[1]
                if not 'imageUrl' in data:
                    query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{goods_tag}';"
                    mysql_cursor.execute(query)
                    image_row = mysql_cursor.fetchone()
                    if image_row:
                        data['imageUrl'] = image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
                    else:
                        data['imageUrl'] = None

                if office_name in office_dict:
                    office_dict[office_name] += 1
                else:
                    office_dict[office_name] = 1
            
            data['officeAndInventoryCount'] = None
            for key in office_dict.keys():
                if data['officeAndInventoryCount']:
                    data['officeAndInventoryCount'] = f"{key}\t/ {office_dict[key]}\n" + data['officeAndInventoryCount']
                else:
                    data['officeAndInventoryCount'] = f"{key}\t/ {office_dict[key]}"

            goodsList.append(data)

        if condition_query:
            condition_query += " GROUP BY part_number, supplier_tag, stocking_date "
            query = f"SELECT count(case when goods.status != 11 then 1 end) as inventoryCount, count(*), SUM(cost), SUM(first_cost), SUM(regular_cost), SUM(sale_cost), SUM(discount_cost), SUM(management_cost) FROM goods " + condition_query + ';'
        else:
            condition_query = " GROUP BY part_number, supplier_tag, stocking_date"
            query = f"SELECT count(case when goods.status != 11 then 1 end) as inventoryCount, count(*), SUM(cost), SUM(first_cost), SUM(regular_cost), SUM(sale_cost), SUM(discount_cost), SUM(management_cost) FROM goods " + condition_query + ';'
        print(query)
        mysql_cursor.execute(query)
        count_rows = mysql_cursor.fetchall()

        send_data['totalResult'] = len(count_rows)
        send_data['result'] = 'SUCCESS'
        send_data['list'] = goodsList
        send_data['totalPage'] = int(len(count_rows)/int(limit)) + 1

        send_data['totalStockingCount'] = 0
        send_data['totalInventoryCount'] = 0
        send_data['totalCost'] = 0
        send_data['totalFirstCost'] = 0
        send_data['totalRegularCost'] = 0
        send_data['totalSaleCost'] = 0
        send_data['totalDiscountCost'] = 0
        send_data['totalManagementCost'] = 0

        for count_row in count_rows:
            send_data['totalInventoryCount'] += int(count_row[0])
            send_data['totalStockingCount'] += int(count_row[1])
            send_data['totalCost'] += int(count_row[2])
            send_data['totalFirstCost'] += int(count_row[3])
            send_data['totalRegularCost'] += int(count_row[4])
            send_data['totalSaleCost'] += int(count_row[5])
            send_data['totalDiscountCost'] += int(count_row[6])
            send_data['totalManagementCost'] += int(count_row[7])

    except Exception as e:
        send_data = {"result": f"Error : {traceback.format_exc()}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#품번 재고 상세 현황 조회
@app.route('/partNumber/<string:partNumber>', methods=['GET'])
def getDetailPartNumberInventoryList(partNumber):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()
        if not 'stockingDate' in params:
            send_data = {"result": "입고일을 지정하지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'supplierTag' in params:
            send_data = {"result": "공급처를 지정하지 않았습니다"}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)

        stocking_date = params['stockingDate']
        supplier_tag = params['supplierTag']

        
        query = f"SELECT goods_tag, import_date, (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), bl_number, season, (SELECT brand_name FROM brand WHERE brand.brand_tag = goods.brand_tag), (SELECT category_name FROM category WHERE category.category_tag = goods.category_tag), sex, color, material, size, origin_name, sale_date, (SELECT office_name FROM office WHERE office.office_tag = goods.office_tag), goods.status, cost, first_cost, regular_cost, sale_cost, discount_cost, management_cost FROM goods WHERE stocking_date = '{stocking_date}' and supplier_tag = {supplier_tag} and part_number = '{partNumber}' and goods.status != 11;"
        mysql_cursor.execute(query)
        goods_rows = mysql_cursor.fetchall()

        goodsList = list()

        send_data['result'] = "SUCCESS"
        send_data['partNumber'] = partNumber
        send_data['stockingDate'] = stocking_date
        send_data['supplierName'] = None
        send_data['firstCost'] = 0
        send_data['totalInventoryCount'] = len(goods_rows)
        send_data['brand'] = None
        send_data['category'] = None

        for goods_row in goods_rows:
            data = dict()
            data['tag'] = goods_row[0]
            data['stockingDate'] = stocking_date
            data['importDate'] = goods_row[1]
            supplier_type = goods_row[2]
            data['supplierName'] = goods_row[3]
            data['blNumber'] = goods_row[4]
            data['season'] = goods_row[5]
            data['brand'] = goods_row[6]
            data['category'] = goods_row[7]
            data['partNumber'] = partNumber
            sex = goods_row[8]
            data['color'] = goods_row[9]
            data['material'] = goods_row[10]
            data['size'] = goods_row[11]
            data['origin'] = goods_row[12]
            data['saleDate'] = goods_row[13]
            data['office'] = goods_row[14]
            goods_status = goods_row[15]
            data['cost'] = goods_row[16]
            data['firstCost'] = goods_row[17]
            data['regularCost'] = goods_row[18]
            data['saleCost'] = goods_row[19]
            data['discountCost'] = goods_row[20]
            data['managementCost'] = goods_row[21]

            if not send_data['supplierName']:
                send_data['supplierName'] = data['supplierName']
            
            if not send_data['brand']:
                send_data['brand'] = data['brand']
            
            if not send_data['category']:
                send_data['category'] = data['category']

            send_data['firstCost'] += int(data['firstCost'])

            #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
            if supplier_type == 1:
                data['supplierType'] = '위탁'
            elif supplier_type == 2:
                data['supplierType'] = '사입'
            elif supplier_type == 3:
                data['supplierType'] = '직수입'
            elif supplier_type == 4:
                data['supplierType'] = '미입고'

            if sex == 0:
                data['sex'] = '공용'
            elif sex == 1:
                data['sex'] = '남성'
            else:
                data['sex'] = '여성'

            if goods_status == 1:
                data['status'] = '스크래치'
            elif goods_status == 2:
                data['status'] = '판매불가'
            elif goods_status == 3:
                data['status'] = '폐기'
            elif goods_status == 4:
                data['status'] = '정상재고'
            elif goods_status == 5:
                data['status'] = '분실'
            elif goods_status == 6:
                data['status'] = '정산대기'
            elif goods_status == 7:
                data['status'] = '분배대기'
            elif goods_status == 8:
                data['status'] = '회수완료'
            elif goods_status == 9:
                data['status'] = '수선중'
            elif goods_status == 10:
                data['status'] = '반품정산대기'
            elif goods_status == 11:
                data['status'] = '판매완료'
            elif goods_status == 12:
                data['status'] = '출고승인대기'
            else:
                data['status'] = '고객반송대기'

            query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{data['tag']}';"
            mysql_cursor.execute(query)
            image_row = mysql_cursor.fetchone()
            if image_row:
                data['imageUrl'] = image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
            else:
                data['imageUrl'] = None
            goodsList.append(data)
        
        query = f"SELECT goods_tag, import_date, (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), bl_number, season, (SELECT brand_name FROM brand WHERE brand.brand_tag = goods.brand_tag), (SELECT category_name FROM category WHERE category.category_tag = goods.category_tag), sex, color, material, size, origin_name, sale_date, (SELECT office_name FROM office WHERE office.office_tag = goods.office_tag), goods.status, cost, first_cost, regular_cost, sale_cost, discount_cost, management_cost FROM goods WHERE stocking_date = '{stocking_date}' and supplier_tag = {supplier_tag} and part_number = '{partNumber}';"
        mysql_cursor.execute(query)
        count_rows = mysql_cursor.fetchall()

        send_data['totalStockingCount'] = len(count_rows)
        send_data['firstCost'] = int(send_data['firstCost'] / send_data['totalInventoryCount'])
        send_data['list'] = goodsList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#브랜드 재고 현황 조회
@app.route('/brand', methods=['GET'])
def getBrandInventoryList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

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
        condition_query = " WHERE goods.goods_tag = goods_history.goods_tag"

        if 'date' in params:
            search_date = "'" + params['date'] + "'"
        else:
            search_date = "CURRENT_TIMESTAMP"

        if 'brandTagList' in params:
            brandTags = request.args.getlist('brandTagList')
            brand_query = None
            for brandTag in brandTags:
                if brand_query:
                    brand_query = brand_query + f" or goods.brand_tag = '{brandTag}'"
                else:
                    brand_query = f"goods.brand_tag = '{brandTag}'"
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
                    category_query = category_query + f" or goods.category_tag = '{categoryTag}'"
                else:
                    category_query = f"goods.category_tag = '{categoryTag}'"
            if category_query:
                if condition_query:
                    condition_query = condition_query + f" and ({category_query})"
                else:
                    condition_query = f"WHERE ({category_query})"

        if 'officeTagList' in params:
            officeTags = request.args.getlist('officeTagList')
            office_query = None
            for officeTag in officeTags:
                if office_query:
                    office_query = office_query + f" or goods.office_tag = {officeTag}"
                else:
                    office_query = f"goods.office_tag = {officeTag}"
            if office_query:
                if condition_query:
                    condition_query = condition_query + f" and ({office_query})"
                else:
                    condition_query = f"WHERE ({office_query})"

        condition_query += " GROUP BY goods.brand_tag, goods.category_tag, goods.office_tag ORDER BY goods.brand_tag "
        query = f"SELECT goods.brand_tag, goods.category_tag, goods.office_tag, count(case when goods.goods_tag = goods_history.goods_tag and goods_history.status != 11 and goods_history_index IN (SELECT MAX(goods_history_index) FROM goods_history WHERE goods.goods_tag = goods_history.goods_tag and update_date < {search_date}) then 1 end) as inventoryCount, SUM(goods.cost), SUM(goods.first_cost), SUM(goods.regular_cost), SUM(goods.sale_cost), SUM(goods.discount_cost), SUM(management_cost) FROM goods, goods_history " + condition_query + limit_query + ';'
        mysql_cursor.execute(query)
        inventory_rows = mysql_cursor.fetchall()

        inventoryList = list()
        
        for index, inventory_row in enumerate(inventory_rows):
            data = dict()
            data['index'] = start + index
            data['brandTag'] = inventory_row[0]
            data['categoryTag'] = inventory_row[1]
            data['officeTag'] = inventory_row[2]
            data['inventoryCount'] = inventory_row[3]
            data['totalCost'] = inventory_row[4]
            data['totalFirstCost'] = inventory_row[5]
            data['totalRegularCost'] = inventory_row[6]
            data['totalSaleCost'] = inventory_row[7]
            data['totalDiscountCost'] = inventory_row[8]
            data['totalManagementCost'] = inventory_row[9]

            query = f"SELECT brand_name FROM brand WHERE brand_tag = '{data['brandTag']}';"
            mysql_cursor.execute(query)
            brand_row = mysql_cursor.fetchone()
            data['brand'] = brand_row[0]

            query = f"SELECT category_name FROM category WHERE category_tag = '{data['categoryTag']}';"
            mysql_cursor.execute(query)
            category_row = mysql_cursor.fetchone()
            data['category'] = category_row[0]

            query = f"SELECT office_name FROM office WHERE office_tag = {data['officeTag']};"
            mysql_cursor.execute(query)
            office_row = mysql_cursor.fetchone()
            data['office'] = office_row[0]

            inventoryList.append(data)

        query = f"SELECT goods.brand_tag, goods.category_tag, goods.office_tag, count(case when goods.goods_tag = goods_history.goods_tag and goods_history.status != 11 and goods_history_index IN (SELECT MAX(goods_history_index) FROM goods_history WHERE goods.goods_tag = goods_history.goods_tag and update_date < {search_date}) then 1 end) as inventoryCount, SUM(goods.cost), SUM(goods.first_cost), SUM(goods.regular_cost), SUM(goods.sale_cost), SUM(goods.discount_cost), SUM(management_cost) FROM goods, goods_history " + condition_query + ';'
        mysql_cursor.execute(query)
        count_rows = mysql_cursor.fetchall()
        send_data['result'] = "SUCCESS"
        send_data['list'] = inventoryList
        send_data['totalResult'] = len(count_rows)
        send_data['totalPage'] = int(len(count_rows)/int(limit)) + 1

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#브랜드 재고 상세 현황 조회
@app.route('/brand/<string:brandTag>', methods=['GET'])
def getDetailBrandInventoryList(brandTag):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()
        if not 'categoryTag' in params:
            send_data = {"result": "상품종류를 지정하지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'officeTag' in params:
            send_data = {"result": "영업소를 지정하지 않았습니다"}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)

        category_tag = params['categoryTag']
        office_tag = params['officeTag']

        if 'date' in params:
            search_date = f"'{params['date']}'"
            send_data['date'] = params['date']
        else:
            search_date = "CURRENT_TIMESTAMP"
            send_data['date'] = None
        
        query = f"SELECT goods_tag, stocking_date, import_date, (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), bl_number, season, (SELECT brand_name FROM brand WHERE brand.brand_tag = goods.brand_tag), (SELECT category_name FROM category WHERE category.category_tag = goods.category_tag), part_number, sex, color, material, size, origin_name, sale_date, (SELECT office_name FROM office WHERE office.office_tag = goods.office_tag), cost, first_cost, regular_cost, sale_cost, discount_cost, management_cost FROM goods WHERE goods.brand_tag = '{brandTag}' and goods.category_tag = '{category_tag}' and goods.office_tag = {office_tag};"
        mysql_cursor.execute(query)
        goods_rows = mysql_cursor.fetchall()

        goodsList = list()

        send_data['result'] = "SUCCESS"
        send_data['totalCost'] = 0
        send_data['totalFirstCost'] = 0
        send_data['totalRegularCost'] = 0
        send_data['totalSaleCost'] = 0
        send_data['totalDiscountCost'] = 0
        send_data['totalManagementCost'] = 0
        send_data['totalStockingCount'] = len(goods_rows)
        send_data['totalInventoryCount'] = 0
        send_data['brand'] = None
        send_data['category'] = None
        send_data['office'] = None

        for goods_row in goods_rows:
            data = dict()
            data['tag'] = goods_row[0]

            query = f"SELECT goods_history.status FROM goods_history WHERE goods_tag = '{data['tag']}' and goods_history IN (SELECT MAX(goods_history_index) FROM goods_history WHERE goods_tag = '{data['tag']}' and update_date < {search_date});"
            mysql_cursor.execute(query)
            status_row = mysql_cursor.fetchone()
            goods_status = int(status_row[0])

            if goods_status == 11:
                continue

            data['stockingDate'] = goods_row[1]
            data['importDate'] = goods_row[2]
            supplier_type = goods_row[3]
            data['supplierName'] = goods_row[4]
            data['blNumber'] = goods_row[5]
            data['season'] = goods_row[6]
            data['brand'] = goods_row[7]
            data['category'] = goods_row[8]
            data['partNumber'] = goods_row[9]
            sex = goods_row[10]
            data['color'] = goods_row[11]
            data['material'] = goods_row[12]
            data['size'] = goods_row[13]
            data['origin'] = goods_row[14]
            data['saleDate'] = goods_row[15]
            data['office'] = goods_row[16]
            data['cost'] = goods_row[17]
            data['firstCost'] = goods_row[18]
            data['regularCost'] = goods_row[19]
            data['saleCost'] = goods_row[20]
            data['discountCost'] = goods_row[21]
            data['managementCost'] = goods_row[22]

            if not send_data['brand']:
                send_data['brand'] = data['brand']
            if not send_data['category']:
                send_data['category'] = data['category']
            if not send_data['office']:
                send_data['office'] = data['office']

            send_data['totalCost'] += data['cost']
            send_data['totalFirstCost'] += data['firstCost']
            send_data['totalRegularCost'] += data['regularCost']
            send_data['totalSaleCost'] += data['saleCost']
            send_data['totalDiscountCost'] += data['discountCost']
            send_data['totalManagementCost'] += data['managementCost']
            send_data['totalInventoryCount'] += 1

            #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
            if supplier_type == 1:
                data['supplierType'] = '위탁'
            elif supplier_type == 2:
                data['supplierType'] = '사입'
            elif supplier_type == 3:
                data['supplierType'] = '직수입'
            elif supplier_type == 4:
                data['supplierType'] = '미입고'

            if sex == 0:
                data['sex'] = '공용'
            elif sex == 1:
                data['sex'] = '남성'
            else:
                data['sex'] = '여성'

            if goods_status == 1:
                data['status'] = '스크래치'
            elif goods_status == 2:
                data['status'] = '판매불가'
            elif goods_status == 3:
                data['status'] = '폐기'
            elif goods_status == 4:
                data['status'] = '정상재고'
            elif goods_status == 5:
                data['status'] = '분실'
            elif goods_status == 6:
                data['status'] = '정산대기'
            elif goods_status == 7:
                data['status'] = '분배대기'
            elif goods_status == 8:
                data['status'] = '회수완료'
            elif goods_status == 9:
                data['status'] = '수선중'
            elif goods_status == 10:
                data['status'] = '반품정산대기'
            elif goods_status == 11:
                data['status'] = '판매완료'
            elif goods_status == 12:
                data['status'] = '출고승인대기'
            else:
                data['status'] = '고객반송대기'

            query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{data['tag']}';"
            mysql_cursor.execute(query)
            image_row = mysql_cursor.fetchone()
            if image_row:
                data['imageUrl'] = image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
            else:
                data['imageUrl'] = None
            goodsList.append(data)

        send_data['totalFirstCost'] = int(send_data['totalFirstCost'] / send_data['totalInventoryCount'])
        send_data['list'] = goodsList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#영업소 재고 현황 조회
@app.route('/office', methods=['GET'])
def getOfficeInventoryList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

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
        condition_query = " WHERE goods.goods_tag = goods_history.goods_tag"

        if 'date' in params:
            search_date = "'" + params['date'] + "'"
        else:
            search_date = "CURRENT_TIMESTAMP"

        if 'brandTagList' in params:
            brandTags = request.args.getlist('brandTagList')
            brand_query = None
            for brandTag in brandTags:
                if brand_query:
                    brand_query = brand_query + f" or goods.brand_tag = '{brandTag}'"
                else:
                    brand_query = f"goods.brand_tag = '{brandTag}'"
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
                    category_query = category_query + f" or goods.category_tag = '{categoryTag}'"
                else:
                    category_query = f"goods.category_tag = '{categoryTag}'"
            if category_query:
                if condition_query:
                    condition_query = condition_query + f" and ({category_query})"
                else:
                    condition_query = f"WHERE ({category_query})"

        if 'officeTagList' in params:
            officeTags = request.args.getlist('officeTagList')
            office_query = None
            for officeTag in officeTags:
                if office_query:
                    office_query = office_query + f" or goods.office_tag = {officeTag}"
                else:
                    office_query = f"goods.office_tag = {officeTag}"
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
                        condition_query = condition_query + f" and goods.part_number like '%{searchContent}%'"
                    else:
                        condition_query = f"WHERE goods.part_number like '%{searchContent}%'"
                elif searchType == 1:
                    if condition_query:
                        condition_query = condition_query + f" and goods.goods_tag like '%{searchContent}%'"
                    else:
                        condition_query = f"WHERE goods.goods_tag like '%{searchContent}%'"
                elif searchType == 2:
                    if condition_query:
                        condition_query = condition_query + f" and goods.color like '%{searchContent}%'"
                    else:
                        condition_query = f"WHERE goods.color like '%{searchContent}%'"
                elif searchType == 3:
                    if condition_query:
                        condition_query = condition_query + f" and goods.material like '%{searchContent}%'"
                    else:
                        condition_query = f"WHERE goods.material like '%{searchContent}%'"
                else:
                    if condition_query:
                        condition_query = condition_query + f" and goods.size like '%{searchContent}%'"
                    else:
                        condition_query = f"WHERE goods.size like '%{searchContent}%'"

        condition_query += " GROUP BY goods.office_tag, goods.brand_tag, goods.part_number ORDER BY goods.office_tag, goods.brand_tag "
        query = f"SELECT goods.office_tag, goods.brand_tag, goods.part_number, any_value(category_tag), count(case when goods.goods_tag = goods_history.goods_tag and goods_history.status != 11 and goods_history_index IN (SELECT MAX(goods_history_index) FROM goods_history WHERE goods.goods_tag = goods_history.goods_tag and update_date < {search_date}) then 1 end) as inventoryCount, SUM(goods.cost), SUM(goods.first_cost), SUM(goods.regular_cost), SUM(goods.sale_cost), SUM(goods.discount_cost), SUM(management_cost) FROM goods, goods_history " + condition_query + limit_query + ';'
        print(query)
        mysql_cursor.execute(query)
        inventory_rows = mysql_cursor.fetchall()

        inventoryList = list()
        
        for index, inventory_row in enumerate(inventory_rows):
            data = dict()
            data['index'] = start + index
            data['officeTag'] = inventory_row[0]
            brand_tag = inventory_row[1]
            data['partNumber'] = inventory_row[2]
            category_tag = inventory_row[3]
            data['inventoryCount'] = inventory_row[4]
            data['totalCost'] = inventory_row[5]
            data['totalFirstCost'] = inventory_row[6]
            data['totalRegularCost'] = inventory_row[7]
            data['totalSaleCost'] = inventory_row[8]
            data['totalDiscountCost'] = inventory_row[9]
            data['totalManagementCost'] = inventory_row[10]

            query = f"SELECT brand_name FROM brand WHERE brand_tag = '{brand_tag}';"
            mysql_cursor.execute(query)
            brand_row = mysql_cursor.fetchone()
            data['brand'] = brand_row[0]

            query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
            mysql_cursor.execute(query)
            category_row = mysql_cursor.fetchone()
            data['category'] = category_row[0]

            query = f"SELECT office_name FROM office WHERE office_tag = {data['officeTag']};"
            mysql_cursor.execute(query)
            office_row = mysql_cursor.fetchone()
            data['office'] = office_row[0]

            inventoryList.append(data)

        query = f"SELECT goods.office_tag, goods.brand_tag, goods.part_number, any_value(category_tag), count(case when goods.goods_tag = goods_history.goods_tag and goods_history.status != 11 and goods_history_index IN (SELECT MAX(goods_history_index) FROM goods_history WHERE goods.goods_tag = goods_history.goods_tag and update_date < {search_date}) then 1 end) as inventoryCount, SUM(goods.cost), SUM(goods.first_cost), SUM(goods.regular_cost), SUM(goods.sale_cost), SUM(goods.discount_cost), SUM(management_cost) FROM goods, goods_history " + condition_query + ';'
        print(query)
        mysql_cursor.execute(query)
        count_rows = mysql_cursor.fetchall()
        send_data['result'] = "SUCCESS"
        send_data['list'] = inventoryList
        send_data['totalResult'] = len(count_rows)
        send_data['totalPage'] = int(len(count_rows)/int(limit)) + 1

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#영업소 재고 상세 현황 조회
@app.route('/office/<string:officeTag>', methods=['GET'])
def getDetailOfficeInventoryList(officeTag):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()
        if not 'partNumber' in params:
            send_data = {"result": "품번을 지정하지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)

        part_number = params['partNumber']

        if 'date' in params:
            search_date = f"'{params['date']}'"
            send_data['date'] = params['date']
        else:
            search_date = "CURRENT_TIMESTAMP"
            send_data['date'] = None
        
        query = f"SELECT goods_tag, stocking_date, import_date, (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag), bl_number, season, (SELECT brand_name FROM brand WHERE brand.brand_tag = goods.brand_tag), (SELECT category_name FROM category WHERE category.category_tag = goods.category_tag), part_number, sex, color, material, size, origin_name, sale_date, (SELECT office_name FROM office WHERE office.office_tag = goods.office_tag), cost, first_cost, regular_cost, sale_cost, discount_cost, management_cost FROM goods WHERE goods.part_number = '{part_number}';"
        mysql_cursor.execute(query)
        goods_rows = mysql_cursor.fetchall()

        goodsList = list()

        send_data['result'] = "SUCCESS"
        send_data['totalCost'] = 0
        send_data['totalFirstCost'] = 0
        send_data['totalRegularCost'] = 0
        send_data['totalSaleCost'] = 0
        send_data['totalDiscountCost'] = 0
        send_data['totalManagementCost'] = 0
        send_data['totalStockingCount'] = len(goods_rows)
        send_data['totalInventoryCount'] = 0
        send_data['brand'] = None
        send_data['category'] = None
        send_data['office'] = None

        for goods_row in goods_rows:
            data = dict()
            data['tag'] = goods_row[0]

            query = f"SELECT goods_history.status FROM goods_history WHERE goods_tag = '{data['tag']}' and goods_history IN (SELECT MAX(goods_history_index) FROM goods_history WHERE goods_tag = '{data['tag']}' and update_date < {search_date});"
            mysql_cursor.execute(query)
            status_row = mysql_cursor.fetchone()
            goods_status = int(status_row[0])

            if goods_status == 11:
                continue

            data['stockingDate'] = goods_row[1]
            data['importDate'] = goods_row[2]
            supplier_type = goods_row[3]
            data['supplierName'] = goods_row[4]
            data['blNumber'] = goods_row[5]
            data['season'] = goods_row[6]
            data['brand'] = goods_row[7]
            data['category'] = goods_row[8]
            data['partNumber'] = goods_row[9]
            sex = goods_row[10]
            data['color'] = goods_row[11]
            data['material'] = goods_row[12]
            data['size'] = goods_row[13]
            data['origin'] = goods_row[14]
            data['saleDate'] = goods_row[15]
            data['office'] = goods_row[16]
            data['cost'] = goods_row[17]
            data['firstCost'] = goods_row[18]
            data['regularCost'] = goods_row[19]
            data['saleCost'] = goods_row[20]
            data['discountCost'] = goods_row[21]
            data['managementCost'] = goods_row[22]

            if not send_data['brand']:
                send_data['brand'] = data['brand']
            if not send_data['category']:
                send_data['category'] = data['category']
            if not send_data['office']:
                send_data['office'] = data['office']

            send_data['totalCost'] += data['cost']
            send_data['totalFirstCost'] += data['firstCost']
            send_data['totalRegularCost'] += data['regularCost']
            send_data['totalSaleCost'] += data['saleCost']
            send_data['totalDiscountCost'] += data['discountCost']
            send_data['totalManagementCost'] += data['managementCost']
            send_data['totalInventoryCount'] += 1

            #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
            if supplier_type == 1:
                data['supplierType'] = '위탁'
            elif supplier_type == 2:
                data['supplierType'] = '사입'
            elif supplier_type == 3:
                data['supplierType'] = '직수입'
            elif supplier_type == 4:
                data['supplierType'] = '미입고'

            if sex == 0:
                data['sex'] = '공용'
            elif sex == 1:
                data['sex'] = '남성'
            else:
                data['sex'] = '여성'

            if goods_status == 1:
                data['status'] = '스크래치'
            elif goods_status == 2:
                data['status'] = '판매불가'
            elif goods_status == 3:
                data['status'] = '폐기'
            elif goods_status == 4:
                data['status'] = '정상재고'
            elif goods_status == 5:
                data['status'] = '분실'
            elif goods_status == 6:
                data['status'] = '정산대기'
            elif goods_status == 7:
                data['status'] = '분배대기'
            elif goods_status == 8:
                data['status'] = '회수완료'
            elif goods_status == 9:
                data['status'] = '수선중'
            elif goods_status == 10:
                data['status'] = '반품정산대기'
            elif goods_status == 11:
                data['status'] = '판매완료'
            elif goods_status == 12:
                data['status'] = '출고승인대기'
            else:
                data['status'] = '고객반송대기'

            query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{data['tag']}';"
            mysql_cursor.execute(query)
            image_row = mysql_cursor.fetchone()
            if image_row:
                data['imageUrl'] = image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
            else:
                data['imageUrl'] = None
            goodsList.append(data)

        send_data['totalFirstCost'] = int(send_data['totalFirstCost'] / send_data['totalInventoryCount'])
        send_data['list'] = goodsList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#수불 현황 조회
@app.route('/receiptPayment', methods=['GET'])
def getReceiptPaymentList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if not 'startDate' in params:
            send_data = {"result": "검색 시작일을 지정하지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'endDate' in params:
            send_data = {"result": "검색 종료일을 지정하지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        
        startDate = params['startDate']
        endDate = params['endDate']

        condition_query = None

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

        if condition_query:
            condition_query += " GROUP BY office_tag "
        else:
            condition_query = " GROUP BY office_tag "
        query = f"SELECT office_tag, count(case when goods.status != 11 and stocking_date < '{startDate}' then 1 end) as baseInventoryCount, count(case when stocking_date >= '{startDate}' and stocking_date <= '{endDate}' then 1 end) as stockingCount, count(case when sale_date >= '{startDate}' and sale_date <= '{endDate}' then 1 end) as saleCount, count(case when consignment_return_date >='{startDate}' and consignment_return_date <='{endDate}' then 1 end) as consignmentReturnCount, count(case when goods.status != 11 and stocking_date <= '{endDate}' then 1 end) as totalInventoryCount FROM goods " + condition_query + ';'
        mysql_cursor.execute(query)
        inventory_rows = mysql_cursor.fetchall()

        inventoryList = list()
        
        for inventory_row in inventory_rows:
            data = dict()
            data['officeTag'] = inventory_row[0]
            data['baseInventoryCount'] = inventory_row[1]
            data['stockingCount'] = inventory_row[2]
            data['saleCount'] = inventory_row[3]
            data['inventorySettingCount'] = 0
            data['consignmentReturnCount'] = inventory_row[4]
            data['totalInventoryCount'] = inventory_row[5]

            query = f"SELECT office_name FROM office WHERE office_tag = {data['officeTag']};"
            mysql_cursor.execute(query)
            office_row = mysql_cursor.fetchone()
            data['office'] = office_row[0]

            inventoryList.append(data)

        send_data['result'] = "SUCCESS"
        send_data['list'] = inventoryList

    except Exception as e:
        #send_data = {"result": f"Error : {e}"}
        send_data = {"result": f"Error : {traceback.format_exc()}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#수불 현황 상세 조회
@app.route('/receiptPayment/<int:officeTag>', methods=['GET'])
def getReceiptPaymentDetailList(officeTag):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if not 'startDate' in params:
            send_data = {"result": "검색 시작일을 지정하지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'endDate' in params:
            send_data = {"result": "검색 종료일을 지정하지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        
        startDate = params['startDate']
        endDate = params['endDate']

        condition_query = f" WHERE office_tag = {officeTag} "

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
        
        if 'item' in params:
            item = int(params['item'])
            if item == 1:
                if condition_query:
                    condition_query = condition_query + f" and goods.status != 11 and stocking_date < '{startDate}'"
                else:
                    condition_query = f"WHERE stocking_date < '{startDate}'"
                send_data['item'] = '기초재고'
            elif item == 2:
                if condition_query:
                    condition_query = condition_query + f" and stocking_date >= '{startDate}' and stocking_date <= '{endDate}'"
                else:
                    condition_query = f"WHERE stocking_date >= '{startDate}' and stocking_date <= '{endDate}'"
                send_data['item'] = '순입고'
            elif item == 3:
                if condition_query:
                    condition_query = condition_query + f" and sale_date >= '{startDate}' and sale_date <= '{endDate}'"
                else:
                    condition_query = f"WHERE sale_date >= '{startDate}' and sale_date <= '{endDate}'"
                send_data['item'] = '판매수량'
            elif item == 4:
                if condition_query:
                    condition_query = condition_query + f" and stocking_date = '-1'"
                else:
                    condition_query = f"WHERE stocking_date = '-1'"
                send_data['재고세팅수량']
            elif item == 5:
                if condition_query:
                    condition_query = condition_query + f" and consignment_return_date >= '{startDate}' and consignment_return_date <= '{endDate}'"
                else:
                    condition_query = f"WHERE consignment_return_date >= '{startDate}' and consignment_return_date <= '{endDate}'"
                send_data['위탁회수수량']
            else:
                send_data = {"result": "검색 item이 잘못 입력 되었습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
        else:
            if condition_query:
                condition_query = condition_query + f" and goods.status != 11 and stocking_date <= '{endDate}'"
            else:
                condition_query = f"WHERE goods.status != 11 and stocking_date <= '{endDate}'"
            send_data['item'] = '총재고'

        if condition_query:
            query = f"SELECT goods_tag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, goods.status, first_cost FROM goods " + condition_query  + ';'
        else:
            query = f"SELECT goods_tag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, goods.status, first_cost FROM goods " + ';'
        mysql_cursor.execute(query)
        goods_rows = mysql_cursor.fetchall()

        send_data['result'] = 'SUCCESS'
        send_data['totalCost'] = 0
        send_data['totalFirstCost'] = 0
        send_data['totalRegularCost'] = 0
        send_data['totalSaleCost'] = 0
        send_data['totalDiscountCost'] = 0
        send_data['totalManagementCost'] = 0

        goodsList = list()
        for goods_row in goods_rows:
            data = dict()
            data['tag'] = goods_row[0]
            data['partNumber'] = goods_row[1]
            data['blNumber'] = goods_row[2]
            data['origin'] = goods_row[3]
            brand_tag = goods_row[4]
            category_tag = goods_row[5]
            office_tag = goods_row[6]
            supplier_tag = goods_row[7]
            data['color'] = goods_row[8]
            data['season'] = goods_row[9]
            sex = int(goods_row[10])
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
            goods_status = int(goods_row[21])
            data['firstCost'] = goods_row[22]
            
            send_data['totalCost'] += data['cost']
            send_data['totalFirstCost'] += data['firstCost']
            send_data['totalRegularCost'] += data['regularCost']
            send_data['totalSaleCost'] += data['saleCost']
            send_data['totalDiscountCost'] += data['discountCost']
            send_data['totalManagementCost'] += data['managementCost']

            if sex == 0:
                data['sex'] = '공용'
            elif sex == 1:
                data['sex'] = '남성'
            else:
                data['sex'] = '여성'

            query = f"SELECT brand_name FROM brand WHERE brand_tag = '{brand_tag}';"
            mysql_cursor.execute(query)
            brand_row = mysql_cursor.fetchone()
            data['brand'] = brand_row[0]

            query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
            mysql_cursor.execute(query)
            category_row = mysql_cursor.fetchone()
            data['category'] = category_row[0]

            query = f"SELECT office_name FROM office WHERE office_tag = {office_tag};"
            mysql_cursor.execute(query)
            office_row = mysql_cursor.fetchone()
            data['office'] = office_row[0]
            send_data['office'] = office_row[0]

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

            if goods_status == 1:
                data['status'] = '스크래치'
            elif goods_status == 2:
                data['status'] = '판매불가'
            elif goods_status == 3:
                data['status'] = '폐기'
            elif goods_status == 4:
                data['status'] = '정상재고'
            elif goods_status == 5:
                data['status'] = '분실'
            elif goods_status == 6:
                data['status'] = '정산대기'
            elif goods_status == 7:
                data['status'] = '분배대기'
            elif goods_status == 8:
                data['status'] = '회수완료'
            elif goods_status == 9:
                data['status'] = '수선중'
            elif goods_status == 10:
                data['status'] = '반품정산대기'
            elif goods_status == 11:
                data['status'] = '판매완료'
            elif goods_status == 12:
                data['status'] = '출고승인대기'
            else:
                data['status'] = '고객반송대기'

            query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{data['tag']}';"
            mysql_cursor.execute(query)
            image_row = mysql_cursor.fetchone()
            if image_row:
                data['imageUrl'] = image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
            else:
                data['imageUrl'] = None
            goodsList.append(data)

        send_data['list'] = goodsList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#품절 상품 리스트 조회
@app.route('/soldOut', methods=['GET'])
def getSoldOutList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

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

        limit_query = f" limit {start}, {limit}"
        condition_query = None

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
                dateString = 'register_date'
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
        
        if 'soldOutStartDate' in params:
            soldOutStartDate = params['soldOutStartDate']
            if condition_query:
                condition_query = condition_query + f" and part_number IN (SELECT part_number FROM goods WHERE sale_date >= '{soldOutStartDate}')"
            else:
                condition_query = f"WHERE part_number IN (SELECT part_number FROM goods WHERE sale_date >= '{soldOutStartDate}')"

        if 'soldOutEndDate' in params:
            soldOutEndDate = params['soldOutEndDate']
            if condition_query:
                condition_query = condition_query + f" and part_number IN (SELECT part_number FROM goods WHERE sale_date <= '{soldOutEndDate}')"
            else:
                condition_query = f"WHERE part_number IN (SELECT part_number FROM goods WHERE sale_date <= '{soldOutEndDate}')"

        if condition_query:
            condition_query += f" GROUP BY part_number, color, size"
        else:
            condition_query = f" GROUP BY part_number, color, size"
        query = f"SELECT * FROM (SELECT count(case when goods.status != 11 then 1 end) as inven, part_number, color, size, MAX(sale_date), any_value(brand_tag), any_value(category_tag), any_value(season), any_value(origin_name), any_value(material) FROM goods " + condition_query + ") as temp WHERE inven = 0 " + limit_query + ';'
        mysql_cursor.execute(query)
        goods_rows = mysql_cursor.fetchall()

        goodsList = list()
        for goods_row in goods_rows:
            data = dict()
            data['partNumber'] = goods_row[1]
            data['color'] = goods_row[2]
            data['size'] = goods_row[3]
            data['soldOutDate'] = goods_row[4]
            brand_tag = goods_row[5]
            category_tag = goods_row[6]
            data['season'] = goods_row[7]
            data['origin'] = goods_row[8]
            data['material'] = goods_row[9]

            if sex == 0:
                data['sex'] = '공용'
            elif sex == 1:
                data['sex'] = '남성'
            else:
                data['sex'] = '여성'

            query = f"SELECT brand_name FROM brand WHERE brand_tag = '{brand_tag}';"
            mysql_cursor.execute(query)
            brand_row = mysql_cursor.fetchone()
            data['brand'] = brand_row[0]

            query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
            mysql_cursor.execute(query)
            category_row = mysql_cursor.fetchone()
            data['category'] = category_row[0]
            goodsList.append(data)

        query = f"SELECT * FROM (SELECT count(case when goods.status != 11 then 1 end) as inven, part_number, color, size, MAX(sale_date), any_value(brand_tag), any_value(category_tag), any_value(season), any_value(origin_name), any_value(material) FROM goods " + condition_query + ") as temp WHERE inven = 0 " + ';'
        mysql_cursor.execute(query)
        count_rows = mysql_cursor.fetchall()

        send_data['result'] = 'SUCCESS'
        send_data['list'] = goodsList
        send_data['totalPage'] = int(len(count_rows)/int(limit)) + 1
        send_data['totalResult'] = len(count_rows)

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
        process_config = config['inventory_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"inventory_management.log"
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