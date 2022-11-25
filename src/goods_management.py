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
                    office_query = office_query + f" or office_tag = '{officeTag}'"
                else:
                    office_query = f"office_tag = '{officeTag}'"
            if office_query:
                if condition_query:
                    condition_query = condition_query + f" and ({office_query})"
                else:
                    condition_query = f"WHERE ({office_query})"

        if 'statusList' in params:
            statuses = request.args.getlist('statusList')
            status_query = None
            for status in statuses:
                if status_query:
                    status_query = status_query + f" or status = {status}"
                else:
                    status_query = f"status = {status}"
            if status_query:
                if condition_query:
                    condition_query = condition_query + f" and ({status_query})"
                else:
                    condition_query = f"WHERE ({status_query})"

        if 'imageFlag' in params:
            imageFlag = int(params['imageFlag'])
            if imageFlag < 0 or imageFlag > 2:
                send_data = {"result": "이미지 구분이 올바르지 않습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if imageFlag == 1:
                if condition_query:
                    condition_query = condition_query + f" and goods_tag IN (SELECT DISTINCT goods_tag FROM goods_image)"
                else:
                    condition_query = f"WHERE goods_tag IN (SELECT DISTINCT goods_tag FROM goods_image)"
            if imageFlag == 2:
                if condition_query:
                    condition_query = condition_query + f" and goods_tag NOT IN (SELECT DISTINCT goods_tag FROM goods_image)"
                else:
                    condition_query = f"WHERE goods_tag NOT IN (SELECT DISTINCT goods_tag FROM goods_image)"
        
        if 'searchType' in params:
            searchType = int(params['imageFlag'])
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
            query = f"SELECT goods_tag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost FROM goods" + condition_query + limit_query + ';'
        else:
            query = f"SELECT goods_tag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost FROM goods" + limit_query + ';'
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
            data['sex'] = goods_row[10]
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
            data['supplierType'] = supplier_row[1]

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
        send_data['totalGoods'] = int(count_row[0])

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#상품 상세 조회, 등록, 수정, 삭제
@app.route('/<string:goodsTag>', methods=['GET','PUT','POST','DELETE'])
def goodsDetailAPIList(goodsTag):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)
    
    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:
            

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)


#원가 리스트 조회
@app.route('/firstCost', methods=['GET'])
def getGoodsFirstCostList():
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
            searchType = int(params['imageFlag'])
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
            condition_query = condition_query + f" GROUP BY stocking_date, supplier_tag ORDER BY stockingDate DESC"
            query = f"SELECT stocking_date, supplier_tag, bl_number, count(goods_tag), sum(first_cost), sum(management_cost), user_id FROM goods" + condition_query + limit_query + ';'
        else:
            condition_query = f" GROUP BY stockingDate, supplier_tag ORDER BY stockingDate DESC"
            query = f"SELECT stocking_date, supplier_tag, bl_number, count(goods_tag), sum(first_cost), sum(management_cost), user_id FROM goods" + condition_query + limit_query + ';'
        mysql_cursor.execute(query)
        goods_rows = mysql_cursor.fetchall()

        goodsList = list()
        for goods_row in goods_rows:
            data = dict()
            data['stockingDate'] = goods_row[0]
            data['supplierTag'] = goods_row[1]
            data['blNumber'] = goods_row[2]
            data['stockCount'] = goods_row[3]
            data['totalStockCost'] = goods_row[4]
            data['totalManagementCost'] = goods_row[5]
            data['averageManagementCostRate'] = float(data['totalManagementCost']/int(data['totalStockCost']))*100
            user_id = goods_row[6]

            query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = '{data['supplierTag']}';"
            mysql_cursor.execute(query)
            supplier_row = mysql_cursor.fetchone()
            data['supplierName'] = supplier_row[0]
            data['supplierType'] = supplier_row[1]

            query = f"SELECT name FROM user WHERE user_id = '{user_id}';"
            mysql_cursor.execute(query)
            user_row = mysql_cursor.fetchone()
            data['registerName'] = user_row[0]
            
            goodsList.append(data)

        query = f"SELECT count(goods_tag), sum(first_cost), sum(management_cost) FROM goods" + condition_query + ';'
        mysql_cursor.execute(query)
        count_rows = mysql_cursor.fetchall()
        send_data['totalSearchResult'] = len(count_rows)
        send_data['totalStockCount'] = 0
        send_data['totalstockCost'] = 0
        send_data['totalManagementCost'] = 0
        for count_row in count_rows:
            send_data['totalStockCount'] += int(count_row[0])
            send_data['totalstockCost'] += int(count_row[1])
            send_data['totalManagementCost'] += int(count_row[2])

        send_data['result'] = 'SUCCESS'
        send_data['list'] = goodsList
        send_data['totalPage'] = int(int(send_data['totalSearchResult'])/int(limit)) + 1
        send_data['averageManagementCostRate'] = float(send_data['totalManagementCost']/send_data['totalstockCost'])*100

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
        process_config = config['goods_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"goods_management.log"
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