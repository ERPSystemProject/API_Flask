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
    
#게시물 작성
@app.route('/', methods=['POST'])
def postBoard():
    send_data = dict()
    status_code = status.HTTP_201_CREATED
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    try:
        request_body = json.loads(request.get_data())
        if not 'offices' in request_body:
            send_data = {"result": "대상 영업소가 지정되지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'boardType' in request_body:
            send_data = {"result": "게시물 분류가 지정되지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'title' in request_body:
            send_data = {"result": "제목이 입력되지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'content' in request_body:
            send_data = {"result": "내용이 입력되지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'userId' in request_body:
            send_data = {"result": "작성자 ID가 입력되지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        
        offices = request_body['offices']
        boardType = request_body['boardType']
        title = request_body['title']
        content = request_body['content']
        userId = request_body['userId']

        if 0 in offices:
            offices = [0]

        query = f"INSERT INTO community_board(type, title, content, user_id, register_date) VALUES({boardType},'{title}','{content}','{userId}',CURRENT_TIMESTAMP);"
        mysql_cursor.execute(query)

        query = f"SELECT MAX(community_board.index) FROM community_board;"
        mysql_cursor.execute(query)
        index_row = mysql_cursor.fetchone()
        if not index_row:
            index = 1
        elif not index_row[0]:
            index = 1
        else:
            index = index_row[0]

        for office in offices:
            query = f"INSERT INTO community_board_target VALUES ({index},{office});"
            mysql_cursor.execute(query)
        
        os.makedirs(f"/home/ubuntu/data/community_board/{index}")

        send_data['result'] = 'SUCCESS'
        send_data['boardIndex'] = index

    except Exception as e:
        send_data = {"result": f"Error : {e}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#공지사항 리스트 조회
@app.route('/notice', methods=['GET'])
def getNoticeBoards():
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
        condition_query = f" limit {start}, {limit};"
        
        if 'searchType' in params and 'searchContent' in params:
            searchType = int(params['searchType'])
            searchContent = params['searchContent']
            if searchType == 0:
                condition_query = f" WHERE title like '%{searchContent}%' AND type = 0" + condition_query
            elif searchType == 1:
                condition_query = f" WHERE content like '%{searchContent}%' AND type = 0" + condition_query
            elif searchType == 2:
                condition_query = f" WHERE user_id like '%{searchContent}%' AND type = 0" + condition_query
            elif searchType == 3:
                condition_query = f" WHERE user_id in (SELECT user_id FROM user WHERE name like '%{searchContent}%') AND type = 0" + condition_query
            else:
                send_data = {"result": "검색 구분이 올바르지 않습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
        else:
            condition_query = f" WHERE type = 0" + condition_query

        query = f"SELECT community_board.index, title, user_id, register_date, view_count FROM community_board" + condition_query
        mysql_cursor.execute(query)
        board_rows = mysql_cursor.fetchall()

        boardList = list()
        for board_row in board_rows:
            data = dict()
            data['boardIndex'] = board_row[0]
            data['title'] = board_row[1]
            user_id = board_row[2]
            data['registerDate'] = board_row[3]
            data['viewCount'] = board_row[4]
            data['boardType'] = '공지사항'

            query = f"SELECT office_tag, name FROM user WHERE user_id = '{user_id}';"
            mysql_cursor.execute(query)
            user_row = mysql_cursor.fetchone()
            data['writeOffice'] = user_row[0]
            data['writer'] = user_row[1]

            query = f"SELECT office_name FROM office WHERE office_tag in (SELECT office_tag FROM community_board_target WHERE community_board_target.index = {data['boardIndex']});"
            mysql_cursor.execute(query)
            target_rows = mysql_cursor.fetchall()
            targetOffices = list()
            for target_row in target_rows:
                targetOffices.append(target_row[0])
            data['targetOffices'] = targetOffices

            query = f"SELECT count(*) FROM community_board_comment WHERE community_board_comment.index = {data['boardIndex']};"
            mysql_cursor.execute(query)
            comment_count_row = mysql_cursor.fetchone()
            data['commentCount'] = comment_count_row[0]
            
            boardList.append(data)

        query = f"SELECT count(*) FROM community_board" + condition_query.replace(limit_query, ";")
        mysql_cursor.execute(query)
        count_row = mysql_cursor.fetchone()

        send_data['result'] = "SUCCESS"
        send_data['list'] = boardList
        send_data['totalPage'] = int(int(count_row[0])/int(limit)) + 1
        send_data['totalBoard'] = int(count_row[0])


    except Exception as e:
        send_data = {"result": f"Error : {traceback.format_exc()}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#요청사항 리스트 조회
@app.route('/request', methods=['GET'])
def getRequestBoards():
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
        condition_query = f" limit {start}, {limit};"

        if 'boardType' in params:
            boardType = int(params['boardType'])
            if boardType < 0 or boardType >=10:
                send_data = {"result": "게시물 종류가 올바르지 않습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)

            if boardType > 0 and boardType < 10:
                condition_query = f" type = {boardType}" + condition_query
            else:
                condition_query = f" type != 0" + condition_query
        else:
            condition_query = f" type != 0" + condition_query
        
        if 'searchType' in params and 'searchContent' in params:
            searchType = int(params['searchType'])
            searchContent = params['searchContent']
            if searchType == 0:
                condition_query = f" WHERE title like '%{searchContent}%' AND" + condition_query
            elif searchType == 1:
                condition_query = f" WHERE content like '%{searchContent}%' AND" + condition_query
            elif searchType == 2:
                condition_query = f" WHERE user_id like '%{searchContent}%' AND" + condition_query
            elif searchType == 3:
                condition_query = f" WHERE user_id in (SELECT user_id FROM user WHERE name like '%{searchContent}%') AND" + condition_query
            else:
                send_data = {"result": "검색 구분이 올바르지 않습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
        else:
            condition_query = f" WHERE" + condition_query

        query = f"SELECT community_board.index, title, user_id, register_date, view_count, type FROM community_board" + condition_query
        mysql_cursor.execute(query)
        board_rows = mysql_cursor.fetchall()

        boardList = list()
        for board_row in board_rows:
            data = dict()
            data['boardIndex'] = board_row[0]
            data['title'] = board_row[1]
            user_id = board_row[2]
            data['registerDate'] = board_row[3]
            data['viewCount'] = board_row[4]
            boardType = int(board_row[5])
            if boardType == 1:
                data['boardType'] = '상풍등록'
            elif boardType == 2:
                data['boardType'] = '교환요청'
            elif boardType == 3:
                data['boardType'] = '문의사항'
            elif boardType == 4:
                data['boardType'] = '배송요청'
            elif boardType == 5:
                data['boardType'] = '회수요청'
            elif boardType == 6:
                data['boardType'] = '홀딩요청'
            elif boardType == 7:
                data['boardType'] = 'ERP수정'
            elif boardType == 8:
                data['boardType'] = '기타'
            elif boardType == 9:
                data['boardType'] = '구매팀요청'

            query = f"SELECT office_tag, name FROM user WHERE user_id = '{user_id}';"
            mysql_cursor.execute(query)
            user_row = mysql_cursor.fetchone()
            data['writeOffice'] = user_row[0]
            data['writer'] = user_row[1]

            query = f"SELECT office_name FROM office WHERE office_tag in (SELECT office_tag FROM community_board_target WHERE community_board_target.index = {data['boardIndex']});"
            mysql_cursor.execute(query)
            target_rows = mysql_cursor.fetchall()
            targetOffices = list()
            for target_row in target_rows:
                targetOffices.append(target_row[0])
            data['targetOffices'] = targetOffices

            query = f"SELECT count(*) FROM community_board_comment WHERE community_board_comment.index = {data['boardIndex']};"
            mysql_cursor.execute(query)
            comment_count_row = mysql_cursor.fetchone()
            data['commentCount'] = comment_count_row[0]

            boardList.append(data)

        query = f"SELECT count(*) FROM community_board" + condition_query.replace(limit_query, ";")
        mysql_cursor.execute(query)
        count_row = mysql_cursor.fetchone()

        send_data['result'] = "SUCCESS"
        send_data['list'] = boardList
        send_data['totalPage'] = int(int(count_row[0])/int(limit)) + 1
        send_data['totalBoard'] = int(count_row[0])

    except Exception as e:
        send_data = {"result": f"Error : {traceback.format_exc()}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#게시물 상세조회, 수정, 삭제
@app.route('/<int:boardIndex>', methods=['GET','PUT','DELETE'])
def boardDetailApis(boardIndex):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)
    
    query = f"SELECT * FROM community_board WHERE community_board.index = {boardIndex};"
    mysql_cursor.execute(query)
    board_row = mysql_cursor.fetchone()
    if not board_row:
        send_data = {"result": "해당 게시물 번호는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'GET':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            query = f"update community_board SET view_count = view_count + 1 WHERE community_board.index = {boardIndex};"
            mysql_cursor.execute(query)

            query = f"SELECT type, title, content, user_id, register_date FROM community_board WHERE community_board.index= {boardIndex};"
            mysql_cursor.execute(query)
            board_row = mysql_cursor.fetchone()
            data = dict()
            data['boardIndex'] = boardIndex
            data['boardType'] = board_row[0]
            data['title'] = board_row[1]
            data['content'] = board_row[2]
            user_id = board_row[3]
            data['registerDate'] = board_row[4]

            query = f"SELECT office_tag, name FROM user WHERE user_id = '{user_id}';"
            mysql_cursor.execute(query)
            user_row = mysql_cursor.fetchone()
            data['writeOffice'] = user_row[0]
            data['writer'] = user_row[1]

            query = f"SELECT office_name FROM office WHERE office_tag in (SELECT office_tag FROM community_board_target WHERE community_board_target.index = {boardIndex});"
            mysql_cursor.execute(query)
            target_rows = mysql_cursor.fetchall()
            targetOffices = list()
            for target_row in target_rows:
                targetOffices.append(target_row[0])
            data['targetOffices'] = targetOffices

            comments = list()
            query = f"SELECT comment_index, content, user_id, register_date FROM community_board_comment WHERE community_board_comment.index = {boardIndex};"
            mysql_cursor.execute(query)
            comment_rows = mysql_cursor.fetchall()
            for comment_row in comment_rows:
                comment_data = dict()
                comment_data['commentIndex'] = comment_row[0]
                comment_data['content'] = comment_row[1]
                commentUserId = comment_row[2]
                comment_data['registerDate'] = comment_row[3]

                query = f"SELECT office_tag, name FROM user WHERE user_id = '{user_id}';"
                mysql_cursor.execute(query)
                user_row = mysql_cursor.fetchone()
                comment_data['writeOffice'] = user_row[0]
                comment_data['writer'] = user_row[1]
                
                comments.append(comment_data)
            data['comments'] = comments
            
            fileDir = f"/home/ubuntu/data/community_board/{boardIndex}"
            fileUrl = f"http://52.79.206.187:19999/community_board/{boardIndex}/"
            files = os.listdir(fileDir)
            fileList = list()
            for index,filename in enumerate(files):
                file_data = dict()
                file_data['id'] = index
                file_data['filepath'] = fileDir + '/' + filename.replace(' ','%20')
                file_data['fileSize'] = os.path.getsize(fileDir + '/' + filename)
                file_data['fileType'] = filename.split('.')[-1]
                file_data['fileName'] = filename
                file_data['fileUrl'] = fileUrl + filename.replace(' ','%20')
                fileList.append(file_data)
            data['fileList'] = fileList

            send_data = data

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)
    
    elif flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'offices' in request_body:
                send_data = {"result": "대상 영업소가 지정되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'boardType' in request_body:
                send_data = {"result": "게시물 분류가 지정되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'title' in request_body:
                send_data = {"result": "제목이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'content' in request_body:
                send_data = {"result": "내용이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "작성자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
        
            offices = request_body['offices']
            boardType = request_body['boardType']
            title = request_body['title']
            content = request_body['content']
            userId = request_body['userId']

            if 0 in offices:
                offices = [0]
            
            query = f"UPDATE community_board SET type = {boardType}, title = '{title}', content = '{content}', user_id = '{userId}', register_date = CURRENT_TIMESTAMP WHERE community_board.index = {boardIndex};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM community_board_target WHERE community_board_target.index = {boardIndex};"
            mysql_cursor.execute(query)

            for office in offices:
                query = f"INSERT INTO community_board_target VALUES ({boardIndex},{office});"
                mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['boardIndex'] = boardIndex

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:
            query = f"DELETE FROM community_board_target WHERE community_board_target.index = {boardIndex};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM community_board_comment WHERE community_board_comment.index = {boardIndex};"
            mysql_cursor.execute(query)

            query = f"DELETE FROM community_board WHERE community_board.index = {boardIndex};"
            mysql_cursor.execute(query)

            dir_path = f"/home/ubuntu/data/community_board/{boardIndex}"
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#게시물 파일 등록
@app.route('/<int:boardIndex>/file', methods=['POST'])
def boardPostFileApis(boardIndex):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)
    
    query = f"SELECT * FROM community_board WHERE community_board.index = {boardIndex};"
    mysql_cursor.execute(query)
    board_row = mysql_cursor.fetchone()
    if not board_row:
        send_data = {"result": "해당 게시물 번호는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'POST':
        send_data = dict()
        status_code = status.HTTP_201_CREATED
        try:
            file = flask.request.files['files']
            filePath = f"/home/ubuntu/data/community_board/{boardIndex}/"
            fileUrl = f"http://52.79.206.187:19999/community_board/{boardIndex}/"
            file.save(filePath+file.filename)
            send_data['result'] = 'SUCCESS'
            send_data['filePath'] = filePath+file.filename.replace(' ','%20')
            send_data['fileUrl'] = fileUrl+file.filename.replace(' ','%20')
            
        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#게시물 파일 삭제
@app.route('/<int:boardIndex>/file/<string:fileName>', methods=['DELETE'])
def boardDeleteFileApis(boardIndex,fileName):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)
    
    query = f"SELECT * FROM community_board WHERE community_board.index = {boardIndex};"
    mysql_cursor.execute(query)
    board_row = mysql_cursor.fetchone()
    if not board_row:
        send_data = {"result": "해당 게시물 번호는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:

            dir_path = f"/home/ubuntu/data/community_board/{boardIndex}/"
            file_path = dir_path+fileName
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                send_data = {"result": f"해당 게시물에는 {fileName} 이라는 파일이 존재하지 않습니다."}
                status_code = status.HTTP_404_NOT_FOUND
                return flask.make_response(flask.jsonify(send_data), status_code)

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

#댓글 등록
@app.route('/<int:boardIndex>/comment', methods=['POST'])
def postComment(boardIndex):
    send_data = dict()
    status_code = status.HTTP_201_CREATED
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)

    query = f"SELECT * FROM community_board WHERE community_board.index = {boardIndex};"
    mysql_cursor.execute(query)
    board_row = mysql_cursor.fetchone()
    if not board_row:
        send_data = {"result": "해당 게시물 번호는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)
    
    try:
        request_body = json.loads(request.get_data())
        if not 'content' in request_body:
            send_data = {"result": "댓글 내용이 입력되지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        if not 'userId' in request_body:
            send_data = {"result": "댓긓 등록자 ID가 입력되지 않았습니다."}
            status_code = status.HTTP_400_BAD_REQUEST
            return flask.make_response(flask.jsonify(send_data), status_code)
        content = request_body['content']
        userId = request_body['userId']

        query = f"INSERT INTO community_board_comment (community_board_comment.index, content, user_id, register_date) VALUES ({boardIndex}, '{content}', '{userId}', CURRENT_TIMESTAMP);"
        mysql_cursor.execute(query)

        query = f"SELECT MAX(comment_index) FROM community_board_comment WHERE community_board_comment.index = {boardIndex};"
        mysql_cursor.execute(query)
        comment_index_row = mysql_cursor.fetchone()
        commentIndex = comment_index_row[0]

        send_data['result'] = 'SUCCESS'
        send_data['boardIndex'] = boardIndex
        send_data['commentIndex'] = commentIndex
    except Exception as e:
        send_data = {"result": f"Error : {traceback.format_exc()}"}
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        return flask.make_response(flask.jsonify(send_data), status_code)

#댓글 수정, 삭제
@app.route('/<int:boardIndex>/comment/<int:commentIndex>', methods=['PUT','DELETE'])
def commentDetailApis(boardIndex,commentIndex):
    mysql_cursor, connect_code = connect_mysql()
    if not connect_code == status.HTTP_200_OK:
        return flask.make_response(flask.jsonify(mysql_cursor), connect_code)
    
    query = f"SELECT * FROM community_board_comment WHERE community_board_comment.index = {boardIndex} and comment_index = {commentIndex};"
    mysql_cursor.execute(query)
    board_row = mysql_cursor.fetchone()
    if not board_row:
        send_data = {"result": "해당 댓글 번호는 존재하지 않습니다."}
        status_code = status.HTTP_404_NOT_FOUND
        return flask.make_response(flask.jsonify(send_data), status_code)

    if flask.request.method == 'PUT':
        send_data = dict()
        status_code = status.HTTP_200_OK
        try:
            request_body = json.loads(request.get_data())
            if not 'content' in request_body:
                send_data = {"result": "댓글 내용이 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            if not 'userId' in request_body:
                send_data = {"result": "댓긓 등록자 ID가 입력되지 않았습니다."}
                status_code = status.HTTP_400_BAD_REQUEST
                return flask.make_response(flask.jsonify(send_data), status_code)
            content = request_body['content']
            userId = request_body['userId']

            query = f"UPDATE community_board_comment SET content = '{content}', user_id = '{userId}', register_date = CURRENT_TIMESTAMP WHERE community_board_comment.index = {boardIndex} and comment_index = {commentIndex};"
            mysql_cursor.execute(query)

            send_data['result'] = 'SUCCESS'
            send_data['boardIndex'] = boardIndex
            send_data['commentIndex'] = commentIndex

        except Exception as e:
            send_data = {"result": f"Error : {traceback.format_exc()}"}
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            return flask.make_response(flask.jsonify(send_data), status_code)

    elif flask.request.method == 'DELETE':
        send_data = dict()
        status_code = status.HTTP_204_NO_CONTENT
        try:

            query = f"DELETE FROM community_board_comment WHERE community_board_comment.index = {boardIndex} and comment_index = {commentIndex};"
            mysql_cursor.execute(query)

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
        process_config = config['community_management']
        db_config = config['DB']['mysql']

        #LogWriter 설정
        log_filename = log_config['filepath']+"community_management.log"
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