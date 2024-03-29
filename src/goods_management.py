# -*- coding: utf-8 -*-
#!/usr/bin/env python3
  
import logging
import json
import sys
import yaml
import os
import shutil
import traceback
import math

import flask
from flask import request
from flask_api import status

import pymysql
import pandas as pd

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

def isNaN(data):
    return data != data

#엑셀
@app.route('/excel', methods=['GET','POST'])
def goodsExcelList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        try:
            send_data = {"excel": "http://52.79.206.187:19999/example/wizzes-erp-상품등록.xlsx"}
        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        try:
            params = request.args.to_dict()
            user_id = params['userId']
            files = flask.request.files.getlist("files")
            query = f"SELECT authority_id FROM user where user_id = '{user_id}';"
            mysql_cursor.execute(query)
            a_id_row = mysql_cursor.fetchone()
            a_id = a_id_row[0]
            if len(files) == 0:
                send_data = {"result": f"엑셀 파일이 없습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            for f in files:
                data = pd.read_excel(f)
                stocking_dates          = data['입고일']
                import_dates            = data['수입일']
                supplier_tags           = data['공급처 TAG']
                office_tags             = data['영업처 TAG']
                brand_tags              = data['브랜드 TAG']
                category_tags           = data['상품종류 TAG']
                part_numbers            = data['품번']
                goods_tags              = data['Tag_no']
                origins                 = data['원산지']
                sexs                    = data['성별 Code (0: 공용, 1: 남성, 2:여성)']
                colors                  = data['색상']
                sizes                   = data['사이즈']
                materials               = data['소재']
                seasons                 = data['시즌']
                bl_numbers              = data['BL 번호']
                memos                   = data['메모']
                costs                   = data['COST']
                regular_costs           = data['정상판매가']
                sale_costs              = data['판매가']
                event_costs             = data['행사 판매가']
                discount_costs          = data['특별 할인가']
                management_costs        = data['관리원가']
                management_cost_rates   = data['관리원가율']
                department_store_costs  = data['백화점 판매가']
                outlet_costs            = data['아울렛 판매가']
                first_costs             = data['원가']
                
                query_list = list()

                for index, goods_tag in enumerate(goods_tags):
                    if isNaN(stocking_dates[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 입고일을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(import_dates[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 수입일을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(supplier_tags[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 공급처 TAG를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    check_query = f"SELECT count(*) FROM supplier WHERE supplier_tag = {supplier_tags[index]};"
                    mysql_cursor.execute(check_query)
                    check_row = mysql_cursor.fetchone()
                    if check_row[0] == 0:
                        send_data = {"result": f"{index+1} 번째 데이터에 공급처 TAG는 존재하지 않는 값입니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(office_tags[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 영업처 TAG를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    check_query = f"SELECT count(*) FROM office WHERE office_tag = {office_tags[index]};"
                    mysql_cursor.execute(check_query)
                    check_row = mysql_cursor.fetchone()
                    if check_row[0] == 0:
                        send_data = {"result": f"{index+1} 번째 데이터에 영업처 TAG는 존재하지 않는 값입니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(brand_tags[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 브랜드 TAG를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    check_query = f"SELECT count(*) FROM brand WHERE brand_tag = '{brand_tags[index]}';"
                    mysql_cursor.execute(check_query)
                    check_row = mysql_cursor.fetchone()
                    if check_row[0] == 0:
                        send_data = {"result": f"{index+1} 번째 데이터에 브랜드 TAG는 존재하지 않는 값입니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(category_tags[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 상품종류 TAG를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    check_query = f"SELECT count(*) FROM category WHERE category_tag = '{category_tags[index]}';"
                    mysql_cursor.execute(check_query)
                    check_row = mysql_cursor.fetchone()
                    if check_row[0] == 0:
                        send_data = {"result": f"{index+1} 번째 데이터에 상품종류 TAG는 존재하지 않는 값입니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(part_numbers[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 품번을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(goods_tags[index]):
                        index_string = format(index+1, '03')
                        goods_tags[index] = f"{index_string}{brand_tags[index]}{stocking_dates[index].replace('-','')}{category_tags[index]}{supplier_tags[index]}"
                    check_query = f"SELECT count(*) FROM goods WHERE goods_tag = '{goods_tags[index]}';"
                    mysql_cursor.execute(check_query)
                    check_row = mysql_cursor.fetchone()
                    if check_row[0] != 0:
                        send_data = {"result": f"{index+1} 번째 데이터에 상품 Tag_no는 이미 존재하는 값입니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(origins[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 원산지를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(sexs[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 성별을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if sexs[index] < 0 or sexs[index] > 2:
                        send_data = {"result": f"{index+1} 번째 데이터에 성별을 입력을 확인해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(colors[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 색상을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(sizes[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 사이즈를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(materials[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 소재를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(seasons[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 시즌을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(bl_numbers[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 BL 번호를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(memos[index]):
                        memo[index] = ""
                    if isNaN(costs[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 COST를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(regular_costs[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 정상판매가를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(sale_costs[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 판매가를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if a_id == 'admin' or a_id == 'staff':
                        if isNaN(first_costs[index]):
                            send_data = {"result": f"{index+1} 번째 데이터에 원가를 입력해주세요."}
                            status_code = status.HTTP_400_BAD_REQUEST
                            return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(management_costs[index]) and isNaN(management_cost_rates[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 관리원가나 관리원가율을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    elif isNaN(management_costs[index]):
                        management_costs[index] = first_costs[index] * management_cost_rates[index] / 100
                    elif isNaN(management_cost_rates[index]):
                        management_cost_rates[index] = management_costs[index] / first_costs[index] * 100
                    if isNaN(event_costs[index]):
                        event_costs[index] = sale_costs[index]
                    if isNaN(discount_costs[index]):
                        discount_costs[index] = sale_costs[index]
                    if isNaN(department_store_costs[index]):
                        department_store_costs[index] = sale_costs[index]
                    if isNaN(outlet_costs[index]):
                        outlet_costs[index] = sale_costs[index]
                    
                    if a_id == 'admin' or a_id == 'staff':
                        query = f"INSERT INTO goods(goods_tag, consignment_flag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, description, status, stocking_date, import_date, first_cost, cost, regular_cost, sale_cost, event_cost, discount_cost, management_cost, management_cost_rate, department_store_cost, outlet_cost, user_id, register_date)"
                        query += f" VALUES ('{goods_tags[index]}',0,'{part_numbers[index]}','{bl_numbers[index]}','{origins[index]}','{brand_tags[index]}','{category_tags[index]}',{office_tags[index]}, {supplier_tags[index]}, '{colors[index]}', '{seasons[index]}', {sexs[index]}, '{sizes[index]}', '{materials[index]}', '{memos[index]}', 4, '{str(stocking_dates[index]).split(' ')[0]}', '{str(import_dates[index]).split(' ')[0]}', {first_costs[index]}, {costs[index]}, {regular_costs[index]}, {sale_costs[index]}, {event_costs[index]}, {discount_costs[index]}, {management_costs[index]}, {management_cost_rates[index]}, {department_store_costs[index]}, {outlet_costs[index]}, '{user_id}', CURRENT_TIMESTAMP);"
                        query_list.append(query)
                    else:
                        query = f"INSERT INTO goods(goods_tag, consignment_flag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, description, status, stocking_date, import_date, first_cost, cost, regular_cost, sale_cost, event_cost, discount_cost, management_cost, management_cost_rate, department_store_cost, outlet_cost, user_id, register_date)"
                        query += f" VALUES ('{goods_tags[index]}',0,'{part_numbers[index]}','{bl_numbers[index]}','{origins[index]}','{brand_tags[index]}','{category_tags[index]}',{office_tags[index]}, {supplier_tags[index]}, '{colors[index]}', '{seasons[index]}', {sexs[index]}, '{sizes[index]}', '{materials[index]}', '{memos[index]}', 4, '{str(stocking_dates[index]).split(' ')[0]}', '{str(import_dates[index]).split(' ')[0]}', 0, {costs[index]}, {regular_costs[index]}, {sale_costs[index]}, {event_costs[index]}, {discount_costs[index]}, {management_costs[index]}, {management_cost_rates[index]}, {department_store_costs[index]}, {outlet_costs[index]}, '{user_id}', CURRENT_TIMESTAMP);"
                        query_list.append(query)

                    history_query = f"INSERT INTO goods_history (goods_tag, goods_history_index, name, status, user_id, update_date) VALUES ('{goods_tags[index]}', 1, '물품등록', 4, '{user_id}', CURRENT_TIMESTAMP);"
                    query_list.append(history_query)

                for query in query_list:
                    mysql_cursor.execute(query)
                    send_data = {"result": f"SUCCESS"}
        except Exception as e:
            print(traceback.format_exc())
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

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
            query = f"SELECT goods_tag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, goods.status, first_cost FROM goods " + condition_query + limit_query + ';'
        else:
            query = f"SELECT goods_tag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, goods.status, first_cost FROM goods " + limit_query + ';'
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

            query = f"SELECT brand_name FROM brand WHERE brand_tag = '{brand_tag}';"
            mysql_cursor.execute(query)
            brand_row = mysql_cursor.fetchone()
            data['brand'] = brand_row[0]
            data['brandTag'] = brand_tag

            query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
            mysql_cursor.execute(query)
            category_row = mysql_cursor.fetchone()
            data['category'] = category_row[0]
            data['categoryTag'] = category_tag

            query = f"SELECT office_name FROM office WHERE office_tag = {office_tag};"
            mysql_cursor.execute(query)
            office_row = mysql_cursor.fetchone()
            data['office'] = office_row[0]
            data['officeTag'] = office_tag

            query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = '{supplier_tag}';"
            mysql_cursor.execute(query)
            supplier_row = mysql_cursor.fetchone()
            data['supplierName'] = supplier_row[0]
            data['supplierTag'] = supplier_tag
            
            if sex == 0:
                data['sex'] = '공용'
            elif sex == 1:
                data['sex'] = '남성'
            else:
                data['sex'] = '여성'
            data['sexTag'] = sex

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
            query = f"SELECT count(*) FROM goods " + condition_query + ';'
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
        query = f"SELECT * FROM goods WHERE goods_tag = '{goodsTag}';"
        mysql_cursor.execute(query)
        goods_row = mysql_cursor.fetchone()
        if not goods_row:
            send_data = {"result": "해당 상품은 존재하지 않습니다."}
            status_code = status.HTTP_404_NOT_FOUND
            return flask.make_response(flask.jsonify(send_data), status_code)
        
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            query = f"SELECT stocking_date, import_date, register_date, supplier_tag, office_tag, part_number, brand_tag, category_tag, origin_name, sex, color, size, material, season, bl_number, description, cost, regular_cost, sale_cost, event_cost, discount_cost, management_cost, management_cost_rate, department_store_cost, outlet_cost, first_cost, goods.status FROM goods WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)
            goods_info_row = mysql_cursor.fetchone()
            baseInfo = dict()
            costInfo = dict()
            baseInfo['stockingDate'] = goods_info_row[0]
            baseInfo['importDate'] = goods_info_row[1]
            baseInfo['registerDate'] = goods_info_row[2]
            supplier_tag = goods_info_row[3]
            office_tag = goods_info_row[4]
            baseInfo['partNumber'] = goods_info_row[5]
            brand_tag = goods_info_row[6]
            category_tag = goods_info_row[7]
            baseInfo['origin'] = goods_info_row[8]
            sex = int(goods_info_row[9])
            baseInfo['color'] = goods_info_row[10]
            baseInfo['size'] = goods_info_row[11]
            baseInfo['material'] = goods_info_row[12]
            baseInfo['season'] = goods_info_row[13]
            baseInfo['blNumber'] = goods_info_row[14]
            baseInfo['description'] = goods_info_row[15]
            costInfo['cost'] = goods_info_row[16]
            costInfo['regularCost'] = goods_info_row[17]
            costInfo['saleCost'] = goods_info_row[18]
            costInfo['eventCost'] = goods_info_row[19]
            costInfo['discountCost'] = goods_info_row[20]
            costInfo['managementCost'] = goods_info_row[21]
            costInfo['managementCostRate'] = goods_info_row[22]
            costInfo['departmentStoreCost'] = goods_info_row[23]
            costInfo['outletCost'] = goods_info_row[24]
            costInfo['firstCost'] = goods_info_row[25]
            goods_status = int(goods_info_row[26])

            query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = {supplier_tag};"
            mysql_cursor.execute(query)
            supplier_row = mysql_cursor.fetchone()
            baseInfo['supplier'] = supplier_row[0]
            supplier_type = int(supplier_row[1])
            baseInfo['supplierTag'] = supplier_tag
            
            #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
            if supplier_type == 1:
                baseInfo['supplierType'] = '위탁'
            elif supplier_type == 2:
                baseInfo['supplierType'] = '사입'
            elif supplier_type == 3:
                baseInfo['supplierType'] = '직수입'
            elif supplier_type == 4:
                baseInfo['supplierType'] = '미입고'

            if goods_status == 1:
                baseInfo['status'] = '스크래치'
            elif goods_status == 2:
                baseInfo['status'] = '판매불가'
            elif goods_status == 3:
                baseInfo['status'] = '폐기'
            elif goods_status == 4:
                baseInfo['status'] = '정상재고'
            elif goods_status == 5:
                baseInfo['status'] = '분실'
            elif goods_status == 6:
                baseInfo['status'] = '정산대기'
            elif goods_status == 7:
                baseInfo['status'] = '분배대기'
            elif goods_status == 8:
                baseInfo['status'] = '회수완료'
            elif goods_status == 9:
                baseInfo['status'] = '수선중'
            elif goods_status == 10:
                baseInfo['status'] = '반품정산대기'
            elif goods_status == 11:
                baseInfo['status'] = '판매완료'
            elif goods_status == 12:
                baseInfo['status'] = '출고승인대기'
            else:
                baseInfo['status'] = '고객반송대기'

            query = f"SELECT office_name FROM office WHERE office_tag = {office_tag};"
            mysql_cursor.execute(query)
            office_row = mysql_cursor.fetchone()
            baseInfo['office'] = office_row[0]
            baseInfo['officeTag'] = office_tag

            query = f"SELECT brand_name FROM brand WHERE brand_tag = '{brand_tag}';"
            mysql_cursor.execute(query)
            brand_row = mysql_cursor.fetchone()
            baseInfo['brand'] = brand_row[0]
            baseInfo['brandTag'] = brand_tag

            query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
            mysql_cursor.execute(query)
            category_row = mysql_cursor.fetchone()
            baseInfo['category'] = category_row[0]
            baseInfo['categoryTag'] = category_tag

            if sex == 0:
                baseInfo['sex'] = '공용'
            elif sex == 1:
                baseInfo['sex'] = '남성'
            else:
                baseInfo['sex'] = '여성'
            baseInfo['sexTag'] = sex
            
            send_data['baseInformation'] = baseInfo
            send_data['costInformation'] = costInfo

            query = f"SELECT goods_image_index, type, image_path FROM goods_image WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)
            image_rows = mysql_cursor.fetchall()
            importCertificateImages = list()
            goodsImages = list()
            for image_row in image_rows:
                index = image_row[0]
                image_type = int(image_row[1])
                image_path = image_row[2]
                image_data = dict()
                image_data['imageIndex'] = index
                image_data['imagePath'] = image_path
                image_data['imageName'] = image_path.split('/')[-1]
                image_data['imageType'] = image_path.split('.')[-1]
                image_data['imageUrl'] = image_path.replace('/home/ubuntu/data/','http://52.79.206.187:19999/')
                if image_type == 1:
                    goodsImages.append(image_data)
                else:
                    importCertificateImages.append(image_data)

            if len(importCertificateImages) > 0:
                send_data['importCertificateImages'] = importCertificateImages
            if len(goodsImages) > 0:
                send_data['goodsImages'] = goodsImages
            
            query = f"SELECT sale_date, sale_type, cost, commission_rate, seller_tag, customer, order_number, invoice_number, receiver_name, receiver_phone_number, receiver_address FROM goods_sale WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)
            sale_info_row = mysql_cursor.fetchone()
            if sale_info_row:
                soldInfo = dict()
                soldInfo['saleDate'] = sale_info_row[0]
                #1:wholesale, 2:consignment, 3:direct management, 4:event, 5:retail sale, 6:online, 7:home shopping
                saleType = int(sale_info_row[1])
                if saleType == 1:
                    soldInfo['type'] = '도매'
                elif saleType == 2:
                    soldInfo['type'] = '위탁'
                elif saleType == 3:
                    soldInfo['type'] = '직영'
                elif saleType == 4:
                    soldInfo['type'] = '행사'
                elif saleType == 5:
                    soldInfo['type'] = '소매'
                elif saleType == 6:
                    soldInfo['type'] = '온라인 쇼핑몰'
                elif saleType == 7:
                    soldInfo['type'] = '홈쇼핑'
                soldInfo['cost'] = sale_info_row[2]
                soldInfo['commissionRate'] = sale_info_row[3]
                seller_tag = sale_info_row[4]
                soldInfo['customer'] = sale_info_row[5]
                soldInfo['orderNumber'] = sale_info_row[6]
                soldInfo['invoiceNumber'] = sale_info_row[7]
                soldInfo['receiverName'] = sale_info_row[8]
                soldInfo['receiverPhoneNumber'] = sale_info_row[9]
                soldInfo['receiverAddress'] = sale_info_row[10]
                query = f"SELECT seller_name FROM seller WHERE seller_tag = {seller_tag};"
                mysql_cursor.execute(query)
                seller_row = mysql_cursor.fetchone()
                soldInfo['sellerName'] = seller_row[0]

                send_data['soldInformation'] = soldInfo

            query = f"SELECT update_date, name, user_id, status, update_value, update_method FROM goods_history WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)
            history_rows = mysql_cursor.fetchall()
            history_list = list()
            for history_row in history_rows:
                history_data = dict()
                history_data['date'] = history_row[0]
                history_data['jobName'] = history_row[1]
                user_id = history_row[2]
                goods_status = int(history_row[3])
                if goods_status == 1:
                    history_data['status'] = '스크래치'
                elif goods_status == 2:
                    history_data['status'] = '판매불가'
                elif goods_status == 3:
                    history_data['status'] = '폐기'
                elif goods_status == 4:
                    history_data['status'] = '정상재고'
                elif goods_status == 5:
                    history_data['status'] = '분실'
                elif goods_status == 6:
                    history_data['status'] = '정산대기'
                elif goods_status == 7:
                    history_data['status'] = '분배대기'
                elif goods_status == 8:
                    history_data['status'] = '회수완료'
                elif goods_status == 9:
                    history_data['status'] = '수선중'
                elif goods_status == 10:
                    history_data['status'] = '반품정산대기'
                elif goods_status == 11:
                    history_data['status'] = '판매완료'
                elif goods_status == 12:
                    history_data['status'] = '출고승인대기'
                elif goods_status == 13:
                    history_data['status'] = '고객반송대기'
                history_data['updateValue'] = history_row[4]
                if not history_row[5]:
                    method = 3
                else:
                    method = int(history_row[5])
                if method == 1:
                    history_data['updateMethod'] = '엑셀입력'
                elif method == 2:
                    history_data['updateMethod'] = '일괄입력'
                elif method == 3:
                    history_data['updateMethod'] = '직접입력'

                query = f"SELECT office_tag, name FROM user WHERE user_id = '{user_id}';"
                mysql_cursor.execute(query)
                user_row = mysql_cursor.fetchone()
                if user_row:
                    user_office_tag = user_row[0]
                    history_data['userName'] = user_row[1]

                    query = f"SELECT office_name FROM office WHERE office_tag = {user_office_tag};"
                    user_office_row = mysql_cursor.fetchone()
                    if user_office_row:
                        history_data['officeName'] = user_office_row[0]
                    else:
                        history_data['officeName'] = None
                else:
                    history_data['userName'] = user_id
                    history_data['officeName'] = None

                history_list.append(history_data)

            send_data['goodsHistory'] = history_list

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        query = f"SELECT * FROM goods WHERE goods_tag = '{goodsTag}';"
        mysql_cursor.execute(query)
        goods_row = mysql_cursor.fetchone()
        if goods_row:
            send_data = {"result": f"이미 {goodsTag} 라는 Tag는 사용 중입니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        try:
            request_body = json.loads(request.get_data())
            if not 'registerType' in request_body:
                send_data = {"result": "입력 방식이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'stockingDate' in request_body:
                send_data = {"result": "입고일이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'importDate' in request_body:
                send_data = {"result": "수입일이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'supplierTag' in request_body:
                send_data = {"result": "공급처가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'officeTag' in request_body:
                send_data = {"result": "영업소가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'partNumber' in request_body:
                send_data = {"result": "품번이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'brandTag' in request_body:
                send_data = {"result": "브랜드가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'categoryTag' in request_body:
                send_data = {"result": "상품종류가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'origin' in request_body:
                send_data = {"result": "원산지가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'sexTag' in request_body:
                send_data = {"result": "성별이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'color' in request_body:
                send_data = {"result": "색상이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'size' in request_body:
                send_data = {"result": "사이즈가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'material' in request_body:
                send_data = {"result": "소재가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'season' in request_body:
                send_data = {"result": "시즌이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'blNumber' in request_body:
                send_data = {"result": "BL 번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "설명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'cost' in request_body:
                send_data = {"result": "cost가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'regularCost' in request_body:
                send_data = {"result": "정상판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'saleCost' in request_body:
                send_data = {"result": "판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'eventCost' in request_body:
                send_data = {"result": "행사판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'discountCost' in request_body:
                send_data = {"result": "특별할인가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'managementCost' in request_body:
                send_data = {"result": "관리원가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'managementCostRate' in request_body:
                send_data = {"result": "관리원가율이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'departmentStoreCost' in request_body:
                send_data = {"result": "백화점판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'outletCost' in request_body:
                send_data = {"result": "아울렛판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "사용자가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            user_id = request_body['userId']
            query = f"SELECT authority_id FROM user where user_id = '{user_id}';"
            mysql_cursor.execute(query)
            a_id_row = mysql_cursor.fetchone()
            a_id = a_id_row[0]
            if a_id == 'admin' or a_id == 'staff':
                if not 'firstCost' in request_body:
                    send_data = {"result": "원가가 입력되지 않았습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
            
            if a_id == 'admin' or a_id == 'staff':
                query = f"INSERT INTO goods(goods_tag, consignment_flag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, description, status, stocking_date, import_date, first_cost, cost, regular_cost, sale_cost, event_cost, discount_cost, management_cost, management_cost_rate, department_store_cost, outlet_cost, user_id, register_date)"
                query += f"VALUES ('{goodsTag}', 0, '{request_body['partNumber']}', '{request_body['blNumber']}', '{request_body['origin']}', '{request_body['brandTag']}', '{request_body['categoryTag']}', {request_body['officeTag']}, {request_body['supplierTag']}, '{request_body['color']}', '{request_body['season']}', {request_body['sexTag']}, '{request_body['size']}', "
                query += f"'{request_body['material']}', '{request_body['description']}', 4, '{request_body['stockingDate']}', '{request_body['importDate']}', {request_body['firstCost']}, {request_body['cost']}, {request_body['regularCost']}, {request_body['saleCost']}, {request_body['eventCost']}, {request_body['discountCost']}, {request_body['managementCost']}, {request_body['managementCostRate']}, {request_body['departmentStoreCost']}, {request_body['outletCost']}, '{request_body['userId']}', CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)
            else:
                query = f"INSERT INTO goods(goods_tag, consignment_flag, part_number, bl_number, origin_name, brand_tag, category_tag, office_tag, supplier_tag, color, season, sex, size, material, description, status, stocking_date, import_date, first_cost, cost, regular_cost, sale_cost, event_cost, discount_cost, management_cost, management_cost_rate, department_store_cost, outlet_cost, user_id, register_date)"
                query += f"VALUES ('{goodsTag}', 0, '{request_body['partNumber']}', '{request_body['blNumber']}', '{request_body['origin']}', '{request_body['brandTag']}', '{request_body['categoryTag']}', {request_body['officeTag']}, {request_body['supplierTag']}, '{request_body['color']}', '{request_body['season']}', {request_body['sexTag']}, '{request_body['size']}', "
                query += f"'{request_body['material']}', '{request_body['description']}', 4, '{request_body['stockingDate']}', '{request_body['importDate']}', 0, {request_body['cost']}, {request_body['regularCost']}, {request_body['saleCost']}, {request_body['eventCost']}, {request_body['discountCost']}, {request_body['managementCost']}, {request_body['managementCostRate']}, {request_body['departmentStoreCost']}, {request_body['outletCost']}, '{request_body['userId']}', CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)

            query = f"INSERT INTO goods_history (goods_tag, goods_history_index, name, status, user_id, update_date) VALUES ('{goodsTag}', 1, '물품등록', 4, '{request_body['userId']}', CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            if not os.path.exists(f"/home/ubuntu/data/goods/{goodsTag}"):
                os.makedirs(f"/home/ubuntu/data/goods/{goodsTag}")

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = goodsTag

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'PUT':
        query = f"SELECT * FROM goods WHERE goods_tag = '{goodsTag}';"
        mysql_cursor.execute(query)
        goods_row = mysql_cursor.fetchone()
        if not goods_row:
            send_data = {"result": "해당 상품은 존재하지 않습니다."}
            status_code = status.HTTP_404_NOT_FOUND
            return flask.make_response(flask.jsonify(send_data), status_code)
        
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'registerType' in request_body:
                send_data = {"result": "입력 방식이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'stockingDate' in request_body:
                send_data = {"result": "입고일이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'importDate' in request_body:
                send_data = {"result": "수입일이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'supplierTag' in request_body:
                send_data = {"result": "공급처가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'officeTag' in request_body:
                send_data = {"result": "영업소가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'partNumber' in request_body:
                send_data = {"result": "품번이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'brandTag' in request_body:
                send_data = {"result": "브랜드가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'categoryTag' in request_body:
                send_data = {"result": "상품종류가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'origin' in request_body:
                send_data = {"result": "원산지가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'sexTag' in request_body:
                send_data = {"result": "성별이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'color' in request_body:
                send_data = {"result": "색상이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'size' in request_body:
                send_data = {"result": "사이즈가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'material' in request_body:
                send_data = {"result": "소재가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'season' in request_body:
                send_data = {"result": "시즌이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'blNumber' in request_body:
                send_data = {"result": "BL 번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "설명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'cost' in request_body:
                send_data = {"result": "cost가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'regularCost' in request_body:
                send_data = {"result": "정상판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'saleCost' in request_body:
                send_data = {"result": "판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'eventCost' in request_body:
                send_data = {"result": "행사판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'discountCost' in request_body:
                send_data = {"result": "특별할인가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'managementCost' in request_body:
                send_data = {"result": "관리원가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'managementCostRate' in request_body:
                send_data = {"result": "관리원가율이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'departmentStoreCost' in request_body:
                send_data = {"result": "백화점판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'outletCost' in request_body:
                send_data = {"result": "아울렛판매가가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "사용자가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            user_id = request_body['userId']
            query = f"SELECT authority_id FROM user where user_id = '{user_id}';"
            mysql_cursor.execute(query)
            a_id_row = mysql_cursor.fetchone()
            a_id = a_id_row[0]
            if a_id == 'admin':
                if not 'firstCost' in request_body:
                    send_data = {"result": "원가가 입력되지 않았습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
            if goodsTag != request_body['goodsTag']:
                query = f"SELECT * FROM goods WHERE goods_tag = '{request_body['goodsTag']}';"
                mysql_cursor.execute(query)
                goods_row = mysql_cursor.fetchone()
                if goods_row:
                    send_data = {"result": "해당 상품 태그는 이미 존재하는 상품 태그입니다."}
                    status_code = status.HTTP_404_NOT_FOUND
                    return flask.make_response(flask.jsonify(send_data), status_code)
            
            if a_id == 'admin':
                query = f"UPDATE goods SET goods_tag = '{request_body['goodsTag']}',"
                query += f"part_number = '{request_body['partNumber']}', "
                query += f"bl_number = '{request_body['blNumber']}', "
                query += f"origin_name = '{request_body['origin']}', "
                query += f"brand_tag = '{request_body['brandTag']}', "
                query += f"category_tag = '{request_body['categoryTag']}', "
                query += f"office_tag = {request_body['officeTag']}, "
                query += f"supplier_tag = {request_body['supplierTag']}, "
                query += f"color = '{request_body['color']}', "
                query += f"season = '{request_body['season']}', "
                query += f"sex = {request_body['sexTag']}, "
                query += f"size = '{request_body['size']}', "
                query += f"material = '{request_body['material']}', "
                query += f"description = '{request_body['description']}', "
                query += f"stocking_date = '{request_body['stockingDate']}', "
                query += f"import_date = '{request_body['importDate']}', "
                query += f"first_cost = {request_body['firstCost']}, "
                query += f"cost = {request_body['cost']}, "
                query += f"regular_cost = {request_body['regularCost']}, "
                query += f"sale_cost = {request_body['saleCost']}, "
                query += f"event_cost = {request_body['eventCost']}, "
                query += f"discount_cost = {request_body['discountCost']}, "
                query += f"management_cost = {request_body['managementCost']}, "
                query += f"management_cost_rate = {request_body['managementCostRate']}, "
                query += f"department_store_cost = {request_body['departmentStoreCost']}, "
                query += f"outlet_cost = {request_body['outletCost']}, "
                query += f"user_id = '{request_body['userId']}', "
                query += f"register_date = CURRENT_TIMESTAMP "
                query += f"WHERE goods_tag = '{goodsTag}';"
                mysql_cursor.execute(query)
            else:
                query = f"UPDATE goods SET goods_tag = '{request_body['goodsTag']}',"
                query += f"part_number = '{request_body['partNumber']}', "
                query += f"bl_number = '{request_body['blNumber']}', "
                query += f"origin_name = '{request_body['origin']}', "
                query += f"brand_tag = '{request_body['brandTag']}', "
                query += f"category_tag = '{request_body['categoryTag']}', "
                query += f"office_tag = {request_body['officeTag']}, "
                query += f"supplier_tag = {request_body['supplierTag']}, "
                query += f"color = '{request_body['color']}', "
                query += f"season = '{request_body['season']}', "
                query += f"sex = {request_body['sexTag']}, "
                query += f"size = '{request_body['size']}', "
                query += f"material = '{request_body['material']}', "
                query += f"description = '{request_body['description']}', "
                query += f"stocking_date = '{request_body['stockingDate']}', "
                query += f"import_date = '{request_body['importDate']}', "
                query += f"first_cost = 0, "
                query += f"cost = {request_body['cost']}, "
                query += f"regular_cost = {request_body['regularCost']}, "
                query += f"sale_cost = {request_body['saleCost']}, "
                query += f"event_cost = {request_body['eventCost']}, "
                query += f"discount_cost = {request_body['discountCost']}, "
                query += f"management_cost = {request_body['managementCost']}, "
                query += f"management_cost_rate = {request_body['managementCostRate']}, "
                query += f"department_store_cost = {request_body['departmentStoreCost']}, "
                query += f"outlet_cost = {request_body['outletCost']}, "
                query += f"user_id = '{request_body['userId']}', "
                query += f"register_date = CURRENT_TIMESTAMP "
                query += f"WHERE goods_tag = '{goodsTag}';"
                mysql_cursor.execute(query)

            query = f"SELECT goods.status FROM goods WHERE goods_tag = '{request_body['goodsTag']}';"
            mysql_cursor.execute(query)
            status_row = mysql_cursor.fetchone()
            goods_status = status_row[0]

            query = f"select MAX(goods_history_index) FROM goods_history WHERE goods_tag = '{request_body['goodsTag']}';"
            mysql_cursor.execute(query)
            index_row = mysql_cursor.fetchone()
            if not index_row:
                index = 1
            elif not index_row[0]:
                index = 1
            else:
                index = index_row[0] + 1

            query = f"INSERT INTO goods_history (goods_tag, goods_history_index, name, status, user_id, update_date) VALUES ('{request_body['goodsTag']}', {index}, '물품정보수정', {goods_status}, '{request_body['userId']}', CURRENT_TIMESTAMP);"
            print(query)
            mysql_cursor.execute(query)

            if not os.path.exists(f"/home/ubuntu/data/goods/{request_body['goodsTag']}"):
                os.makedirs(f"/home/ubuntu/data/goods/{request_body['goodsTag']}")

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = request_body['goodsTag']

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:
            query = f"DELETE FROM goods_sale WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)

            query = f"DELETE FROM goods_history WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)
            
            query = f"DELETE FROM goods_image WHERE goods_tag ='{goodsTag}';"
            mysql_cursor.execute(query)

            query = f"DELETE FROM goods WHERE goods_tag = '{goodsTag}';"
            mysql_cursor.execute(query)

            dir_path = f"/home/ubuntu/data/goods/{goodsTag}"
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)

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
            condition_query = condition_query + f" GROUP BY stocking_date, supplier_tag ORDER BY stocking_date DESC"
            query = f"SELECT stocking_date, supplier_tag, any_value(bl_number), count(goods_tag), sum(first_cost), sum(management_cost), any_value(user_id) FROM goods " + condition_query + limit_query 
        else:
            condition_query = f" GROUP BY stocking_date, supplier_tag ORDER BY stocking_date DESC"
            query = f"SELECT stocking_date, supplier_tag, any_value(bl_number), count(goods_tag), sum(first_cost), sum(management_cost), any_value(user_id) FROM goods " + condition_query + limit_query 
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

            query = f"SELECT name FROM user WHERE user_id = '{user_id}';"
            mysql_cursor.execute(query)
            user_row = mysql_cursor.fetchone()
            data['registerName'] = user_row[0]
            
            goodsList.append(data)

        query = f"SELECT count(goods_tag), sum(first_cost), sum(management_cost) FROM goods " + condition_query + ';'
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

#원가 관리 상세조회, 관리원가 수정
@app.route('/firstCost/<int:supplierTag>/<string:stockingDate>', methods=['GET','PUT'])
def firstCostDetailAPIList(supplierTag,stockingDate):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    query = f"SELECT goods_tag, import_date, register_date, bl_number, season, brand_tag, category_tag, part_number, sex, color, material, size, origin_name, sale_date, office_tag, cost, regular_cost, sale_cost, discount_cost, management_cost, user_id, first_cost FROM goods WHERE supplier_tag = {supplierTag} and stocking_date = '{stockingDate}' ORDER BY register_date DESC;"
    mysql_cursor.execute(query)
    goods_rows = mysql_cursor.fetchall()
    if len(goods_rows) == 0:
        send_data = {"result": "해당 입고일, 공급처 TAG에 데이터를 찾을 수 없습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'GET':
        try:
            send_data['stockingDate'] = stockingDate
            send_data['stockingCount'] = len(goods_rows)
            totalStockCost = 0
            totalManagementCost = 0
            user = ''
            goodsList = list()
            for goods_row in goods_rows:
                data = dict()
                data['tag'] = goods_row[0]
                data['stockingDate'] = stockingDate
                data['importDate'] = goods_row[1]
                data['registerDate'] = goods_row[2]
                data['blNumber'] = goods_row[3]
                data['season'] = goods_row[4]
                brand_tag = goods_row[5]
                category_tag = goods_row[6]
                data['partNumber'] = goods_row[7]
                sex = int(goods_row[8])
                data['color'] = goods_row[9]
                data['material'] = goods_row[10]
                data['size'] = goods_row[11]
                data['origin'] = goods_row[12]
                data['saleDate'] = goods_row[13]
                office_tag = goods_row[14]
                data['cost'] = goods_row[15]
                data['regularCost'] = goods_row[16]
                data['saleCost'] = goods_row[17]
                data['discountCost'] = goods_row[18]
                data['managementCost'] = goods_row[19]
                user_id = goods_row[20]
                data['firstCost'] = goods_row[21]
                totalStockCost += data['firstCost']
                totalManagementCost += data['managementCost']

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

                query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = '{supplierTag}';"
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

                if sex == 0:
                    data['sex'] = '공용'
                elif sex == 1:
                    data['sex'] = '남성'
                else:
                    data['sex'] = '여성'

                query = f"SELECT name FROM user WHERE user_id = '{user_id}';"
                mysql_cursor.execute(query)
                user_row = mysql_cursor.fetchone()
                user = user_row[0]

                goodsList.append(data)
            
            send_data['registerName'] = user
            send_data['totalStockCost'] = totalStockCost
            send_data['totalManagementCost'] = totalManagementCost
            send_data['averageManagementCostRate'] = float(totalManagementCost/totalStockCost)*100
            send_data['list'] = goodsList


        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'PUT':
        try:
            request_body = json.loads(request.get_data())
            user_id = request_body['userId']
            query = f"SELECT authority_id FROM user where user_id = '{user_id}';"
            mysql_cursor.execute(query)
            a_id_row = mysql_cursor.fetchone()
            a_id = a_id_row[0]
            if a_id != 'admin':
                send_data = {"result": "Admin이 아님으로 원가 수정할 수 없습니다"}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'totalManagementCost' in request_body:
                send_data = {"result": "총 원가관리비용이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            query = f"SELECT goods_tag FROM goods WHERE supplier_tag = {supplierTag} and stocking_date = '{stockingDate}';"
            mysql_cursor.execute(query)
            goods_rows = mysql_cursor.fetchall()
            managementCost = int(request_body['totalManagementCost']/len(goods_rows))
            for goods_row in goods_rows:
                goods_tag = goods_row[0]
                query = f"SELECT first_cost FROM goods WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)
                first_cost_row = mysql_cursor.fetchone()
                first_cost = first_cost_row[0]
                rate = float(managementCost/first_cost)*100
                query = f"UPDATE goods SET management_cost = {managementCost}, management_cost_rate = {rate} WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#상품 이미지 등록
@app.route('/<string:goodsTag>/image', methods=['POST'])
def postGoodsImageList(goodsTag):
    send_data = dict()
    status_code = status.HTTP_201_CREATED
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)
    query = f"SELECT * FROM goods WHERE goods_tag = '{goodsTag}';"
    mysql_cursor.execute(query)
    goods_row = mysql_cursor.fetchone()
    if not goods_row:
        send_data = {"result": "해당 상품은 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)
    try:
        query = f"SELECT MAX(goods_image_index) FROM goods_image WHERE goods_tag = '{goodsTag}';"
        mysql_cursor.execute(query)
        index_row = mysql_cursor.fetchone()
        if not index_row[0]:
            index = 1
        else:
            index = index_row[0] + 1

        files = flask.request.files.getlist("files")
        if len(files) < 1:
            send_data = {"result": "등록할 파일을 입력받지 못했습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        filePath = f"/home/ubuntu/data/goods/{goodsTag}/"
        for file in files:
            file.save(filePath+file.filename)
            image_path = filePath+file.filename
            query = f"INSERT INTO goods_image(goods_tag, goods_image_index, type, image_path, user_id, register_date) VALUES ('{goodsTag}',{index},1,'{image_path}','admin',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)
            index += 1

        send_data['result'] = 'SUCCESS'
        send_data['tag'] = goodsTag

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#상품 이미지 삭제
@app.route('/<string:goodsTag>/image/<int:imageIndex>', methods=['DELETE'])
def deleteGoodsImageList(goodsTag,imageIndex):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)
    try:
        query = f"SELECT * FROM goods WHERE goods_tag = '{goodsTag}';"
        mysql_cursor.execute(query)
        goods_row = mysql_cursor.fetchone()
        if not goods_row:
            send_data = {"result": "해당 상품은 존재하지 않습니다."}
            status_code = status.HTTP_404_NOT_FOUND
            return flask.make_response(flask.jsonify(send_data), status_code)
        query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{goodsTag}' and goods_image_index = {imageIndex};"
        mysql_cursor.execute(query)
        image_row = mysql_cursor.fetchone()
        if not image_row:
            send_data = {"result": "해당 상품 이미지는 존재하지 않습니다."}
            status_code = status.HTTP_404_NOT_FOUND
            return flask.make_response(flask.jsonify(send_data), status_code)
        image_path = image_row[0]
        query = f"DELETE FROM goods_image WHERE goods_tag = '{goodsTag}' and goods_image_index = {imageIndex};"
        mysql_cursor.execute(query)

        if os.path.isfile(image_path):
            os.remove(image_path)

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