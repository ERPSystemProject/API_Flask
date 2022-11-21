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
def commentDetailApis(boardIndex,commentIndex):
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

            query = f"SELECT brand_tag, brand_name, use_flag, description, user_id FROM brand" + condition_query + ';'
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

            query = f"INSERT INTO brand(brand_tag,brand_name,use_flag,,description,user_id,register_date) VALUES ('{tag}','{name}',{useFlag},'{description}','{userId}',CURRENT_TIMESTAMP);"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['tag'] = tag

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