# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys

import flask
from flask_restx import Api, Resource, Namespace, fields, reqparse
import werkzeug
import requests
import json
import yaml

community_ns = Namespace('Community', version="1.0", title='Community API List', description='Community API List')

notice_query_parser = reqparse.RequestParser()
notice_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
notice_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
notice_query_parser.add_argument('searchType', type=int, help='searchType | 0: title, 1: content, 2: writer ID, 3: writer name')
notice_query_parser.add_argument('searchContent', type=str, help='searchContent')

request_query_parser = reqparse.RequestParser()
request_query_parser.add_argument('limit', type=int, required=True, default=15, help='limit')
request_query_parser.add_argument('page', type=int, required=True, default=1, help='current page')
request_query_parser.add_argument('searchType', type=int, help='searchType | 0: title, 1: content, 2: writer ID, 3: writer name')
request_query_parser.add_argument('searchContent', type=str, help='searchContent')
request_query_parser.add_argument('boardType', type=int, help='boardType 0: all, 1: register goods, 2: exchange request, 3: questions, 4: delivery request, 5: return request, 6: holding request, 7: ERP fix, 8: etc, 9: Purchasing Team Request')

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('files', location='files', type=werkzeug.datastructures.FileStorage, help='file upload')

board_list_fields = community_ns.model('board list fields', {
    'boardIndex':fields.Integer(description='id', required=True, example=1),
    'targetOffices':fields.List(fields.String(description='target Offices', required=True, example='all')),
    'boardType':fields.String(description='board Type', required=True, example='notice'),
    'title':fields.String(description='title', required=True, example='title'),
    'commentCount':fields.Integer(description='comment Count',required=True,example=0),
    'writeOffice':fields.String(description='write Office',required=True,example='write Office'),
    'writer':fields.String(description='writer name',required=True,example='writer'),
    'registerDate':fields.String(description='registerDate',required=True,example='2022-01-01 12:00'),
    'viewCount':fields.Integer(description='viewCount',required=True,example=0)
})

notice_list_response_fields = community_ns.model('notice list response', {
    'result':fields.String(description="result", required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(board_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10)
})

request_list_response_fields = community_ns.model('request list response', {
    'result':fields.String(description='result', required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(board_list_fields)),
    'totalPage':fields.Integer(description="totalPage", required=True, example=10)
})

post_board_request_fields = community_ns.model('post board request', {
    'offices':fields.List(fields.Integer(description='target offices ID | 0: all', required=True, example=0)),
    'boardType':fields.Integer(description='board Type | 0: notice, 1: register goods, 2: exchange request, 3: questions, 4: delivery request, 5: return request, 6: holding request, 7: ERP fix, 8: etc, 9: Purchasing Team Request', required=True, example=0),
    'title':fields.String(description='title', required=True, example='title'),
    'content':fields.String(description='content',required=True,example='content'),
    'userId':fields.String(description='writer ID',required=True,example='admin')
})

post_board_response_fields = community_ns.model('post board response', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'boardIndex':fields.Integer(description='board Index', required=True, example='1')
})

comment_request_fields = community_ns.model('comment request fields', {
    'content':fields.String(description='content',required=True,example='content'),
    'userId':fields.String(description='user ID',required=True,example='admin')
})

comment_response_fields = community_ns.model('comment response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'boardIndex':fields.Integer(description='boardIndex', required=True, example=1),
    'commentIndex':fields.Integer(description='commentIndex', required=True, example=1)
})

comment_fields = community_ns.model('comment fields', {
    'commentIndex':fields.Integer(description='commentIndex',required=True,example=1),
    'writeOffice':fields.String(description='writeOffice',required=True,example='writeOffice'),
    'writer':fields.String(description='writer',required=True,example='writer'),
    'content':fields.String(description='content',required=True,example='content'),
    'registerDate':fields.String(description='registerDate',required=True,example='2022-01-01 12:00')
})

file_fields = community_ns.model('file fields', {
    'fileName':fields.String(description='fileName',required=True,example='test.txt'),
    'fileUrl':fields.String(description='fileUrl',required=True,example='http://52.79.206.187:19999/community_board/1/test.txt')
})

