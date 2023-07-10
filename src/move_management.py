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
def moveExcelList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        try:
            send_data = {"excel": "http://52.79.206.187:19999/example/wizzes-erp-출고요청.xlsx"}
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
            query = f"SELECT authority_id, office_tag FROM user where user_id = '{user_id}';"
            mysql_cursor.execute(query)
            a_id_row = mysql_cursor.fetchone()
            a_id = a_id_row[0]
            user_office = a_id_row[1]
            if len(files) == 0:
                send_data = {"result": f"엑셀 파일이 없습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            for f in files:
                data = pd.read_excel(f)
                from_office_tags    = data['출발 영업처 TAG']
                to_office_tags      = data['도착 영업처 TAG']
                goods_tags          = data['Tag_no']
                export_dates        = data['출고일']
                memos               = data['메모']
                approver_users      = data['출고 승인자 이름']
                move_users          = data['출고 처리자 이름']
                
                query_list = list()

                for index, goods_tag in enumerate(goods_tags):
                    if isNaN(from_office_tags[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 출발 영업처 TAG를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    check_query = f"SELECT count(*) FROM office WHERE office_tag = {from_office_tags[index]};"
                    mysql_cursor.execute(check_query)
                    check_row = mysql_cursor.fetchone()
                    if check_row[0] == 0:
                        send_data = {"result": f"{index+1} 번째 데이터에 출발 영업처 TAG는 존재하지 않는 값입니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if a_id == 'manager' and user_office != from_office_tags[index]:
                        send_data = {"result": f"{index+1} 번째 데이터에 출발 영업처 TAG는 권한이 없습니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(to_office_tags[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 도착 영업처 TAG를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    check_query = f"SELECT count(*) FROM office WHERE office_tag = {to_office_tags[index]};"
                    mysql_cursor.execute(check_query)
                    check_row = mysql_cursor.fetchone()
                    if check_row[0] == 0:
                        send_data = {"result": f"{index+1} 번째 데이터에 도착 영업처 TAG는 존재하지 않는 값입니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(goods_tags[index]):
                        send_data = {"result": f"{index+1} 번째 데이터에 Tag_no를 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    check_query = f"SELECT count(*) FROM goods WHERE goods_tag = '{goods_tags[index]}';"
                    mysql_cursor.execute(check_query)
                    check_row = mysql_cursor.fetchone()
                    if check_row[0] == 0:
                        send_data = {"result": f"{index+1} 번째 데이터에 Tag_no는 존재하지 않는 값입니다."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(export_dates[index]):
                        send_data = {"result": f"{index} 번째 데이터에 출고일을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(memos[index]):
                        memos[index] = ''
                    if isNaN(approver_users[index]):
                        send_data = {"result": f"{index} 번째 데이터에 출고 승인자 이름을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)
                    if isNaN(move_users[index]):
                        send_data = {"result": f"{index} 번째 데이터에 출고 처리자 이름을 입력해주세요."}
                        status_code = status.HTTP_400_BAD_REQUEST
                        return flask.make_response(flask.jsonify(send_data), status_code)

                    query1 = f"DELETE FROM goods_movement WHERE goods_tag = '{goods_tags[index]}';"
                    query_list.append(query1)

                    query2 = f"INSERT INTO goods_movement (goods_tag, from_office_tag, to_office_tag, export_date, status, description, move_user, approver_user, user_id, register_type, register_date) "
                    query2 += f"VALUES ('{goods_tags[index]}', {from_office_tags[index]}, {to_office_tags[index]}, '{str(export_dates[index]).split(' ')[0]}', 0, '{memos[index]}', '{move_users[index]}', '{approver_users[index]}', '{user_id}', 1, CURRENT_TIMESTAMP);"
                    query_list.append(query2)
                
                    query3 = f"select MAX(goods_history_index) FROM goods_history WHERE goods_tag = '{goods_tags[index]}';"
                    mysql_cursor.execute(query3)
                    index_row = mysql_cursor.fetchone()
                    if not index_row:
                        h_index = 1
                    elif not index_row[0]:
                        h_index = 1
                    else:
                        h_index = index_row[0] + 1

                    query4 = f"INSERT INTO goods_history(goods_tag, goods_history_index, name, status, update_method, user_id, update_date) "
                    query4 += f"VALUES ('{goods_tags[index]}',{h_index},'출고요청',12,1,'{user_id}',CURRENT_TIMESTAMP);"
                    query_list.append(query4)

                    query5 = f"UPDATE goods SET goods.status = 12 WHERE goods_tag = '{goods_tags[index]}';"
                    query_list.append(query5)

                
                for query in query_list:
                    mysql_cursor.execute(query)
                    send_data = {"result": f"SUCCESS"}
        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    
# 상품 리스트 조회 및 출고 요청
@app.route('/', methods=['GET','POST'])
def moveList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        try:
            params = request.args.to_dict()
            user_id = params['userId']
            query = f"SELECT authority_id, office_tag FROM user where user_id = '{user_id}';"
            mysql_cursor.execute(query)
            user_row = mysql_cursor.fetchone()
            a_id = user_row[0]
            user_office = user_row[1]
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
            if a_id == 'manager':
                condition_query = f" WHERE goods.status = 4 and goods.office_tag = {user_office}"
            else:
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
                query = f"SELECT goods_tag, part_number, bl_number, origin_name, (SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, first_cost FROM goods " + condition_query + limit_query + ';'
            else:
                condition_query = ' ORDER BY brand'
                query = f"SELECT goods_tag, part_number, bl_number, origin_name, (SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, first_cost FROM goods " + condition_query + limit_query + ';'
            mysql_cursor.execute(query)
            goods_rows = mysql_cursor.fetchall()

            send_data['table'] = dict()
            send_data['table']['column'] = ['검색 번호','입고일','수입일','공급처유형','공급처','BL번호','시즌','이미지','브랜드','상품종류','품번','Tag_no','성별','색상','소재','사이즈','원산지','영업처','COST','원가','정상판매가','판매가','특별할인가']
            send_data['table']['rows'] = list()

            for index, goods_row in enumerate(goods_rows):
                data = list()
                tag = goods_row[0]
                data.append(start+index+1)
                data.append(goods_row[13])
                data.append(goods_row[14])

                supplier_tag = goods_row[7]
                query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = '{supplier_tag}';"
                mysql_cursor.execute(query)
                supplier_row = mysql_cursor.fetchone()
                #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
                supplier_type = int(supplier_row[1])
                if supplier_type == 1:
                    data.append('위탁')
                elif supplier_type == 2:
                    data.append('사입')
                elif supplier_type == 3:
                    data.append('직수입')
                else:
                    data.append('미입고')
                data.append(supplier_row[0])
                data.append(goods_row[2])
                data.append(goods_row[9])

                query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{tag}';"
                mysql_cursor.execute(query)
                image_row = mysql_cursor.fetchone()
                if image_row:
                    data.append(image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/'))
                else:
                    data.append(None)
                
                data.append(goods_row[4])

                category_tag = goods_row[5]
                query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
                mysql_cursor.execute(query)
                category_row = mysql_cursor.fetchone()
                data.append(category_row[0])

                data.append(goods_row[1])
                data.append(tag)

                sex = int(goods_row[10]) 
                if sex == 0:
                    data.append('공용')
                elif sex == 1:
                    data.append('남성')
                else:
                    data.append('여성')

                data.append(goods_row[8])
                data.append(goods_row[12])
                data.append(goods_row[11])
                data.append(goods_row[3])
                
                office_tag = goods_row[6]
                query = f"SELECT office_name FROM office WHERE office_tag = {office_tag};"
                mysql_cursor.execute(query)
                office_row = mysql_cursor.fetchone()
                data.append(office_row[0])
                
                data.append(goods_row[16])
                data.append(goods_row[21])
                data.append(goods_row[17])
                data.append(goods_row[18])
                data.append(goods_row[19])

                send_data['table']['rows'].append(data)

            if condition_query:
                query = f"SELECT count(*) FROM goods" + condition_query.replace('ORDER BY brand','') + ';'
            else:
                query = f"SELECT count(*) FROM goods;"
            mysql_cursor.execute(query)
            count_row = mysql_cursor.fetchone()

            send_data['result'] = 'SUCCESS'
            send_data['totalPage'] = int(int(count_row[0])/int(limit)) + 1
            send_data['totalMove'] = int(count_row[0])

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    elif flask.request.method == 'POST':
        try:
            request_body = json.loads(request.get_data())
            if not 'requestType' in request_body:
                send_data = {"result": "입력 방식이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'fromOfficeTag' in request_body:
                send_data = {"result": "출발 영업소가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'toOfficeTag' in request_body:
                send_data = {"result": "도착 영업소가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'goodsTagList' in request_body:
                send_data = {"result": "물품 태그 리스트가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if len(request_body['goodsTagList']) == 0:
                send_data = {"result": "물품 태그 리스트가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'exportDate' in request_body:
                send_data = {"result": "출고일이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'approverName' in request_body:
                send_data = {"result": "승인자가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'moverName' in request_body:
                send_data = {"result": "출고자가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            register_type = request_body['requestType']
            from_office_tag = request_body['fromOfficeTag']
            to_office_tag = request_body['toOfficeTag']
            goodsTagList = request_body['goodsTagList']
            export_date = request_body['exportDate']
            description = request_body['description']
            move_user = request_body['moverName']
            approver_user = request_body['approverName']
            user_id = request_body['userId']

            for goods_tag in goodsTagList:
                
                query = f"DELETE FROM goods_movement WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)

                query = f"INSERT INTO goods_movement (goods_tag, from_office_tag, to_office_tag, export_date, status, description, move_user, approver_user, user_id, register_type, register_date) "
                query += f"VALUES ('{goods_tag}', {from_office_tag}, {to_office_tag}, '{export_date}', 0, '{description}', '{move_user}', '{approver_user}', '{user_id}', {register_type}, CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)
                
                query = f"select MAX(goods_history_index) FROM goods_history WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)
                index_row = mysql_cursor.fetchone()
                if not index_row:
                    index = 1
                elif not index_row[0]:
                    index = 1
                else:
                    index = index_row[0] + 1

                query = f"INSERT INTO goods_history(goods_tag, goods_history_index, name, status, update_method, user_id, update_date) "
                query += f"VALUES ('{goods_tag}',{index},'출고요청',12,{register_type},'{user_id}',CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)

                query = f"UPDATE goods SET goods.status = 12 WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)

            send_data['result'] = "SUCCESS"
            send_data['tags'] = goodsTagList

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#출고승인대기 리스트 조회 및 출고 승인
@app.route('/approve', methods=['GET','POST'])
def approveList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        try:
            params = request.args.to_dict()
            user_id = params['userId']
            query = f"SELECT authority_id, office_tag FROM user where user_id = '{user_id}';"
            mysql_cursor.execute(query)
            user_row = mysql_cursor.fetchone()
            a_id = user_row[0]
            user_office = user_row[1]
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
            if a_id == 'manager':
                condition_query = f" WHERE goods.goods_tag = goods_movement.goods_tag and goods.status = 12 and goods_movement.to_office_tag = {user_office}"
            else:
                condition_query = " WHERE goods.goods_tag = goods_movement.goods_tag and goods.status = 12"

            if 'dateType' in params:
                dateType = int(params['dateType'])
                if dateType < 0 or dateType > 2:
                    send_data = {"result": "날짜 검색 구분이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if dateType == 0:
                    dateString = 'goods_movement.export_date'
                elif dateType == 1:
                    dateString = 'goods_movement.register_date'
                elif dateType == 2:
                    dateString = 'stocking_date'
                elif dateType == 3:
                    dateString = 'import_date'
                else:
                    dateString = 'goods.register_date'
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

            if 'fromOfficeTagList' in params:
                officeTags = request.args.getlist('fromOfficeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or from_office_tag = '{officeTag}'"
                    else:
                        office_query = f"from_office_tag = '{officeTag}'"
                if office_query:
                    if condition_query:
                        condition_query = condition_query + f" and goods_tag ANY (SELECT goods_tag FROM goods_movement WHERE {office_query})"
                    else:
                        condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_movement WHERE {office_query})"
            
            if 'toOfficeTagList' in params:
                officeTags = request.args.getlist('toOfficeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or to_office_tag = '{officeTag}'"
                    else:
                        office_query = f"to_office_tag = '{officeTag}'"
                if office_query:
                    if condition_query:
                        condition_query = condition_query + f" and goods_tag ANY (SELECT goods_tag FROM goods_movement WHERE {office_query})"
                    else:
                        condition_query = f"WHERE goods_tag ANY (SELECT goods_tag FROM goods_movement WHERE {office_query})"
        
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

            if 'moveUserName' in params:
                mover = params['moveUserName']
                if condition_query:
                    condition_query += f" and goods_movement.goods_tag IN (SELECT goods_movement.goods_tag FROM goods_movement WHERE move_user like '%{mover}%')"
                else:
                    condition_query = f"WHERE goods_movement.goods_tag IN (SELECT goods_movement.goods_tag FROM goods_movement WHERE move_user like '%{mover}%')"
            
            if 'approveUserName' in params:
                approver = params['approveUserName']
                if condition_query:
                    condition_query += f" and goods_movement.goods_tag IN (SELECT goods_movement.goods_tag FROM goods_movement WHERE approver_user like '%{approver}%')"
                else:
                    condition_query = f"WHERE goods_movement.goods_tag IN (SELECT goods_movement.goods_tag FROM goods_movement WHERE approver_user like '%{approver}%')"

            if condition_query:
                condition_query = condition_query + ' ORDER BY export_date DESC'
                query = f"SELECT goods.goods_tag, part_number, bl_number, origin_name, (SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, export_date, from_office_tag, to_office_tag, goods_movement.register_type, move_user, approver_user, goods_movement.description, first_cost FROM goods, goods_movement " + condition_query + limit_query + ';'
            else:
                condition_query = ' ORDER BY export_date DESC ORDER BY export_date DESC'
                query = f"SELECT goods.goods_tag, part_number, bl_number, origin_name, (SELECT brand.brand_name FROM brand WHERE goods.brand_tag = brand.brand_tag) as brand, category_tag, office_tag, supplier_tag, color, season, sex, size, material, stocking_date, import_date, sale_date, cost, regular_cost, sale_cost, discount_cost, management_cost, export_date, from_office_tag, to_office_tag, goods_movement.register_type, move_user, approver_user, goods_movement.description, first_cost FROM goods, goods_movement " + condition_query + limit_query + ';'
            mysql_cursor.execute(query)
            goods_rows = mysql_cursor.fetchall()

            send_data['table'] = dict()
            send_data['table']['column'] = ['검색 번호','출고일','출발 영업처','도착 영업처','입고일','수입일','공급처유형','공급처','BL번호','시즌','이미지','브랜드','상품종류','품번','Tag_no','성별','색상','소재','사이즈','원산지','입력방식','출고자','승인자','메모','cost','원가','정상판매가','판매가','특별할인가']
            send_data['table']['rows'] = list()

            for index, goods_row in enumerate(goods_rows):
                data = list()
                tag = goods_row[0]
                data.append(start+index+1)
                data.append(goods_row[21])
                
                from_office_tag = goods_row[22]
                to_office_tag = goods_row[23]
                query = f"SELECT office_name FROM office WHERE office_tag = {from_office_tag};"
                mysql_cursor.execute(query)
                office_row = mysql_cursor.fetchone()
                data.append(office_row[0])

                query = f"SELECT office_name FROM office WHERE office_tag = {to_office_tag};"
                mysql_cursor.execute(query)
                office_row = mysql_cursor.fetchone()
                data.append(office_row[0])

                data.append(goods_row[13])
                data.append(goods_row[14])

                supplier_tag = goods_row[7]
                query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = '{supplier_tag}';"
                mysql_cursor.execute(query)
                supplier_row = mysql_cursor.fetchone()
                #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
                supplier_type = int(supplier_row[1])
                if supplier_type == 1:
                    data.append('위탁')
                elif supplier_type == 2:
                    data.append('사입')
                elif supplier_type == 3:
                    data.append('직수입')
                elif supplier_type == 4:
                    data.append('미입고')
                data.append(supplier_row[0])

                data.append(goods_row[2])
                data.append(goods_row[9])
                
                query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{tag}';"
                mysql_cursor.execute(query)
                image_row = mysql_cursor.fetchone()
                if image_row:
                    data.append(image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/'))
                else:
                    data.append(None)

                data.append(goods_row[4])
                
                category_tag = goods_row[5]
                query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
                mysql_cursor.execute(query)
                category_row = mysql_cursor.fetchone()
                data.append(category_row[0])

                data.append(goods_row[1])
                data.append(tag)
                
                sex = int(goods_row[10])
                if sex == 0:
                    data.append('공용')
                elif sex == 1:
                    data.append('남성')
                else:
                    data.append('여성')

                data.append(goods_row[8])
                data.append(goods_row[12])
                data.append(goods_row[11])
                data.append(goods_row[3])
                
                register_type = int(goods_row[24])
                if register_type == 1:
                    data.append('엑셀입력')
                elif register_type == 2:
                    data.append('일괄입력')
                else:
                    data.append('직접입력')

                data.append(goods_row[25])
                data.append(goods_row[26])
                data.append(goods_row[27])
                data.append(goods_row[16])
                data.append(goods_row[28])
                data.append(goods_row[17])
                data.append(goods_row[18])
                data.append(goods_row[19])

                send_data['table']['rows'].append(data)

            if condition_query:
                query = f"SELECT count(*) FROM goods, goods_movement " + condition_query + ';'
            else:
                query = f"SELECT count(*) FROM goods, goods_movement;"
            mysql_cursor.execute(query)
            count_row = mysql_cursor.fetchone()

            send_data['result'] = 'SUCCESS'
            send_data['totalPage'] = int(int(count_row[0])/int(limit)) + 1
            send_data['totalMove'] = int(count_row[0])

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    elif flask.request.method == 'POST':
        try:
            request_body = json.loads(request.get_data())
            if not 'approveType' in request_body:
                send_data = {"result": "승인 방식이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'goodsTagList' in request_body:
                send_data = {"result": "상품 tag가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            approveType = request_body['approveType']
            goodsTagList = request_body['goodsTagList']

            for goods_tag in goodsTagList:
                query = f"SELECT approver_user, to_office_tag FROM goods_movement WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)
                approver_row = mysql_cursor.fetchone()
                approver_name = approver_row[0]
                to_office_tag = approver_row[1]
                
                query = f"select MAX(goods_history_index) FROM goods_history WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)
                index_row = mysql_cursor.fetchone()
                if not index_row:
                    index = 1
                elif not index_row[0]:
                    index = 1
                else:
                    index = index_row[0] + 1

                query = f"INSERT INTO goods_history(goods_tag, goods_history_index, name, status, update_method, user_id, update_date) "
                query += f"VALUES ('{goods_tag}',{index},'출고승인',4,{approveType},'{approver_name}',CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)

                query = f"UPDATE goods SET goods.status = 4, office_tag = {to_office_tag} WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)

                query = f"UPDATE goods_movement SET goods_movement.status = 1 WHERE goods_tag = '{goods_tag}';"
                mysql_cursor.execute(query)

            send_data['result'] = "SUCCESS"
            send_data['tags'] = goodsTagList

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#영업소 출고 현황 리스트 조회
@app.route('/status/office', methods=['GET'])
def statusOfficeList():
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
            condition_query = None

            if 'startDate' in params:
                startDate = params['startDate']
                if condition_query:
                    condition_query = condition_query + f" and export_date >= '{startDate}'"
                else:
                    condition_query = f"WHERE export_date >= '{startDate}'"
            if 'endDate' in params:
                endDate = params['endDate']
                if condition_query:
                    condition_query = condition_query + f" and export_date <= '{endDate}'"
                else:
                    condition_query = f"WHERE export_date <= '{endDate}'"
        
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
                        condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE {brand_query})"
                    else:
                        condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE {brand_query})"
        
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
                        condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE {category_query})"
                    else:
                        condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE {category_query})"

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
                        condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE {sex_query})"
                    else:
                        condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE {sex_query})"

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
                        condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE {origin_query})"
                    else:
                        condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE {origin_query})"

            if 'fromOfficeTagList' in params:
                officeTags = request.args.getlist('fromOfficeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or from_office_tag = '{officeTag}'"
                    else:
                        office_query = f"from_office_tag = '{officeTag}'"
                if office_query:
                    if condition_query:
                        condition_query = condition_query + f" and ({office_query})"
                    else:
                        condition_query = f"WHERE ({office_query})"
            
            if 'toOfficeTagList' in params:
                officeTags = request.args.getlist('toOfficeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or to_office_tag = '{officeTag}'"
                    else:
                        office_query = f"to_office_tag = '{officeTag}'"
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
                            condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE part_number like '%{searchContent}%')"
                        else:
                            condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE part_number like '%{searchContent}%')"
                    elif searchType == 1:
                        if condition_query:
                            condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE goods.goods_tag like '%{searchContent}%')"
                        else:
                            condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE goods.goods_tag like '%{searchContent}%')"
                    elif searchType == 2:
                        if condition_query:
                            condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE color like '%{searchContent}%')"
                        else:
                            condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE color like '%{searchContent}%')"
                    elif searchType == 3:
                        if condition_query:
                            condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE material like '%{searchContent}%')"
                        else:
                            condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE material like '%{searchContent}%')"
                    else:
                        if condition_query:
                            condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods WHERE size like '%{searchContent}%')"
                        else:
                            condition_query = f"WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE size like '%{searchContent}%')"
            
            if 'approve' in params:
                approve = int(params['approve'])
                if approve < 0 or approve > 1:
                    send_data = {"result": "승인 여부가 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if approve == 0:
                    approve_status = 0
                else:
                    approve_status = 1
                if condition_query:
                    condition_query += f" and goods_movement.status = {approve_status}"
                else:
                    condition_query = f"WHERE goods_movement.status = {approve_status}"

            if condition_query:
                condition_query = condition_query + ' GROUP BY export_date, from_office_tag, to_office_tag ORDER BY export_date DESC'
                query = f"SELECT export_date, from_office_tag, to_office_tag, count(*), count(case when goods_movement.status = 1 then 1 end) as approveCount, count(case when goods_movement.status = 0 then 1 end) as unApproveCount FROM goods_movement " + condition_query + limit_query + ';'
            else:
                condition_query = ' GROUP BY export_date, from_office_tag, to_office_tag ORDER BY export_date DESC'
                query = f"SELECT export_date, from_office_tag, to_office_tag, count(*), count(case when goods_movement.status = 1 then 1 end) as approveCount, count(case when goods_movement.status = 0 then 1 end) as unApproveCount FROM goods_movement " + condition_query + limit_query + ';'
            print(query)
            mysql_cursor.execute(query)
            status_rows = mysql_cursor.fetchall()
            
            send_data['table'] = dict()
            send_data['table']['column'] = ['검색 번호','출고일','출발 영업처','fromOfficeTag','도착 영업처','toOfficeTag','출고건수','승인건수','미승인건수']
            send_data['table']['rows'] = list()

            for index, status_row in enumerate(status_rows):
                data = list()
                data.append(start+index+1)

                data.append(status_row[0])

                fromOfficeTag  = status_row[1]
                toOfficeTag     = status_row[2]

                query = f"SELECT office_name FROM office WHERE office_tag = {fromOfficeTag};"
                mysql_cursor.execute(query)
                from_office_row = mysql_cursor.fetchone()
                data.append(from_office_row[0])
                data.append(fromOfficeTag)

                query = f"SELECT office_name FROM office WHERE office_tag = {toOfficeTag};"
                mysql_cursor.execute(query)
                to_office_row = mysql_cursor.fetchone()
                data.append(to_office_row[0])
                data.append(toOfficeTag)

                data.append(status_row[3])
                data.append(status_row[4])
                data.append(status_row[5])

                send_data['table']['rows'].append(data)

           
            query = f"SELECT count(*), count(case when goods_movement.status = 1 then 1 end) as approveCount, count(case when goods_movement.status = 0 then 1 end) as unApproveCount FROM goods_movement " + condition_query + ';'
            mysql_cursor.execute(query)
            count_rows = mysql_cursor.fetchall()
            send_data['totalResult'] = len(count_rows)
            totalMove = 0
            totalApprove = 0
            totalUnapprove = 0

            for count_row in count_rows:
                totalMove += int(count_row[0])
                totalApprove += int(count_row[1])
                totalUnapprove += int(count_row[2])

            send_data['result'] = 'SUCCESS'
            send_data['totalPage'] = int((len(count_rows))/int(limit)) + 1
            send_data['totalMove'] = totalMove
            send_data['totalApprove'] = totalApprove
            send_data['totalUnapprove'] = totalUnapprove

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#영업소 출고 현황 상세 조회
@app.route('/status/office/detail', methods=['GET'])
def statusOfficeDetailList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        try:
            params = request.args.to_dict()
            if not 'exportDate' in params:
                send_data = {"result": "출고일이 지정하지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'fromOfficeTag' in params:
                send_data = {"result": "출발 영업처 tag가 지정하지 않았습니다"}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'toOfficeTag' in params:
                send_data = {"result": "도착 영업처 tag가 지정하지 않았습니다"}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            export_date = params['exportDate']
            from_office_tag = params['fromOfficeTag']
            to_office_tag = params['toOfficeTag']

            send_data['exportDate'] = export_date
            
            query = f"SELECT stocking_date, import_date, season, part_number, goods_tag, (SELECT brand_name FROM brand WHERE brand.brand_tag = goods.brand_tag) as brand, (SELECT category_name FROM category WHERE category.category_tag = goods.category_tag), sex, color, material, size, origin_name, supplier_tag, goods.status, cost, first_cost, regular_cost, department_store_cost, event_cost, outlet_cost, sale_cost, discount_cost, description, (SELECT move_user FROM goods_movement WHERE goods_movement.goods_tag = goods.goods_tag) as mover, (SELECT goods_movement.status FROM goods_movement WHERE goods_movement.goods_tag = goods.goods_tag) as move_status, (SELECT approver_user FROM goods_movement WHERE goods_movement.goods_tag = goods.goods_tag) as approver, register_date FROM goods WHERE goods_tag IN (SELECT goods_tag FROM goods_movement WHERE export_date = '{export_date}' and from_office_tag = {from_office_tag} and to_office_tag = {to_office_tag});"
            mysql_cursor.execute(query)
            status_rows = mysql_cursor.fetchall()
            
            send_data['table'] = dict()
            send_data['table']['column'] = ['검색 번호','출고일','입고일','수입일','이미지','시즌','품번','태그번호','브랜드','상품종류','성별','색상','소재','사이즈','원산지','공급처 유형','공급처','출발영업소','도착영업소','상품상태','COST','원가','정상 판매가','백화점 판매가','행사 판매가','아울렛 판매가','특별 할인가','메모','출고요청자','승인여부','승인자']
            send_data['table']['rows'] = list()

            for index, status_row in enumerate(status_rows):
                data = list()
                data.append(index+1)
                data.append(export_date)
                data.append(status_row[0])
                data.append(status_row[1])

                goodsTag = status_row[4]

                query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{goodsTag}';"
                mysql_cursor.execute(query)
                image_row = mysql_cursor.fetchone()
                if image_row:
                    data.append(image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/'))
                else:
                    data.append(None)

                data.append(status_row[2])
                data.append(status_row[3])
                data.append(goodsTag)                
                data.append(status_row[5])
                data.append(status_row[6])
                sex = int(status_row[7])
                if sex == 0:
                    data.append('공용')
                elif sex == 1:
                    data.append('남성')
                else:
                    data.append('여성')

                data.append(status_row[8])
                data.append(status_row[9])
                data.append(status_row[10])
                data.append(status_row[11])

                supplier_tag = status_row[12]
                query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = '{supplier_tag}';"
                mysql_cursor.execute(query)
                supplier_row = mysql_cursor.fetchone()
                #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
                supplier_type = int(supplier_row[1])
                if supplier_type == 1:
                    data.append('위탁')
                elif supplier_type == 2:
                    data.append('사입')
                elif supplier_type == 3:
                    data.append('직수입')
                elif supplier_type == 4:
                    data.append('미입고')
                data.append(supplier_row[0])

                query = f"SELECT from_office_tag, to_office_tag FROM goods_movement WHERE goods_tag = '{goodsTag}'"
                mysql_cursor.execute(query)
                office_tag_row = mysql_cursor.fetchone()
                fromOfficeTag = office_tag_row[0]
                toOfficeTag = office_tag_row[1]

                query = f"SELECT office_name FROM office WHERE office_tag = {fromOfficeTag};"
                mysql_cursor.execute(query)
                from_office_row = mysql_cursor.fetchone()
                data.append(from_office_row[0])
                send_data['fromOffice'] = from_office_row[0]

                query = f"SELECT office_name FROM office WHERE office_tag = {toOfficeTag};"
                mysql_cursor.execute(query)
                to_office_row = mysql_cursor.fetchone()
                data.append(to_office_row[0])
                send_data['toOffice'] = to_office_row[0]

                goods_status = status_row[13]
                if goods_status == 1:
                    data.append('스크래치')
                elif goods_status == 2:
                    data.append('판매불가')
                elif goods_status == 3:
                    data.append('폐기')
                elif goods_status == 4:
                    data.append('정상재고')
                elif goods_status == 5:
                    data.append('분실')
                elif goods_status == 6:
                    data.append('정산대기')
                elif goods_status == 7:
                    data.append('분배대기')
                elif goods_status == 8:
                    data.append('회수완료')
                elif goods_status == 9:
                    data.append('수선중')
                elif goods_status == 10:
                    data.append('반품정산대기')
                elif goods_status == 11:
                    data.append('판매완료')
                elif goods_status == 12:
                    data.append('출고승인대기')
                elif goods_status == 13:
                    data.append('고객반송대기')

                data.append(status_row[14])
                data.append(status_row[15])
                data.append(status_row[16])
                data.append(status_row[17])
                data.append(status_row[18])
                data.append(status_row[19])
                data.append(status_row[20])
                data.append(status_row[21])
                data.append(status_row[22])
                data.append(status_row[23])
                move_status= int(status_row[24])
                if move_status == 0:
                    data.append('NO')
                else:
                    data.append('YES')
                data.append(status_row[25])

                send_data['table']['rows'].append(data)

            query = f"SELECT count(*), count(case when goods_movement.status = 1 then 1 end) as approveCount, count(case when goods_movement.status = 0 then 1 end) as unApproveCount FROM goods_movement WHERE export_date = '{export_date}' and from_office_tag = {from_office_tag} and to_office_tag = {to_office_tag};"
            mysql_cursor.execute(query)
            count_row = mysql_cursor.fetchone()
            send_data['totalMove'] = count_row[0]
            send_data['totalApprove'] = count_row[1]
            send_data['totalUnapprove'] = count_row[2]
            send_data['result'] = 'SUCCESS'

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#품번 출고 현황 리스트 조회
@app.route('/status/partNumber', methods=['GET'])
def statusPartNumberList():
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
                        condition_query = f" WHERE {dateString} >= '{startDate}'"
                if 'endDate' in params:
                    endDate = params['endDate']
                    if condition_query:
                        condition_query = condition_query + f" and {dateString} <= '{endDate}'"
                    else:
                       condition_query = f" WHERE {dateString} <= '{endDate}'"
        
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
                        condition_query = f" WHERE ({brand_query})"
        
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
                        condition_query = f" WHERE ({category_query})"

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
                        condition_query = condition_query + f" and {origin_query}"
                    else:
                        condition_query = f" WHERE {origin_query}"

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
                        condition_query = f" WHERE supplier_tag IN (SELECT supplier_tag FROM supplier WHERE {supplier_type_query})"
        
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
                        condition_query = f" WHERE ({supplier_query})"

            if 'fromOfficeTagList' in params:
                officeTags = request.args.getlist('fromOfficeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or from_office_tag = '{officeTag}'"
                    else:
                        office_query = f"from_office_tag = '{officeTag}'"
                if office_query:
                    if condition_query:
                        condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods_movement WHERE {office_query})"
                    else:
                        condition_query = f" WHERE goods_tag IN (SELECT goods_tag FROM goods_movement WHERE {office_query})"
            
            if 'toOfficeTagList' in params:
                officeTags = request.args.getlist('toOfficeTagList')
                office_query = None
                for officeTag in officeTags:
                    if office_query:
                        office_query = office_query + f" or to_office_tag = '{officeTag}'"
                    else:
                        office_query = f"to_office_tag = '{officeTag}'"
                if office_query:
                    if condition_query:
                        condition_query = condition_query + f" and goods_tag IN (SELECT goods_tag FROM goods_movement WHERE {office_query})"
                    else:
                        condition_query = f" WHERE goods_tag IN (SELECT goods_tag FROM goods_movement WHERE {office_query})"
        
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
                            condition_query = f" WHERE part_number like '%{searchContent}%'"
                    elif searchType == 1:
                        if condition_query:
                            condition_query = condition_query + f" and goods_tag like '%{searchContent}%'"
                        else:
                            condition_query = f" WHERE goods_tag like '%{searchContent}%'"
                    elif searchType == 2:
                        if condition_query:
                            condition_query = condition_query + f" and color like '%{searchContent}%'"
                        else:
                            condition_query = f" WHERE gcolor like '%{searchContent}%'"
                    elif searchType == 3:
                        if condition_query:
                            condition_query = condition_query + f" and material like '%{searchContent}%'"
                        else:
                            condition_query = f" WHERE material like '%{searchContent}%'"
                    else:
                        if condition_query:
                            condition_query = condition_query + f" and size like '%{searchContent}%'"
                        else:
                            condition_query = f" WHERE size like '%{searchContent}%'"
            
            if 'approve' in params:
                approve = int(params['approve'])
                if approve < 0 or approve >1:
                    send_data = {"result": "승인 여부가 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if approve == 0:
                    approve_status = 0
                else:
                    approve_status = 1
                if condition_query:
                    condition_query += f" and goods_tag IN (SELECT goods_tag FROM goods_movement WHERE goods_movement.status = {approve_status})"
                else:
                    condition_query = f" WHERE goods_tag IN (SELECT goods_tag FROM goods_movement WHERE goods_movement.status = {approve_status})"

            if condition_query:
                condition_query = condition_query + ' and goods_tag IN (SELECT goods_tag FROM goods_movement) GROUP BY stocking_date, part_number, supplier_tag ORDER BY stocking_date DESC'
                query = f"SELECT (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_type, (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_name, any_value(brand_tag), any_value(category_tag), part_number, stocking_date, any_value(color), any_value(material), any_value(origin_name), avg(cost), avg(first_cost), avg(regular_cost), avg(department_store_cost), avg(event_cost), avg(outlet_cost), avg(sale_cost), avg(discount_cost), avg(management_cost)  FROM goods " + condition_query + limit_query + ';'
            else:
                condition_query = ' WHERE goods_tag IN (SELECT goods_tag FROM goods_movement) GROUP BY stocking_date, part_number, supplier_tag ORDER BY stocking_date DESC'
                query = f"SELECT (SELECT supplier_type FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_type, (SELECT supplier_name FROM supplier WHERE supplier.supplier_tag = goods.supplier_tag) as supplier_name, any_value(brand_tag), any_value(category_tag), part_number, stocking_date, any_value(color), any_value(material), any_value(origin_name), avg(cost), avg(first_cost), avg(regular_cost), avg(department_store_cost), avg(event_cost), avg(outlet_cost), avg(sale_cost), avg(discount_cost), avg(management_cost)  FROM goods " + condition_query + limit_query + ';'
            mysql_cursor.execute(query)
            status_rows = mysql_cursor.fetchall()
            
            send_data['table'] = dict()
            send_data['table']['column'] = ['검색 번호','공급처 유형','공급처','브랜드','상품종류','이미지','품번','입고일','색상','소재','원산지','총 출고 건수','출고영업소 / 건수','총 승인 건수','도착영업소 / 승인','총 미승인 건수','도착영업소 / 미승인','COST','원가','정상 판매가','판매가','백화점 판매가','행사 판매가','아울렛 판매가','특별 할인가','관리원가']
            send_data['table']['rows'] = list()

            for index,status_row in enumerate(status_rows):
                data = list()
                partNumber = status_row[4]
                data.append(start+index+1)
                data.append(status_row[0])
                data.append(status_row[1])

                brand_tag = status_row[2]
                query = f"SELECT brand_name FROM brand WHERE brand_tag = '{brand_tag}';"
                mysql_cursor.execute(query)
                brand_row = mysql_cursor.fetchone()
                data.append(brand_row[0])

                category_tag = status_row[3]
                query = f"SELECT category_name FROM category WHERE category_tag = '{category_tag}';"
                mysql_cursor.execute(query)
                category_row = mysql_cursor.fetchone()
                data.append(category_row[0])

                query = f"SELECT image_path FROM goods_image WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE part_number = '{partNumber}');"
                mysql_cursor.execute(query)
                image_row = mysql_cursor.fetchone()
                if image_row:
                    data.append(image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/'))
                else:
                    data.append(None)

                data.append(partNumber)

                data.append(status_row[5])
                data.append(status_row[6])
                data.append(status_row[7])
                data.append(status_row[8])

                query = f"SELECT status, (SELECT office_name FROM office WHERE office_tag = from_office_tag) as from_office, (SELECT office_name FROM office WHERE office_tag = to_office_tag) as to_office FROM goods_movement WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE part_number = '{partNumber}' and stocking_date = '{status_row[5]}');"
                mysql_cursor.execute(query)
                goods_rows = mysql_cursor.fetchall()

                data.append(len(goods_rows))

                approveCount = 0
                unApproveCount = 0
                formOfficeDict = dict()
                toOfficeApproveDict = dict()
                toOfficeUnApproveDict = dict()

                for goods_row in goods_rows:
                    move_status = goods_row[0]
                    from_office = goods_row[1]
                    to_office = goods_row[2]
                    if from_office in formOfficeDict:
                        formOfficeDict[from_office] += 1
                    else:
                        formOfficeDict[from_office] = 1
                    if move_status == 0:
                        unApproveCount += 1
                        if to_office in toOfficeUnApproveDict:
                            toOfficeUnApproveDict[to_office] += 1
                        else:
                            toOfficeUnApproveDict[to_office] = 1
                    else:
                        approveCount += 1
                        if to_office in toOfficeApproveDict:
                            toOfficeApproveDict[to_office] += 1
                        else:
                            toOfficeApproveDict[to_office] = 1

                fromOffice = None
                for key in formOfficeDict:
                    if not fromOffice:
                        fromOffice = f"{key}\t/ {formOfficeDict[key]}"
                    else:
                        fromOffice = fromOffice + f"\n{key}\t/ {formOfficeDict[key]}"
                data.append(fromOffice)

                data.append(approveCount)

                toOfficeApprove = None
                for key in toOfficeApproveDict:
                    if not toOfficeApprove:
                        toOfficeApprove = f"{key}\t/ {toOfficeApproveDict[key]}"
                    else:
                        toOfficeApprove = toOfficeApprove + f"\n{key}\t/ {toOfficeApproveDict[key]}"
                data.append(toOfficeApprove)
                
                data.append(unApproveCount)

                toOfficeUnApprove = None
                for key in toOfficeUnApproveDict:
                    if not toOfficeUnApprove:
                        toOfficeUnApprove = f"{key}\t/ {toOfficeUnApproveDict[key]}"
                    else:
                        toOfficeUnApprove = toOfficeUnApprove + f"\n{key}\t/ {toOfficeUnApproveDict[key]}"
                data.append(toOfficeUnApprove)

                data.append(status_row[9])
                data.append(status_row[10])
                data.append(status_row[11])
                data.append(status_row[15])
                data.append(status_row[12])
                data.append(status_row[13])
                data.append(status_row[14])
                data.append(status_row[16])
                data.append(status_row[17])

                send_data['table']['rows'].append(data)

           
            query = f"SELECT count(*), count(case when goods.status != 12 then 1 end) as approveCount, count(case when goods.status = 12 then 1 end) as unApproveCount, sum(cost), sum(first_cost), sum(regular_cost), sum(department_store_cost), sum(event_cost), sum(outlet_cost), sum(sale_cost), sum(discount_cost), sum(management_cost) FROM goods " + condition_query + ';'
            mysql_cursor.execute(query)
            count_rows = mysql_cursor.fetchall()
            send_data['totalResult'] = len(count_rows)
            send_data['totalMove'] = 0
            send_data['totalApprove'] = 0
            send_data['totalUnapprove'] = 0
            send_data['totalCost'] = 0
            send_data['totalFirstCost'] = 0
            send_data['totalRegularCost'] = 0
            send_data['totalDepartmentStoreCost'] = 0
            send_data['totalEventCost'] = 0
            send_data['totalOutletCost'] = 0
            send_data['totalSaleCost'] = 0
            send_data['totalDiscountCost'] = 0
            send_data['totalManagementCost'] = 0

            for count_row in count_rows:
                send_data['totalMove'] += count_row[0]
                send_data['totalApprove'] += count_row[1]
                send_data['totalUnapprove'] += count_row[2]
                send_data['totalCost'] += count_row[3]
                send_data['totalFirstCost'] += count_row[4]
                send_data['totalRegularCost'] += count_row[5]
                send_data['totalDepartmentStoreCost'] += count_row[6]
                send_data['totalEventCost'] += count_row[7]
                send_data['totalOutletCost'] += count_row[8]
                send_data['totalSaleCost'] += count_row[9]
                send_data['totalDiscountCost'] += count_row[10]
                send_data['totalManagementCost'] += count_row[11]

            send_data['result'] = 'SUCCESS'
            send_data['totalPage'] = int((len(count_rows))/int(limit)) + 1

        except Exception as e:
            send_data = {"result": f"Error : {e}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#품번 출고 현황 상세 조회
@app.route('/status/partNumber/detail', methods=['GET'])
def statusPartNumberDetailList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        try:
            params = request.args.to_dict()
            if not 'stockingDate' in params:
                send_data = {"result": "입고일이 지정하지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'partNumber' in params:
                send_data = {"result": "품번이 지정하지 않았습니다"}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            stocking_date = params['stockingDate']
            part_number = params['partNumber']

            send_data['stockingDate'] = stocking_date
            send_data['partNumber'] = part_number
            
            query = f"SELECT (SELECT export_date FROM goods_movement WHERE goods_movement.goods_tag = goods.goods_tag) as export_date, stocking_date, import_date, season, part_number, goods_tag, (SELECT brand_name FROM brand WHERE brand.brand_tag = goods.brand_tag) as brand, (SELECT category_name FROM category WHERE category.category_tag = goods.category_tag), sex, color, material, size, origin_name, supplier_tag, status, cost, first_cost, regular_cost, department_store_cost, event_cost, outlet_cost, sale_cost, discount_cost, description, (SELECT move_user FROM goods_movement WHERE goods_movement.goods_tag = goods.goods_tag) as mover, (SELECT goods_movement.status FROM goods_movement WHERE goods_movement.goods_tag = goods.goods_tag) as move_status, (SELECT approver_user FROM goods_movement WHERE goods_movement.goods_tag = goods.goods_tag) as approver, register_date FROM goods WHERE stocking_date = '{stocking_date}' and part_number = '{part_number}';"
            mysql_cursor.execute(query)
            status_rows = mysql_cursor.fetchall()
            
            send_data['table'] = dict()
            send_data['table']['column'] = ['검색 번호','출고일','입고일','수입일','이미지','시즌','품번','태그번호','브랜드','상품종류','성별','색상','소재','사이즈','원산지','공급처 유형','공급처','출발영업소','도착영업소','상품상태','COST','원가','정상 판매가','백화점 판매가','행사 판매가','아웃렛 판매가','특별할인가','메모','승인여부','승인자']
            send_data['table']['rows'] = list()

            for index, status_row in enumerate(status_rows):
                data = list()
                goodsTag = status_row[5]
                data.append(index+1)
                data.append(status_row[0])
                data.append(status_row[1])
                data.append(status_row[2])
                query = f"SELECT image_path FROM goods_image WHERE goods_tag = '{goodsTag}';"
                mysql_cursor.execute(query)
                image_row = mysql_cursor.fetchone()
                if image_row:
                    data.append(image_row[0].replace('/home/ubuntu/data/','http://52.79.206.187:19999/'))
                else:
                    data.append(None)
                
                data.append(status_row[3])
                data.append(status_row[4])
                data.append(goodsTag)
                
                data.append(status_row[6])
                data.append(status_row[7])

                sex = int(status_row[8])
                if sex == 0:
                    data.append('공용')
                elif sex == 1:
                    data.append('남성')
                else:
                    data.append('여성')

                data.append(status_row[9])
                data.append(status_row[10])
                data.append(status_row[11])
                data.append(status_row[12])

                supplier_tag = status_row[13]
                query = f"SELECT supplier_name, supplier_type FROM supplier WHERE supplier_tag = '{supplier_tag}';"
                mysql_cursor.execute(query)
                supplier_row = mysql_cursor.fetchone()
                #1:위탁, 2: 사입, 3: 직수입, 4: 미입고
                supplier_type = int(supplier_row[1])
                if supplier_type == 1:
                    data.append('위탁')
                elif supplier_type == 2:
                    data.append('사입')
                elif supplier_type == 3:
                    data.append('직수입')
                elif supplier_type == 4:
                    data.append('미입고')
                data.append(supplier_row[0])

                query = f"SELECT from_office_tag, to_office_tag FROM goods_movement WHERE goods_tag = '{goodsTag}';"
                mysql_cursor.execute(query)
                office_tag_row = mysql_cursor.fetchone()
                fromOfficeTag = office_tag_row[0]
                toOfficeTag = office_tag_row[1]

                query = f"SELECT office_name FROM office WHERE office_tag = {fromOfficeTag};"
                mysql_cursor.execute(query)
                from_office_row = mysql_cursor.fetchone()
                data.append(from_office_row[0])

                query = f"SELECT office_name FROM office WHERE office_tag = {toOfficeTag};"
                mysql_cursor.execute(query)
                to_office_row = mysql_cursor.fetchone()
                data.append(to_office_row[0])

                data.append(status_row[14])
                data.append(status_row[15])
                data.append(status_row[16])
                data.append(status_row[17])
                data.append(status_row[18])
                data.append(status_row[19])
                data.append(status_row[20])
                data.append(status_row[22])
                data.append(status_row[23])
                move_status= int(status_row[25])
                if move_status == 0:
                    data.append('NO')
                else:
                    data.append('YES')
                data.append(status_row[26])

                send_data['table']['rows'].append(data)

            if len(send_data['table']['rows']) > 0:
                send_data['brand'] = send_data['table']['rows'][0][8]
                send_data['category'] = send_data['table']['rows'][0][9]
                send_data['supplierName'] = send_data['table']['rows'][0][16]
            else:
                send_data['brand'] = None
                send_data['category'] = None
                send_data['supplierName'] = None

            query = f"SELECT count(*), count(case when goods_movement.status = 1 then 1 end) as approveCount, count(case when goods_movement.status = 0 then 1 end) as unApproveCount FROM goods_movement WHERE goods_tag IN (SELECT goods_tag FROM goods WHERE stocking_date = '{stocking_date}' and part_number = '{part_number}');"
            mysql_cursor.execute(query)
            count_row = mysql_cursor.fetchone()
            send_data['totalMove'] = count_row[0]
            send_data['totalApprove'] = count_row[1]
            send_data['totalUnapprove'] = count_row[2]
            send_data['result'] = 'SUCCESS'

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
        process_config = config['move_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"move_management.log"
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