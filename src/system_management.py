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

#브랜드 리스트 조회, 등록
@app.route('/brand', methods=['GET','POST'])
def brandApis():
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            params = request.args.to_dict()
            condition_query = None
            
            if 'useFlag' in params:
                useFlag = int(params['useFlag'])
                if useFlag < 0 or useFlag > 2:
                    send_data = {"result": "사용 여부의 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if useFlag == 1:
                    if condition_query:
                        condition_query = condition_query + " and use_flag = 1"
                    else:
                        condition_query = " WHERE use_flag = 1"
                elif useFlag == 2:
                    if condition_query:
                        condition_query = condition_query + " and use_flag != 1"
                    else:
                        condition_query = " WHERE use_flag != 1"

            if 'name' in params:
                name = params['name']
                if condition_query:
                    condition_query = condition_query + f" and brand_name like '%{name}%'"
                else:
                    condition_query = f" WHERE brand_name like '%{name}%'"

            if 'tag' in params:
                tag = params['tag']
                if condition_query:
                    condition_query = condition_query + f" and brand_tag like '%{tag}%'"
                else:
                    condition_query = f" WHERE brand_tag like '%{tag}%'"

            if 'sort' in params:
                if params['sort'] == 1:
                    if condition_query:
                        condition_query = condition_query + " ORDER BY brand_name"
                    else:
                        condition_query = " ORDER BY brand_name"
            if condition_query:
                query = f"SELECT brand_tag, brand_name, use_flag, description, user_id FROM brand" + condition_query + ';'
            else:
                query = f"SELECT brand_tag, brand_name, use_flag, description, user_id FROM brand;"
            mysql_cursor.execute(query)
            brand_rows = mysql_cursor.fetchall()
            
            brand_list = list()
            for brand_row in brand_rows:
                data = dict()
                data['tag'] = brand_row[0]
                data['name'] = brand_row[1]
                data['useFlag'] = brand_row[2]
                data['description'] = brand_row[3]
                data['userId'] = brand_row[4]
                brand_list.append(data)

            send_data['result'] = 'SUCCESS'
            send_data['list'] = brand_list

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            request_body = json.loads(request.get_data())
            if not 'tag' in request_body:
                send_data = {"result": "브랜드 tag가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'name' in request_body:
                send_data = {"result": "브랜드명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            tag = request_body['tag']
            name = request_body['name']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"SELECT count(*) FROM brand WHERE brand_tag = '{tag}';"
            mysql_cursor.execute(query)
            check_row = mysql_cursor.fetchone()
            if check_row[0] > 0:
                send_data = {"result": "이미 존재하는 브랜드 Tag 입니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"INSERT INTO brand(brand_tag,brand_name,use_flag,description,user_id,register_date) VALUES ('{tag}','{name}',{useFlag},'{description}','{userId}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = tag

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#브랜드 수정, 삭제
@app.route('/brand/<string:brandTag>', methods=['PUT','DELETE'])
def brandtDetailApis(brandTag):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    query = f"SELECT * FROM brand WHERE brand_tag = '{brandTag}';"
    mysql_cursor.execute(query)
    brand_row = mysql_cursor.fetchone()
    if not brand_row:
        send_data = {"result": "해당 브랜드 Tag는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'tag' in request_body:
                send_data = {"result": "브랜드 tag가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'name' in request_body:
                send_data = {"result": "브랜드명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            tag = request_body['tag']
            name = request_body['name']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"SELECT count(*) FROM brand WHERE brand_tag = '{tag}';"
            mysql_cursor.execute(query)
            check_row = mysql_cursor.fetchone()
            if check_row[0] > 0 and tag != brandTag:
                send_data = {"result": "이미 존재하는 브랜드 Tag 입니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"UPDATE brand SET brand_tag='{tag}',brand_name='{name}',use_flag={useFlag},description='{description}',user_id='{userId}',register_date=CURRENT_TIMESTAMP WHERE brand_tag = '{brandTag}';"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = tag

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    
    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:
            query = f"DELETE FROM brand WHERE brand_tag = '{brandTag}';"
            mysql_cursor.execute(query)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#상품종류 리스트 조회, 등록
@app.route('/category', methods=['GET','POST'])
def categoryApis():
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            params = request.args.to_dict()
            condition_query = None
            
            if 'useFlag' in params:
                useFlag = int(params['useFlag'])
                if useFlag < 0 or useFlag > 2:
                    send_data = {"result": "사용 여부의 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if useFlag == 1:
                    if condition_query:
                        condition_query = condition_query + " and use_flag = 1"
                    else:
                        condition_query = " WHERE use_flag = 1"
                elif useFlag == 2:
                    if condition_query:
                        condition_query = condition_query + " and use_flag != 1"
                    else:
                        condition_query = " WHERE use_flag != 1"

            if 'name' in params:
                name = params['name']
                if condition_query:
                    condition_query = condition_query + f" and category_name like '%{name}%'"
                else:
                    condition_query = f" WHERE category_name like '%{name}%'"

            if 'tag' in params:
                tag = params['tag']
                if condition_query:
                    condition_query = condition_query + f" and category_tag like '%{tag}%'"
                else:
                    condition_query = f" WHERE category_tag like '%{tag}%'"

            if 'sort' in params:
                if params['sort'] == 1:
                    if condition_query:
                        condition_query = condition_query + " ORDER BY category_name"
                    else:
                        condition_query = " ORDER BY category_name"

            if condition_query:
                query = f"SELECT category_tag, category_name, use_flag, description, user_id FROM category" + condition_query + ';'
            else:
                query = f"SELECT category_tag, category_name, use_flag, description, user_id FROM category;"
            mysql_cursor.execute(query)
            category_rows = mysql_cursor.fetchall()
            
            category_list = list()
            for category_row in category_rows:
                data = dict()
                data['tag'] = category_row[0]
                data['name'] = category_row[1]
                data['useFlag'] = category_row[2]
                data['description'] = category_row[3]
                data['userId'] = category_row[4]
                category_list.append(data)

            send_data['result'] = 'SUCCESS'
            send_data['list'] = category_list

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            request_body = json.loads(request.get_data())
            if not 'tag' in request_body:
                send_data = {"result": "상품종류 tag가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'name' in request_body:
                send_data = {"result": "상품종류명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            tag = request_body['tag']
            name = request_body['name']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"SELECT count(*) FROM category WHERE category_tag = '{tag}';"
            mysql_cursor.execute(query)
            check_row = mysql_cursor.fetchone()
            if check_row[0] > 0:
                send_data = {"result": "이미 존재하는 상품종류 Tag 입니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"INSERT INTO category(category_tag,category_name,use_flag,description,user_id,register_date) VALUES ('{tag}','{name}',{useFlag},'{description}','{userId}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = tag

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#상품종류 수정, 삭제
@app.route('/category/<string:categoryTag>', methods=['PUT','DELETE'])
def categorytDetailApis(categoryTag):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    query = f"SELECT * FROM category WHERE category_tag = '{categoryTag}';"
    mysql_cursor.execute(query)
    category_row = mysql_cursor.fetchone()
    if not category_row:
        send_data = {"result": "해당 상품종류 Tag는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'tag' in request_body:
                send_data = {"result": "상품종류 tag가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'name' in request_body:
                send_data = {"result": "상품종류명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            tag = request_body['tag']
            name = request_body['name']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"SELECT count(*) FROM category WHERE category_tag = '{tag}';"
            mysql_cursor.execute(query)
            check_row = mysql_cursor.fetchone()
            if check_row[0] > 0 and tag != categoryTag:
                send_data = {"result": "이미 존재하는 상품종류 Tag 입니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"UPDATE category SET category_tag='{tag}',category_name='{name}',use_flag={useFlag},description='{description}',user_id='{userId}',register_date=CURRENT_TIMESTAMP WHERE category_tag = '{categoryTag}';"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = tag

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    
    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:
            query = f"DELETE FROM category WHERE category_tag = '{categoryTag}';"
            mysql_cursor.execute(query)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#원산지 리스트 조회, 등록
@app.route('/origin', methods=['GET','POST'])
def originApis():
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            params = request.args.to_dict()
            condition_query = None
            
            if 'useFlag' in params:
                useFlag = int(params['useFlag'])
                if useFlag < 0 or useFlag > 2:
                    send_data = {"result": "사용 여부의 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if useFlag == 1:
                    if condition_query:
                        condition_query = condition_query + " and use_flag = 1"
                    else:
                        condition_query = " WHERE use_flag = 1"
                elif useFlag == 2:
                    if condition_query:
                        condition_query = condition_query + " and use_flag != 1"
                    else:
                        condition_query = " WHERE use_flag != 1"

            if 'name' in params:
                name = params['name']
                if condition_query:
                    condition_query = condition_query + f" and origin_name like '%{name}%'"
                else:
                    condition_query = f" WHERE origin_name like '%{name}%'"

            if condition_query:
                query = f"SELECT origin_name, use_flag, description, user_id FROM origin" + condition_query + ';'
            else:
                query = f"SELECT origin_name, use_flag, description, user_id FROM origin;"
            mysql_cursor.execute(query)
            origin_rows = mysql_cursor.fetchall()
            
            origin_list = list()
            for origin_row in origin_rows:
                data = dict()
                data['name'] = origin_row[0]
                data['useFlag'] = origin_row[1]
                data['description'] = origin_row[2]
                data['userId'] = origin_row[3]
                origin_list.append(data)

            send_data['result'] = 'SUCCESS'
            send_data['list'] = origin_list

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            request_body = json.loads(request.get_data())
            if not 'name' in request_body:
                send_data = {"result": "원산지명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            name = request_body['name']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"SELECT count(*) FROM origin WHERE origin_name = '{name}';"
            mysql_cursor.execute(query)
            check_row = mysql_cursor.fetchone()
            if check_row[0] > 0:
                send_data = {"result": "이미 존재하는 원산지입니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"INSERT INTO origin(origin_name,use_flag,description,user_id,register_date) VALUES ('{name}',{useFlag},'{description}','{userId}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = name

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#원산지 수정, 삭제
@app.route('/origin/<string:originName>', methods=['PUT','DELETE'])
def originDetailApis(originName):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    query = f"SELECT * FROM origin WHERE origin_name = '{originName}';"
    mysql_cursor.execute(query)
    origin_row = mysql_cursor.fetchone()
    if not origin_row:
        send_data = {"result": "해당 원산지 이름은 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'name' in request_body:
                send_data = {"result": "상품종류명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            name = request_body['name']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"SELECT count(*) FROM origin WHERE origin_name = '{originName}';"
            mysql_cursor.execute(query)
            check_row = mysql_cursor.fetchone()
            if check_row[0] > 0 and name != originName:
                send_data = {"result": "이미 존재하는 원산지입니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"UPDATE origin SET origin_name='{name}',use_flag={useFlag},description='{description}',user_id='{userId}',register_date=CURRENT_TIMESTAMP WHERE origin_name = '{originName}';"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = name

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    
    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:
            query = f"DELETE FROM origin WHERE origin_name = '{originName}';"
            mysql_cursor.execute(query)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#공급처 리스트 조회, 등록
@app.route('/supplier', methods=['GET','POST'])
def supplierApis():
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            params = request.args.to_dict()
            condition_query = None
            
            if 'useFlag' in params:
                useFlag = int(params['useFlag'])
                if useFlag < 0 or useFlag > 2:
                    send_data = {"result": "사용 여부의 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if useFlag == 1:
                    if condition_query:
                        condition_query = condition_query + " and use_flag = 1"
                    else:
                        condition_query = " WHERE use_flag = 1"
                elif useFlag == 2:
                    if condition_query:
                        condition_query = condition_query + " and use_flag != 1"
                    else:
                        condition_query = " WHERE use_flag != 1"

            if 'name' in params:
                name = params['name']
                if condition_query:
                    condition_query = condition_query + f" and supplier_name like '%{name}%'"
                else:
                    condition_query = f" WHERE supplier_name like '%{name}%'"

            if 'tag' in params:
                tag = params['tag']
                if condition_query:
                    condition_query = condition_query + f" and supplier_tag like '%{tag}%'"
                else:
                    condition_query = f" WHERE supplier_tag like '%{tag}%'"

            if 'type' in params:
                supplier_type = int(params['type'])
                if supplier_type < 0 or supplier_type > 4:
                    send_data = {"result": "공급처 유형의 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if supplier_type > 0:
                    if condition_query:
                        condition_query = condition_query + f" and supplier_type = {supplier_type}"
                    else:
                        condition_query = f" WHERE supplier_type = {supplier_type}"

            if 'sort' in params:
                if params['sort'] == 1:
                    if condition_query:
                        condition_query = condition_query + " ORDER BY supplier_name"
                    else:
                        condition_query = " ORDER BY supplier_name"

            if condition_query:
                query = f"SELECT supplier_tag, supplier_name, supplier_type, use_flag, description, user_id FROM supplier" + condition_query + ';'
            else:
                query = f"SELECT supplier_tag, supplier_name, supplier_type, use_flag, description, user_id FROM supplier;"
            mysql_cursor.execute(query)
            supplier_rows = mysql_cursor.fetchall()
            
            supplier_list = list()
            for supplier_row in supplier_rows:
                data = dict()
                data['tag'] = supplier_row[0]
                data['name'] = supplier_row[1]
                data['type'] = supplier_row[2]
                data['useFlag'] = supplier_row[3]
                data['description'] = supplier_row[4]
                data['userId'] = supplier_row[5]
                supplier_list.append(data)

            send_data['result'] = 'SUCCESS'
            send_data['list'] = supplier_list

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            request_body = json.loads(request.get_data())
            if not 'name' in request_body:
                send_data = {"result": "공급처 이름이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'type' in request_body:
                send_data = {"result": "공급처 유형이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            name = request_body['name']
            supplier_type = int(request_body['type'])
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            if supplier_type < 1 or supplier_type > 4:
                send_data = {"result": "공급처 유형은 1:위탁, 2: 사입, 3: 직수입, 4: 미입고로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"INSERT INTO supplier(supplier_name,supplier_type,use_flag,description,user_id,register_date) VALUES ('{name}',{supplier_type},{useFlag},'{description}','{userId}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            query = f"SELECT MAX(supplier_tag) FROM supplier;"
            mysql_cursor.execute(query)
            tag_row = mysql_cursor.fetchone()
            if not tag_row:
                tag = 1
            elif not tag_row[0]:
                tag = 1
            else:
                tag = tag_row[0]

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = str(tag)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#공급처 수정, 삭제
@app.route('/supplier/<int:supplierTag>', methods=['PUT','DELETE'])
def suppliertDetailApis(supplierTag):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    query = f"SELECT * FROM supplier WHERE supplier_tag = {supplierTag};"
    mysql_cursor.execute(query)
    supplier_row = mysql_cursor.fetchone()
    if not supplier_row:
        send_data = {"result": "해당 공급처 Tag는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'tag' in request_body:
                send_data = {"result": "공급처 Tag가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'type' in request_body:
                send_data = {"result": "공급처 유형이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'name' in request_body:
                send_data = {"result": "공급처명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            tag = request_body['tag']
            supplier_type = request_body['type']
            name = request_body['name']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            query = f"SELECT count(*) FROM supplier WHERE supplier_tag = {tag};"
            mysql_cursor.execute(query)
            check_row = mysql_cursor.fetchone()
            if check_row[0] > 0 and tag != supplierTag:
                send_data = {"result": "이미 존재하는 공급처 Tag입니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"UPDATE supplier SET supplier_tag = {tag}, supplier_name='{name}', supplier_type = {supplier_type},use_flag={useFlag},description='{description}',user_id='{userId}',register_date=CURRENT_TIMESTAMP WHERE supplier_tag = '{supplierTag}';"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = str(tag)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    
    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:
            query = f"DELETE FROM supplier WHERE supplier_tag = '{supplierTag}';"
            mysql_cursor.execute(query)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#영업소 리스트 조회, 등록
@app.route('/office', methods=['GET','POST'])
def officeApis():
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            params = request.args.to_dict()
            condition_query = ""
            
            if 'type' in params:
                officeType = int(params['type'])
                if officeType < 0 or officeType > 7:
                    send_data = {"result": "영업처 판매 유형 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if officeType != 0:
                    if condition_query: 
                        condition_query = condition_query + f" and office_tag IN (SELECT office_tag FROM office_selling_type WHERE type = {officeType})"
                    else:
                        condition_query = f" WHERE office_tag IN (SELECT office_tag FROM office_selling_type WHERE type = {officeType})"

            if 'useFlag' in params:
                useFlag = int(params['useFlag'])
                if useFlag < 0 or useFlag > 2:
                    send_data = {"result": "사용 여부의 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if useFlag == 1:
                    if condition_query: 
                        condition_query = condition_query + " and use_flag = 1"
                    else:
                        condition_query = " WHERE use_flag = 1"
                elif useFlag == 2:
                    if condition_query:
                        condition_query = condition_query + " and use_flag != 1"
                    else:
                        condition_query = " WHERE use_flag != 1"

            if 'officeName' in params:
                name = params['officeName']
                if condition_query:
                    condition_query = condition_query + f" and office_name like '%{name}%'"
                else:
                    condition_query = f" WHERE office_name like '%{name}%'"

            if 'registrationName' in params:
                name = params['registrationName']
                if condition_query:
                    condition_query = condition_query + f" and registration_name like '%{name}%'"
                else:
                    condition_query = f" WHERE registration_name like '%{name}%'"

            if 'phoneNumber' in params:
                phoneNumber = params['phoneNumber']
                if condition_query:
                    condition_query = condition_query + f" and phone_number like '%{phoneNumber}%'"
                else:
                    condition_query = f" WHERE phone_number like '%{phoneNumber}%'"

            if condition_query:
                query = f"SELECT office_tag, office_name, registration_number, registration_name, representative, phone_number, fax_number, use_flag, description, address, business_status, business_item, user_id FROM office" + condition_query + ';'
            else:
                query = f"SELECT office_tag, office_name, registration_number, registration_name, representative, phone_number, fax_number, use_flag, description, address, business_status, business_item, user_id FROM office;"
            mysql_cursor.execute(query)
            office_rows = mysql_cursor.fetchall()
            
            office_list = list()
            for office_row in office_rows:
                data = dict()
                data['tag'] = office_row[0]
                data['name'] = office_row[1]
                data['registrationNumber'] = office_row[2]
                data['registrationName'] = office_row[3]
                data['representative'] = office_row[4]
                data['phoneNumber'] = office_row[5]
                data['faxNumber'] = office_row[6]
                data['useFlag'] = office_row[7]
                data['description'] = office_row[8]
                data['address'] = office_row[9]
                data['businessStatus'] = office_row[10]
                data['businessItem'] = office_row[11]
                data['userId'] = office_row[12]

                query = f"SELECT type FROM office_selling_type WHERE office_tag = {data['tag']};"
                mysql_cursor.execute(query)
                selling_type_rows = mysql_cursor.fetchall()
                data['sellingType'] = list()
                for selling_type_row in selling_type_rows:
                    data['sellingType'].append(selling_type_row[0])

                query = f"SELECT type FROM office_cost_type WHERE office_tag = {data['tag']};"
                mysql_cursor.execute(query)
                cost_type_rows = mysql_cursor.fetchall()
                data['costType'] = list()
                for cost_type_row in cost_type_rows:
                    data['costType'].append(cost_type_row[0])

                office_list.append(data)

            send_data['result'] = 'SUCCESS'
            send_data['list'] = office_list

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            request_body = json.loads(request.get_data())
            if not 'name' in request_body:
                send_data = {"result": "영업소명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'registrationName' in request_body:
                send_data = {"result": "사업자명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'registrationNumber' in request_body:
                send_data = {"result": "사업자번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'representative' in request_body:
                send_data = {"result": "대표자가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'phoneNumber' in request_body:
                send_data = {"result": "전화번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'faxNumber' in request_body:
                send_data = {"result": "전화번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'sellingType' in request_body:
                send_data = {"result": "판매유형이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'costType' in request_body:
                send_data = {"result": "가격권한이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'address' in request_body:
                send_data = {"result": "재소지가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'businessStatus' in request_body:
                send_data = {"result": "업태가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'businessItem' in request_body:
                send_data = {"result": "종목이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            name = request_body['name']
            registrationName = request_body['registrationName']
            registrationNumber = request_body['registrationNumber']
            sellingTypes = request_body['sellingType']
            costTypes = request_body['costType']
            representative = request_body['representative']
            phoneNumber = request_body['phoneNumber']
            faxNumber = request_body['faxNumber']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            address = request_body['address']
            businessStatus = request_body['businessStatus']
            businessItem = request_body['businessItem']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"INSERT INTO office(registration_number,registration_name,office_name,representative,description,phone_number,fax_number,address,business_status,business_item,use_flag,user_id,register_date) VALUES ('{registrationNumber}','{registrationName}','{name}','{representative}','{description}','{phoneNumber}','{faxNumber}','{address}','{businessStatus}','{businessItem}',{useFlag},'{userId}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            query = f"SELECT MAX(office_tag) FROM office;"
            mysql_cursor.execute(query)
            tag_row = mysql_cursor.fetchone()
            if not tag_row:
                tag = 1
            elif not tag_row[0]:
                tag = 1
            else:
                tag = tag_row[0]
            for sellingType in sellingTypes:
                query = f"INSERT INTO office_selling_type(office_tag, type, user_id, register_date) VALUES ({tag},{sellingType},'{userId}',CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)
            
            for costType in costTypes:
                query = f"INSERT INTO office_cost_type(office_tag, type, user_id, register_date) VALUES ({tag},{costType},'{userId}',CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = str(tag)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#영업소 수정, 삭제
@app.route('/office/<int:officeTag>', methods=['PUT','DELETE'])
def officetDetailApis(officeTag):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    query = f"SELECT * FROM office WHERE office_tag = '{officeTag}';"
    mysql_cursor.execute(query)
    office_row = mysql_cursor.fetchone()
    if not office_row:
        send_data = {"result": "해당 처 Tag는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'name' in request_body:
                send_data = {"result": "영업소명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'registrationName' in request_body:
                send_data = {"result": "사업자명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'registrationNumber' in request_body:
                send_data = {"result": "사업자번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'representative' in request_body:
                send_data = {"result": "대표자가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'phoneNumber' in request_body:
                send_data = {"result": "전화번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'faxNumber' in request_body:
                send_data = {"result": "전화번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'sellingType' in request_body:
                send_data = {"result": "판매유형이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'costType' in request_body:
                send_data = {"result": "가격권한이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'address' in request_body:
                send_data = {"result": "재소지가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'businessStatus' in request_body:
                send_data = {"result": "업태가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'businessItem' in request_body:
                send_data = {"result": "종목이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            name = request_body['name']
            registrationName = request_body['registrationName']
            registrationNumber = request_body['registrationNumber']
            sellingTypes = request_body['sellingType']
            costTypes = request_body['costType']
            representative = request_body['representative']
            phoneNumber = request_body['phoneNumber']
            faxNumber = request_body['faxNumber']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            address = request_body['address']
            businessStatus = request_body['businessStatus']
            businessItem = request_body['businessItem']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"UPDATE office SET registration_number= '{registrationNumber}',registration_name = '{registrationName}',office_name = '{name}', representative='{representative}',description='{description}',phone_number='{phoneNumber}',fax_number='{faxNumber}',address='{address}',business_status='{businessStatus}',business_item='{businessItem}',use_flag={useFlag},user_id='{userId}',register_date=CURRENT_TIMESTAMP WHERE office_tag = {officeTag};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM office_selling_type WHERE office_tag = {officeTag};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM office_cost_type WHERE office_tag = {officeTag};"
            mysql_cursor.execute(query)

            for sellingType in sellingTypes:
                query = f"INSERT INTO office_selling_type(office_tag, type, user_id, register_date) VALUES ({officeTag},{sellingType},'{userId}',CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)
            
            for costType in costTypes:
                query = f"INSERT INTO office_cost_type(office_tag, type, user_id, register_date) VALUES ({officeTag},{costType},'{userId}',CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = str(officeTag)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    
    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:

            query = f"DELETE FROM office_selling_type WHERE office_tag = {officeTag};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM office_cost_type WHERE office_tag = {officeTag};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM office WHERE office_tag = {officeTag};"
            mysql_cursor.execute(query)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#판매처 리스트 조회, 등록
@app.route('/seller', methods=['GET','POST'])
def sellerApis():
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            params = request.args.to_dict()
            condition_query = None
            
            if 'type' in params:
                sellerType = int(params['type'])
                if sellerType < 0 or sellerType > 5:
                    send_data = {"result": "판매처 판매 유형 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if sellerType != 0:
                    if condition_query: 
                        condition_query = condition_query + f" seller_tag IN (SELECT seller_tag FROM seller_selling_type WHERE type = {sellerType})"
                    else:
                        condition_query = f" WHERE seller_tag IN (SELECT seller_tag FROM seller_selling_type WHERE type = {sellerType})"

            if 'useFlag' in params:
                useFlag = int(params['useFlag'])
                if useFlag < 0 or useFlag > 2:
                    send_data = {"result": "사용 여부의 값이 올바르지 않습니다."}
                    status_code = status.HTTP_400_BAD_REQUEST
                    return flask.make_response(flask.jsonify(send_data), status_code)
                if useFlag == 1:
                    if condition_query: 
                        condition_query = condition_query + " and use_flag = 1"
                    else:
                        condition_query = " WHERE use_flag = 1"
                elif useFlag == 2:
                    if condition_query:
                        condition_query = condition_query + " and use_flag != 1"
                    else:
                        condition_query = " WHERE use_flag != 1"

            if 'sellerName' in params:
                name = params['sellerName']
                if condition_query:
                    condition_query = condition_query + f" and seller_name like '%{name}%'"
                else:
                    condition_query = f" WHERE seller_name like '%{name}%'"

            if 'registrationName' in params:
                name = params['registrationName']
                if condition_query:
                    condition_query = condition_query + f" and registration_name like '%{name}%'"
                else:
                    condition_query = f" WHERE registration_name like '%{name}%'"

            if 'phoneNumber' in params:
                phoneNumber = params['phoneNumber']
                if condition_query:
                    condition_query = condition_query + f" and phone_number like '%{phoneNumber}%'"
                else:
                    condition_query = f" WHERE phone_number like '%{phoneNumber}%'"

            if condition_query:
                query = f"SELECT seller_tag, seller_name, registration_number, registration_name, representative, phone_number, fax_number, use_flag, description, address, business_status, business_item, user_id FROM seller" + condition_query + ';'
            else:
                query = f"SELECT seller_tag, seller_name, registration_number, registration_name, representative, phone_number, fax_number, use_flag, description, address, business_status, business_item, user_id FROM seller;"
            mysql_cursor.execute(query)
            seller_rows = mysql_cursor.fetchall()
            
            seller_list = list()
            for seller_row in seller_rows:
                data = dict()
                data['tag'] = seller_row[0]
                data['name'] = seller_row[1]
                data['registrationNumber'] = seller_row[2]
                data['registrationName'] = seller_row[3]
                data['representative'] = seller_row[4]
                data['phoneNumber'] = seller_row[5]
                data['faxNumber'] = seller_row[6]
                data['useFlag'] = seller_row[7]
                data['description'] = seller_row[8]
                data['address'] = seller_row[9]
                data['businessStatus'] = seller_row[10]
                data['businessItem'] = seller_row[11]
                data['userId'] = seller_row[12]

                query = f"SELECT type FROM seller_selling_type WHERE seller_tag = {data['tag']};"
                mysql_cursor.execute(query)
                selling_type_rows = mysql_cursor.fetchall()
                data['sellingType'] = list()
                for selling_type_row in selling_type_rows:
                    data['sellingType'].append(selling_type_row[0])

                query = f"SELECT coupon_discount, card_discount FROM seller_cost WHERE seller_tag = {data['tag']} ORDER BY register_date DESC;"
                mysql_cursor.execute(query)
                cost_type_row = mysql_cursor.fetchone()
                if cost_type_row:
                    data['couponDiscount'] = cost_type_row[0]
                    data['cardDiscount'] = cost_type_row[1]
                else:
                    data['couponDiscount'] = float(0)
                    data['cardDiscount'] = float(0)

                seller_list.append(data)

            send_data['result'] = 'SUCCESS'
            send_data['list'] = seller_list

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            request_body = json.loads(request.get_data())
            if not 'name' in request_body:
                send_data = {"result": "영업소명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'registrationName' in request_body:
                send_data = {"result": "사업자명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'registrationNumber' in request_body:
                send_data = {"result": "사업자번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'representative' in request_body:
                send_data = {"result": "대표자가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'phoneNumber' in request_body:
                send_data = {"result": "전화번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'faxNumber' in request_body:
                send_data = {"result": "전화번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'sellingType' in request_body:
                send_data = {"result": "판매유형이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'address' in request_body:
                send_data = {"result": "재소지가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'businessStatus' in request_body:
                send_data = {"result": "업태가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'businessItem' in request_body:
                send_data = {"result": "종목이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            name = request_body['name']
            registrationName = request_body['registrationName']
            registrationNumber = request_body['registrationNumber']
            sellingTypes = request_body['sellingType']
            representative = request_body['representative']
            phoneNumber = request_body['phoneNumber']
            faxNumber = request_body['faxNumber']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            address = request_body['address']
            businessStatus = request_body['businessStatus']
            businessItem = request_body['businessItem']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"INSERT INTO seller(registration_number,registration_name,seller_name,representative,description,phone_number,fax_number,address,business_status,business_item,use_flag,user_id,register_date) VALUES ('{registrationNumber}','{registrationName}','{name}','{representative}','{description}','{phoneNumber}','{faxNumber}','{address}','{businessStatus}','{businessItem}',{useFlag},'{userId}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)
            query = f"SELECT MAX(seller_tag) FROM seller;"
            mysql_cursor.execute(query)
            tag_row = mysql_cursor.fetchone()
            if not tag_row:
                tag = 1
            elif not tag_row[0]:
                tag = 1
            else:
                tag = tag_row[0]

            for sellingType in sellingTypes:
                query = f"INSERT INTO seller_selling_type(seller_tag, type, user_id, register_date) VALUES ({tag},{sellingType},'{userId}',CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = str(tag)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#판매처 수정, 삭제
@app.route('/seller/<int:sellerTag>', methods=['PUT','DELETE'])
def sellertDetailApis(sellerTag):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    query = f"SELECT * FROM seller WHERE seller_tag = '{sellerTag}';"
    mysql_cursor.execute(query)
    seller_row = mysql_cursor.fetchone()
    if not seller_row:
        send_data = {"result": "해당 판매처 Tag는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'name' in request_body:
                send_data = {"result": "영업소명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'registrationName' in request_body:
                send_data = {"result": "사업자명이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'registrationNumber' in request_body:
                send_data = {"result": "사업자번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'representative' in request_body:
                send_data = {"result": "대표자가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'phoneNumber' in request_body:
                send_data = {"result": "전화번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'faxNumber' in request_body:
                send_data = {"result": "전화번호가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'sellingType' in request_body:
                send_data = {"result": "판매유형이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'useFlag' in request_body:
                send_data = {"result": "사용여부가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'description' in request_body:
                send_data = {"result": "메모가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'address' in request_body:
                send_data = {"result": "재소지가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'businessStatus' in request_body:
                send_data = {"result": "업태가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'businessItem' in request_body:
                send_data = {"result": "종목이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            name = request_body['name']
            registrationName = request_body['registrationName']
            registrationNumber = request_body['registrationNumber']
            sellingTypes = request_body['sellingType']
            representative = request_body['representative']
            phoneNumber = request_body['phoneNumber']
            faxNumber = request_body['faxNumber']
            useFlag = int(request_body['useFlag'])
            description = request_body['description']
            address = request_body['address']
            businessStatus = request_body['businessStatus']
            businessItem = request_body['businessItem']
            userId = request_body['userId']

            if useFlag < 0 or useFlag > 1:
                send_data = {"result": "사용여부는 0:미사용, 1: 사용으로 입력해주세요."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            query = f"UPDATE seller SET registration_number= '{registrationNumber}',registration_name = '{registrationName}',seller_name = '{name}', representative='{representative}',description='{description}',phone_number='{phoneNumber}',fax_number='{faxNumber}',address='{address}',business_status='{businessStatus}',business_item='{businessItem}',use_flag={useFlag},user_id='{userId}',register_date=CURRENT_TIMESTAMP WHERE seller_tag = {sellerTag};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM seller_selling_type WHERE seller_tag = {sellerTag};"
            mysql_cursor.execute(query)

            for sellingType in sellingTypes:
                query = f"INSERT INTO seller_selling_type(seller_tag, type, user_id, register_date) VALUES ({sellerTag},{sellingType},'{userId}',CURRENT_TIMESTAMP);"
                mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = str(sellerTag)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    
    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:
            query = f"DELETE FROM seller WHERE seller_tag = {sellerTag};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM seller_selling_type WHERE seller_tag = {sellerTag};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM seller_cost WHERE seller_tag = {sellerTag};"
            mysql_cursor.execute(query)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#판매처 비용 리스트 조회, 등록
@app.route('/seller/<int:sellerTag>/cost', methods=['GET','POST'])
def sellerCostApis(sellerTag):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            query = f"SELECT register_date, coupon_discount, card_discount, advertisement_cost, partner_levy, product_maintenance_cost, penalty_cost, delivery_cost FROM seller_cost WHERE seller_tag = {sellerTag}"
            mysql_cursor.execute(query)
            cost_rows = mysql_cursor.fetchall()
            
            cost_list = list()
            for cost_row in cost_rows:
                data = dict()
                data['registerDate'] = cost_row[0]
                data['couponDiscount'] = cost_row[1]
                data['cardDiscount'] = cost_row[2]
                data['advertisementCost'] = cost_row[3]
                data['partnerLevy'] = cost_row[4]
                data['productMaintenanceCost'] = cost_row[5]
                data['penaltyCost'] = cost_row[6]
                data['deliveryCost'] = cost_row[7]

                cost_list.append(data)

            send_data['result'] = 'SUCCESS'
            send_data['list'] = cost_list

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            request_body = json.loads(request.get_data())
            if not 'couponDiscount' in request_body:
                send_data = {"result": "쿠폰 할인율이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'cardDiscount' in request_body:
                send_data = {"result": "카드 할인율이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'advertisementCost' in request_body:
                send_data = {"result": "마케팅 비용이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'partnerLevy' in request_body:
                send_data = {"result": "협력사 부담금 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'productMaintenanceCost' in request_body:
                send_data = {"result": "상품 유지비용이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'penaltyCost' in request_body:
                send_data = {"result": "패널티 비용이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'deliveryCost' in request_body:
                send_data = {"result": "배송 비용이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            
            coupon_discount = request_body['couponDiscount']
            card_discount = request_body['cardDiscount']
            advertisement_cost = request_body['advertisementCost']
            partner_levy = request_body['partnerLevy']
            product_maintenance_cost = request_body['productMaintenanceCost']
            penalty_cost = request_body['penaltyCost']
            delivery_cost = request_body['deliveryCost']
            user_id = request_body['userId']

            query = f"INSERT INTO seller_cost(seller_tag,coupon_discount,card_discount,advertisement_cost,partner_levy,product_maintenance_cost,penalty_cost,delivery_cost,user_id,register_date) VALUES ({sellerTag},{coupon_discount},{card_discount},{advertisement_cost},{partner_levy},{product_maintenance_cost},{penalty_cost},{delivery_cost},'{user_id}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = str(sellerTag)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
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
        process_config = config['system_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"system_management.log"
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