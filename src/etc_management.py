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
    
#office 드롭박스 리스트 조회
@app.route('/offices', methods=['GET'])
def getOfficeDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT office_tag, office_name FROM office WHERE office_tag > 0 and office_name like '%{params['keyword']}%';"
        else:
            query = "SELECT office_tag, office_name FROM office WHERE office_tag > 0;"
        mysql_cursor.execute(query)
        office_rows = mysql_cursor.fetchall()

        officeList = list()
        for office_row in office_rows:
            data = dict()
            data['tag'] = office_row[0]
            data['name'] = office_row[1]
            officeList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '영업처'
        send_data['items'] = officeList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#from office 드롭박스 리스트 조회
@app.route('/fromOffices', methods=['GET'])
def getFromOfficeDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT office_tag, office_name FROM office WHERE office_tag > 0 and office_name like '%{params['keyword']}%';"
        else:
            query = "SELECT office_tag, office_name FROM office WHERE office_tag > 0;"
        mysql_cursor.execute(query)
        office_rows = mysql_cursor.fetchall()

        officeList = list()
        for office_row in office_rows:
            data = dict()
            data['tag'] = office_row[0]
            data['name'] = office_row[1]
            officeList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '출발 영업처'
        send_data['items'] = officeList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#to office 드롭박스 리스트 조회
@app.route('/toOffices', methods=['GET'])
def getToOfficeDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT office_tag, office_name FROM office WHERE office_tag > 0 and office_name like '%{params['keyword']}%';"
        else:
            query = "SELECT office_tag, office_name FROM office WHERE office_tag > 0;"
        mysql_cursor.execute(query)
        office_rows = mysql_cursor.fetchall()

        officeList = list()
        for office_row in office_rows:
            data = dict()
            data['tag'] = office_row[0]
            data['name'] = office_row[1]
            officeList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '도착 영업처'
        send_data['items'] = officeList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#brand 드롭박스 리스트 조회
@app.route('/brands', methods=['GET'])
def getBrandDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT brand_tag, brand_name FROM brand WHERE brand_name like '%{params['keyword']}%';"
        else:
            query = "SELECT brand_tag, brand_name FROM brand;"
        mysql_cursor.execute(query)
        rows = mysql_cursor.fetchall()

        dataList = list()
        for row in rows:
            data = dict()
            data['tag'] = row[0]
            data['name'] = row[1]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '브랜드'
        send_data['items'] = dataList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#category 드롭박스 리스트 조회
@app.route('/categories', methods=['GET'])
def getCategoryDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT category_tag, category_name FROM category WHERE category_name like '%{params['keyword']}%';"
        else:
            query = "SELECT category_tag, category_name FROM category;"
        mysql_cursor.execute(query)
        rows = mysql_cursor.fetchall()

        dataList = list()
        for row in rows:
            data = dict()
            data['tag'] = row[0]
            data['name'] = row[1]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '상품 종류'
        send_data['items'] = dataList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#origin 드롭박스 리스트 조회
@app.route('/origins', methods=['GET'])
def getOriginDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT origin_name FROM origin WHERE origin_name like '%{params['keyword']}%';"
        else:
            query = "SELECT origin_name FROM origin;"
        mysql_cursor.execute(query)
        rows = mysql_cursor.fetchall()

        dataList = list()
        for row in rows:
            data = dict()
            data['tag'] = row[0]
            data['name'] = row[0]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '원산지'
        send_data['items'] = dataList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#season 드롭박스 리스트 조회
@app.route('/seasons', methods=['GET'])
def getSeasonDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT season FROM season WHERE season like '%{params['keyword']}%';"
        else:
            query = "SELECT season FROM season;"
        mysql_cursor.execute(query)
        rows = mysql_cursor.fetchall()

        dataList = list()
        for row in rows:
            data = dict()
            data['tag'] = row[0]
            data['name'] = row[0]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '시즌'
        send_data['items'] = dataList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#supplier 드롭박스 리스트 조회
@app.route('/suppliers', methods=['GET'])
def getSupplierDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT supplier_tag, supplier_name FROM supplier WHERE supplier_tag > 0 and supplier_name like '%{params['keyword']}%';"
        else:
            query = "SELECT supplier_tag, supplier_name FROM supplier WHERE supplier_tag > 0;"
        mysql_cursor.execute(query)
        rows = mysql_cursor.fetchall()

        dateList = list()
        for row in rows:
            data = dict()
            data['tag'] = row[0]
            data['name'] = row[1]
            dateList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '공급처'
        send_data['items'] = dateList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#sex 드롭박스 리스트 조회
@app.route('/sex', methods=['GET'])
def getSexDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        dateList = list()
        rows = ['공용','남성','여성']
        for index, row in enumerate(rows):
            data = dict()
            data['tag'] = index
            data['name'] = row
            dateList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '성별'
        send_data['items'] = dateList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#supplier type 드롭박스 리스트 조회
@app.route('/supplierTypes', methods=['GET'])
def getSupplierTypesDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        dateList = list()
        rows = ['위탁','사입','직수입','미입고']
        for index, row in enumerate(rows):
            data = dict()
            data['tag'] = index + 1
            data['name'] = row
            dateList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '공급처유형'
        send_data['items'] = dateList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#goods status 드롭박스 리스트 조회
@app.route('/goodsStatus', methods=['GET'])
def getGoodsStatusDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        dateList = list()
        rows = ['스크래치','판매불가','폐기','정상재고','분실','정산대기','분배대기','회수완료','수선중','반품정산대기','판매완료','출고승인대기','고객반송대기']
        for index, row in enumerate(rows):
            data = dict()
            data['tag'] = index + 1
            data['name'] = row
            dateList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '상품상태'
        send_data['items'] = dateList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#seller types 드롭박스 리스트 조회
@app.route('/sellerTypes', methods=['GET'])
def getSellerTypesDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        dateList = list()
        rows = ['도매','위탁','직영','행사','홈쇼핑','온라인','소매','기타']
        for index, row in enumerate(rows):
            data = dict()
            data['tag'] = index + 1
            data['name'] = row
            dateList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '판매처유형'
        send_data['items'] = dateList

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#seller 드롭박스 리스트 조회
@app.route('/sellers', methods=['GET'])
def getSellerDropBoxList():
    send_data = dict()
    status_code = status.HTTP_200_OK
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        params = request.args.to_dict()

        if 'keyword' in params:
            query = f"SELECT seller_tag, seller_name FROM seller WHERE seller_name like '%{params['keyword']}%';"
        else:
            query = "SELECT seller_tag, seller_name FROM seller;"
        mysql_cursor.execute(query)
        rows = mysql_cursor.fetchall()

        dataList = list()
        for row in rows:
            data = dict()
            data['tag'] = row[0]
            data['name'] = row[1]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['name'] = '판매처'
        send_data['items'] = dataList

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
        process_config = config['etc_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"etc_management.log"
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