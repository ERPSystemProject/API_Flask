# -*- coding: utf-8 -*-
#!/usr/bin/env python3
  
import logging
import json
import sys
import yaml

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
    
#로그인
@app.route('/login', methods=['POST'])
def userLogin():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        request_body = json.loads(request.get_data())
        user_id = request_body['id']
        user_password = request_body['password']
        query = f"SELECT password FROM user WHERE user_id = '{user_id}';"
        mysql_cursor.execute(query)
        password_row = mysql_cursor.fetchone()

        if not password_row:
            send_data = {"message": "로그인 실패하였습니다. ID 또는 패스워드를 확인해 주세요."}
            status_code = status.HTTP_401_UNAUTHORIZED
            return flask.make_response(flask.jsonify(send_data), status_code)
        if user_password != password_row[0]:
            send_data = {"message": "로그인 실패하였습니다. ID 또는 패스워드를 확인해 주세요."}
            status_code = status.HTTP_401_UNAUTHORIZED
            return flask.make_response(flask.jsonify(send_data), status_code)
        query = f"SELECT community_board_flag, goods_management_flag, consignment_management_flag, move_management_flag, sell_managemant_flag, remain_management_flag, sale_management_flag, system_management_flag, user_authority_management_flag FROM user_authority WHERE user_id = '{user_id}';"
        mysql_cursor.execute(query)
        authority_row = mysql_cursor.fetchone()
        if not authority_row:
            send_data = {"message": "권한을 가져오는데 실패했습니다. 관리자에게 문의하세요."}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return flask.make_response(flask.jsonify(send_data), status_code)
        send_data['result'] = "SUCCESS"
        send_data['authority'] = dict()
        send_data['authority']['community_board_flag'] = authority_row[0]
        send_data['authority']['goods_management_flag'] = authority_row[1]
        send_data['authority']['consignment_management_flag'] = authority_row[2]
        send_data['authority']['move_management_flag'] = authority_row[3]
        send_data['authority']['sell_managemant_flag'] = authority_row[4]
        send_data['authority']['remain_management_flag'] = authority_row[5]
        send_data['authority']['sale_management_flag'] = authority_row[6]
        send_data['authority']['system_management_flag'] = authority_row[7]
        send_data['authority']['user_authority_management_flag'] = authority_row[8]

    except Exception as e:
        send_data = {"message": f"Error : {e}"}
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
        process_config = config['user_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+log_config['filename']
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