# -*- coding: utf-8 -*-
#!/usr/bin/env python3
  
import logging
import json
import sys
import yaml

import flask
from flask import request
from flask_api import status
from flask_jwt_extended import JWTManager, create_access_token
import pymysql
import datetime

logWriter = None
db_config = None
config_path = "../config/config.yaml"

app = flask.Flask(__name__)

# 토큰 생성에 사용될 Secret Key를 flask 환경 변수에 등록
app.config.update(
			DEBUG = True,
			JWT_SECRET_KEY = "WATERIN"
		)

# JWT 확장 모듈을 flask 어플리케이션에 등록
jwt = JWTManager(app)

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
    status_code = status.HTTP_201_CREATED
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
            send_data = {"result": "로그인 실패하였습니다. ID 또는 패스워드를 확인해 주세요."}
            status_code = status.HTTP_401_UNAUTHORIZED
            return flask.make_response(flask.jsonify(send_data), status_code)
        if user_password != password_row[0]:
            send_data = {"result": "로그인 실패하였습니다. ID 또는 패스워드를 확인해 주세요."}
            status_code = status.HTTP_401_UNAUTHORIZED
            return flask.make_response(flask.jsonify(send_data), status_code)
        query = f"SELECT community_board_flag, community_board_1_flag, community_board_2_flag, goods_management_flag, goods_management_1_flag, goods_management_2_flag, goods_management_3_flag, consignment_management_flag, consignment_management_1_flag, consignment_management_2_flag, consignment_management_3_flag, move_management_flag, move_management_1_flag, move_management_2_flag, move_management_3_flag, move_management_4_flag, sell_management_flag, sell_management_1_flag, sell_management_2_flag, remain_management_flag, remain_management_1_flag, remain_management_2_flag, remain_management_3_flag, remain_management_4_flag, remain_management_5_flag, remain_management_6_flag, sale_management_flag, sale_management_1_flag, sale_management_2_flag, sale_management_3_flag, system_management_flag, system_management_1_flag, system_management_2_flag, system_management_3_flag, system_management_4_flag, system_management_5_flag, system_management_6_flag, user_authority_management_flag FROM user_authority WHERE authority_id IN (SELECT authority_id FROM user WHERE user_id = '{user_id}');"
        mysql_cursor.execute(query)
        authority_row = mysql_cursor.fetchone()
        if not authority_row:
            send_data = {"result": "권한을 가져오는데 실패했습니다. 관리자에게 문의하세요."}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return flask.make_response(flask.jsonify(send_data), status_code)
        send_data['result'] = "SUCCESS"
        send_data['userId'] = user_id
        send_data['authority'] = dict()
        send_data['authority']['community_board_flag'] = authority_row[0]
        send_data['authority']['community_board_1_flag'] = authority_row[1]
        send_data['authority']['community_board_2_flag'] = authority_row[2]
        send_data['authority']['goods_management_flag'] = authority_row[3]
        send_data['authority']['goods_management_1_flag'] = authority_row[4]
        send_data['authority']['goods_management_2_flag'] = authority_row[5]
        send_data['authority']['goods_management_3_flag'] = authority_row[6]
        send_data['authority']['consignment_management_flag'] = authority_row[7]
        send_data['authority']['consignment_management_1_flag'] = authority_row[8]
        send_data['authority']['consignment_management_2_flag'] = authority_row[9]
        send_data['authority']['consignment_management_3_flag'] = authority_row[10]
        send_data['authority']['move_management_flag'] = authority_row[11]
        send_data['authority']['move_management_1_flag'] = authority_row[12]
        send_data['authority']['move_management_2_flag'] = authority_row[13]
        send_data['authority']['move_management_3_flag'] = authority_row[14]
        send_data['authority']['move_management_4_flag'] = authority_row[15]
        send_data['authority']['sell_management_flag'] = authority_row[16]
        send_data['authority']['sell_management_1_flag'] = authority_row[17]
        send_data['authority']['sell_management_2_flag'] = authority_row[18]
        send_data['authority']['remain_management_flag'] = authority_row[19]
        send_data['authority']['remain_management_1_flag'] = authority_row[20]
        send_data['authority']['remain_management_2_flag'] = authority_row[21]
        send_data['authority']['remain_management_3_flag'] = authority_row[22]
        send_data['authority']['remain_management_4_flag'] = authority_row[23]
        send_data['authority']['remain_management_5_flag'] = authority_row[24]
        send_data['authority']['remain_management_6_flag'] = authority_row[25]
        send_data['authority']['sale_management_flag'] = authority_row[26]
        send_data['authority']['sale_management_1_flag'] = authority_row[27]
        send_data['authority']['sale_management_2_flag'] = authority_row[28]
        send_data['authority']['sale_management_3_flag'] = authority_row[29]
        send_data['authority']['system_management_flag'] = authority_row[30]
        send_data['authority']['system_management_1_flag'] = authority_row[31]
        send_data['authority']['system_management_2_flag'] = authority_row[32]
        send_data['authority']['system_management_3_flag'] = authority_row[33]
        send_data['authority']['system_management_4_flag'] = authority_row[34]
        send_data['authority']['system_management_5_flag'] = authority_row[35]
        send_data['authority']['system_management_6_flag'] = authority_row[36]
        send_data['authority']['user_authority_management_flag'] = authority_row[37]

        send_data['token'] = create_access_token(identity = user_id, expires_delta = datetime.timedelta(minutes=15))

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#토큰으로 현재 회원 값 조회
@app.route('/<string:user_id>', methods=['GET'])
def tokenUser(user_id):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        query = f"SELECT password FROM user WHERE user_id = '{user_id}';"
        mysql_cursor.execute(query)
        password_row = mysql_cursor.fetchone()

        if not password_row:
            send_data = {"result": "올바르지 않은 토큰입니다."}
            status_code = status.HTTP_401_UNAUTHORIZED
            return flask.make_response(flask.jsonify(send_data), status_code)
        
        query = f"SELECT community_board_flag, community_board_1_flag, community_board_2_flag, goods_management_flag, goods_management_1_flag, goods_management_2_flag, goods_management_3_flag, consignment_management_flag, consignment_management_1_flag, consignment_management_2_flag, consignment_management_3_flag, move_management_flag, move_management_1_flag, move_management_2_flag, move_management_3_flag, move_management_4_flag, sell_management_flag, sell_management_1_flag, sell_management_2_flag, remain_management_flag, remain_management_1_flag, remain_management_2_flag, remain_management_3_flag, remain_management_4_flag, remain_management_5_flag, remain_management_6_flag, sale_management_flag, sale_management_1_flag, sale_management_2_flag, sale_management_3_flag, system_management_flag, system_management_1_flag, system_management_2_flag, system_management_3_flag, system_management_4_flag, system_management_5_flag, system_management_6_flag, user_authority_management_flag FROM user_authority WHERE authority_id IN (SELECT authority_id FROM user WHERE user_id = '{user_id}');"
        mysql_cursor.execute(query)
        authority_row = mysql_cursor.fetchone()
        if not authority_row:
            send_data = {"result": "권한을 가져오는데 실패했습니다. 관리자에게 문의하세요."}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return flask.make_response(flask.jsonify(send_data), status_code)
        send_data['result'] = "SUCCESS"
        send_data['userId'] = user_id
        send_data['authority'] = dict()
        send_data['authority']['community_board_flag'] = authority_row[0]
        send_data['authority']['community_board_1_flag'] = authority_row[1]
        send_data['authority']['community_board_2_flag'] = authority_row[2]
        send_data['authority']['goods_management_flag'] = authority_row[3]
        send_data['authority']['goods_management_1_flag'] = authority_row[4]
        send_data['authority']['goods_management_2_flag'] = authority_row[5]
        send_data['authority']['goods_management_3_flag'] = authority_row[6]
        send_data['authority']['consignment_management_flag'] = authority_row[7]
        send_data['authority']['consignment_management_1_flag'] = authority_row[8]
        send_data['authority']['consignment_management_2_flag'] = authority_row[9]
        send_data['authority']['consignment_management_3_flag'] = authority_row[10]
        send_data['authority']['move_management_flag'] = authority_row[11]
        send_data['authority']['move_management_1_flag'] = authority_row[12]
        send_data['authority']['move_management_2_flag'] = authority_row[13]
        send_data['authority']['move_management_3_flag'] = authority_row[14]
        send_data['authority']['move_management_4_flag'] = authority_row[15]
        send_data['authority']['sell_management_flag'] = authority_row[16]
        send_data['authority']['sell_management_1_flag'] = authority_row[17]
        send_data['authority']['sell_management_2_flag'] = authority_row[18]
        send_data['authority']['remain_management_flag'] = authority_row[19]
        send_data['authority']['remain_management_1_flag'] = authority_row[20]
        send_data['authority']['remain_management_2_flag'] = authority_row[21]
        send_data['authority']['remain_management_3_flag'] = authority_row[22]
        send_data['authority']['remain_management_4_flag'] = authority_row[23]
        send_data['authority']['remain_management_5_flag'] = authority_row[24]
        send_data['authority']['remain_management_6_flag'] = authority_row[25]
        send_data['authority']['sale_management_flag'] = authority_row[26]
        send_data['authority']['sale_management_1_flag'] = authority_row[27]
        send_data['authority']['sale_management_2_flag'] = authority_row[28]
        send_data['authority']['sale_management_3_flag'] = authority_row[29]
        send_data['authority']['system_management_flag'] = authority_row[30]
        send_data['authority']['system_management_1_flag'] = authority_row[31]
        send_data['authority']['system_management_2_flag'] = authority_row[32]
        send_data['authority']['system_management_3_flag'] = authority_row[33]
        send_data['authority']['system_management_4_flag'] = authority_row[34]
        send_data['authority']['system_management_5_flag'] = authority_row[35]
        send_data['authority']['system_management_6_flag'] = authority_row[36]
        send_data['authority']['user_authority_management_flag'] = authority_row[37]

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#토큰으로 현재 회원 상세 조회
@app.route('/information/<string:user_id>', methods=['GET'])
def userInformation(user_id):
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        query = f"SELECT name, department, phone_number, email, office_tag, register_date FROM user WHERE user_id = '{user_id}';"
        mysql_cursor.execute(query)
        info_row = mysql_cursor.fetchone()
        if not info_row:
            send_data = {"result": "올바르지 않은 토큰입니다."}
            status_code = status.HTTP_401_UNAUTHORIZED
            return flask.make_response(flask.jsonify(send_data), status_code)
        
        send_data['result'] = "SUCCESS"
        send_data['name'] = info_row[0]
        send_data['department'] = info_row[1]
        send_data['phoneNumber'] = info_row[2]
        send_data['email'] = info_row[3]
        office_tag = info_row[4]
        send_data['registerDate'] = info_row[5]
        if office_tag:
            query = f"SELECT office_name FROM office WHERE office_tag = {office_tag};"
            mysql_cursor.execute(query)
            office_row = mysql_cursor.fetchone()
            send_data['office'] = office_row[0]
        else:
            send_data['office'] = None

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
        process_config = config['user_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"user_management.log"
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