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
            data['officeTag'] = office_row[0]
            data['officeName'] = office_row[1]
            officeList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['list'] = officeList

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
        for index, row in enumerate(rows):
            data = dict()
            data['index'] = index
            data['brandTag'] = row[0]
            data['brandName'] = row[1]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['list'] = dataList

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
        for index, row in enumerate(rows):
            data = dict()
            data['index'] = index
            data['categoryTag'] = row[0]
            data['categoryName'] = row[1]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['list'] = dataList

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
        for index, row in enumerate(rows):
            data = dict()
            data['index'] = index
            data['origin'] = row[0]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['list'] = dataList

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
        for index, row in enumerate(rows):
            data = dict()
            data['index'] = index
            data['season'] = row[0]
            dataList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['list'] = dataList

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
            data['supplierTag'] = row[0]
            data['supplierName'] = row[1]
            dateList.append(data)

        send_data['result'] = 'SUCCESS'
        send_data['list'] = dateList

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