get_board_detail_fields = community_ns.model('board detail fields', {
    'targetOffices':fields.List(fields.Integer(description='targetOffices ID | 0: all', required=True, example=0)),
    'boardType':fields.Integer(description='board Type | 0: notice, 1: register goods, 2: exchange request, 3: questions, 4: delivery request, 5: return request, 6: holding request, 7: ERP fix, 8: etc, 9: Purchasing Team Request', required=True, example=0),
    'title':fields.String(description='title', required=True, example='title'),
    'content':fields.String(description='content',required=True,example='content'),
    'writeOffice':fields.String(description='writeOffice',required=True,example='writeOffice'),
    'writer':fields.String(description='writer',required=True,example='writer'),
    'registerDate':fields.String(description='registerDate',required=True,example='2022-01-01 12:00'),
    'comments':fields.List(fields.Nested(comment_fields)),
    'fileList':fields.List(fields.Nested(file_fields))
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['community_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@community_ns.route('/notice')
class noticeApiList(Resource):

    @community_ns.expect(notice_query_parser)
    @community_ns.response(200, 'OK', notice_list_response_fields)
    @community_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def get(self):
        '''
        get notice list 
        '''
        args = notice_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/notice", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code


@community_ns.route('/request')
class requestApiList(Resource):
    @community_ns.expect(request_query_parser)
    @community_ns.response(200, 'OK', request_list_response_fields)
    @community_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def get(self):
        '''
        get request list
        '''
        args = request_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/request", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@community_ns.route('/')
class communityApiList(Resource):
    
    @community_ns.expect(post_board_request_fields)
    @community_ns.response(201, 'OK', post_board_response_fields)
    @community_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def post(self):
        '''
        post board
        board Type | 0: notice, 1: register goods, 2: exchange request, 3: questions, 4: delivery request, 5: return request, 6: holding request, 7: ERP fix, 8: etc, 9: Purchasing Team Request
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@community_ns.route('/<int:boardIndex>')
class communityBoardApiList(Resource):

    @community_ns.response(200, 'OK', get_board_detail_fields)
    def get(self,boardIndex):
        '''
        get board detail
        board Type | 0: notice, 1: register goods, 2: exchange request, 3: questions, 4: delivery request, 5: return request, 6: holding request, 7: ERP fix, 8: etc, 9: Purchasing Team Request
        '''
        res = requests.get(f"http://{management_url}/{boardIndex}", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code
    
    @community_ns.expect(post_board_request_fields)
    @community_ns.response(200, 'OK', post_board_response_fields)
    @community_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def put(self,boardIndex):
        '''
        adjust board
        board Type | 0: notice, 1: register goods, 2: exchange request, 3: questions, 4: delivery request, 5: return request, 6: holding request, 7: ERP fix, 8: etc, 9: Purchasing Team Request
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/{boardIndex}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @community_ns.doc(responses={204: 'OK'})
    def delete(self,boardIndex):
        '''
        delete board
        '''
        res = requests.delete(f"http://{management_url}/{boardIndex}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@community_ns.route('/<int:boardIndex>/comment')
class communityBoardCommentPostApiList(Resource):

    @community_ns.expect(comment_request_fields)
    @community_ns.response(201, 'OK', comment_response_fields)
    @community_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def post(self,boardIndex):
        '''
        post comment
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.post(f"http://{management_url}/{boardIndex}/comment", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@community_ns.route('/<int:boardIndex>/comment/<int:commentIndex>')
class communityBoardCommentApiList(Resource):

    @community_ns.expect(comment_request_fields)
    @community_ns.response(200, 'OK', comment_response_fields)
    @community_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def put(self,boardIndex,commentIndex):
        '''
        adjust comment
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/{boardIndex}/comment/{commentIndex}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @community_ns.doc(responses={204: 'OK'})
    def delete(self,boardIndex,commentIndex):
        '''
        delete comment
        '''
        res = requests.delete(f"http://{management_url}/{boardIndex}/comment/{commentIndex}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code

@community_ns.route('/<int:boardIndex>/file')
class communityBoardCommentApiList(Resource):
    @community_ns.expect(upload_parser)
    @community_ns.response(201, 'OK', post_board_response_fields)
    @community_ns.doc(responses={201:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def post(self,boardIndex):
        '''
        post file of board
        '''
        files = flask.request.files
        file_list = list()
        upload_files = flask.request.files.getlist("files")
        for upload_file in upload_files:
            filename = upload_file.filename
            file_ = upload_file.read()
            type_ = upload_file.content_type
            file_list.append(('files',(filename,file_,type_)))
        res = requests.post(f"http://{management_url}/{boardIndex}/file", files=file_list, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

@community_ns.route('/<int:boardIndex>/file/<string:fileName>')
class communityBoardCommentApiList(Resource):
    @community_ns.doc(responses={204: 'OK'})
    def delete(self,boardIndex,fileName):
        '''
        delete file of board
        '''
        res = requests.delete(f"http://{management_url}/{boardIndex}/file/{fileName}", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code