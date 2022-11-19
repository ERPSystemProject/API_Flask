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
notice_query_parser.add_argument('limit', type=int, required=True, default=15, help='한 페이지당 몇개의 게시물')
notice_query_parser.add_argument('page', type=int, required=True, default=1, help='현재 페이지')
notice_query_parser.add_argument('searchType', type=int, help='검색기준 | 0: 제목, 1: 내용, 2: 작성자 ID, 3: 작성자 이름')
notice_query_parser.add_argument('searchContent', type=str, help='검색내용')

request_query_parser = reqparse.RequestParser()
request_query_parser.add_argument('limit', type=int, required=True, default=15, help='한 페이지당 몇개의 게시물')
request_query_parser.add_argument('page', type=int, required=True, default=1, help='현재 페이지')
request_query_parser.add_argument('searchType', type=int, help='검색기준 | 0: 제목, 1: 내용, 2: 작성자 ID, 3: 작성자 이름')
request_query_parser.add_argument('searchContent', type=str, help='검색내용')
request_query_parser.add_argument('boardType', type=int, help='게시물종류 0: 전체, 1: 상품등록, 2: 교환요청, 3: 문의사항, 4: 배송요청, 5: 회수요청, 6: 홀딩요청, 7: ERP수정, 8: 기타, 9: 구매팀요청')

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('files', location='files', type=werkzeug.datastructures.FileStorage, action='append', help='파일 업로드')

board_list_fields = community_ns.model('게시물 리스트 내용', {
    'boardIndex':fields.Integer(description='번호', required=True, example=1),
    'targetOffices':fields.List(fields.String(description='대상 영업소', required=True, example='전체')),
    'boardType':fields.String(description='게시물 분류', required=True, example='공지사항'),
    'title':fields.String(description='제목', required=True, example='테스트'),
    'commentCount':fields.Integer(description='댓글수',required=True,example=0),
    'writeOffice':fields.String(description='작성영업소',required=True,example='작성영업소'),
    'writer':fields.String(description='작성자이름',required=True,example='관리자'),
    'registerDate':fields.String(description='작성일',required=True,example='2022-01-01 12:00'),
    'viewCount':fields.Integer(description='조회수',required=True,example=0)
})

notice_list_response_fields = community_ns.model('공지사항 리스트 조회', {
    'result':fields.String(description="리스트 조회 결과", required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(board_list_fields))
})

request_list_response_fields = community_ns.model('요청사항 리스트 조회', {
    'result':fields.String(description='리스트 조회 결과', required=True, example='SUCCESS'),
    'list':fields.List(fields.Nested(board_list_fields))
})

post_board_request_fields = community_ns.model('게시판 작성 request', {
    'offices':fields.List(fields.Integer(description='대상 영업소 ID | 0: 전체', required=True, example=0)),
    'boardType':fields.Integer(description='게시물 분류 | 0: 공지사항, 1: 상품등록, 2: 교환요청, 3: 문의사항, 4: 배송요청, 5: 회수요청, 6: 홀딩요청, 7: ERP수정, 8: 기타, 9: 구매팀요청', required=True, example=0),
    'title':fields.String(description='제목', required=True, example='테스트'),
    'content':fields.String(description='내용',required=True,example='내용'),
    'userId':fields.String(description='사용자 ID',required=True,example='admin')
})

post_board_response_fields = community_ns.model('게시판 작성 response', {
    'result':fields.String(description='결과',required=True,example='SUCCESS'),
    'boardIndex':fields.Integer(description='게시판 번호', required=True, example='1')
})

comment_request_fields = community_ns.model('댓글 관리 요청 fields', {
    'content':fields.String(description='내용',required=True,example='내용'),
    'userId':fields.String(description='사용자 ID',required=True,example='admin')
})

comment_response_fields = community_ns.model('댓글 관리 결과 fields', {
    'result':fields.String(description='결과',required=True,example='SUCCESS'),
    'boardIndex':fields.Integer(description='게시판 번호', required=True, example='1'),
    'commentIndex':fields.Integer(description='댓글 번호', required=True, example='1')
})

comment_fields = community_ns.model('댓글 fields', {
    'commentIndex':fields.Integer(description='댓글 번호',required=True,example=1),
    'writeOffice':fields.String(description='작성영업소',required=True,example='작성영업소'),
    'writer':fields.String(description='작성자이름',required=True,example='관리자'),
    'content':fields.String(description='내용',required=True,example='내용'),
    'registerDate':fields.String(description='작성일',required=True,example='2022-01-01 12:00')
})

file_fields = community_ns.model('피알 fields', {
    'filePath':fields.String(description='파일 경로',required=True,example='/path/to/file')
})

get_board_detail_fields = community_ns.model('게시판 상세 조회', {
    'targetOffices':fields.List(fields.Integer(description='대상 영업소 ID | 0: 전체', required=True, example=0)),
    'boardType':fields.Integer(description='게시물 분류 | 0: 공지사항, 1: 상품등록, 2: 교환요청, 3: 문의사항, 4: 배송요청, 5: 회수요청, 6: 홀딩요청, 7: ERP수정, 8: 기타, 9: 구매팀요청', required=True, example=0),
    'title':fields.String(description='제목', required=True, example='테스트'),
    'content':fields.String(description='내용',required=True,example='내용'),
    'writeOffice':fields.String(description='작성영업소',required=True,example='작성영업소'),
    'writer':fields.String(description='작성자이름',required=True,example='관리자'),
    'registerDate':fields.String(description='작성일',required=True,example='2022-01-01 12:00'),
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
        공지사항 리스트 조회
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
        요청사항 리스트 조회
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
        게시물 작성
        boardType | 0: 공지사항, 1: 상품등록, 2: 교환요청, 3: 문의사항, 4: 배송요청, 5: 회수요청, 6: 홀딩요청, 7: ERP수정, 8: 기타, 9: 구매팀요청
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
        게시물 상세 조회
        boardType | 0: 공지사항, 1: 상품등록, 2: 교환요청, 3: 문의사항, 4: 배송요청, 5: 회수요청, 6: 홀딩요청, 7: ERP수정, 8: 기타, 9: 구매팀요청
        '''
        res = requests.get(f"http://{management_url}/{boardIndex}", timeout=3)
        result = json.loads(res.text)
        return result, res.status_code
    
    @community_ns.expect(post_board_request_fields)
    @community_ns.response(200, 'OK', post_board_response_fields)
    @community_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    def put(self,boardIndex):
        '''
        게시물 수정
        boardType | 0: 공지사항, 1: 상품등록, 2: 교환요청, 3: 문의사항, 4: 배송요청, 5: 회수요청, 6: 홀딩요청, 7: ERP수정, 8: 기타, 9: 구매팀요청
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/{boardIndex}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @community_ns.doc(responses={204: 'OK'})
    def delete(self,boardIndex):
        '''
        게시물 삭제
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
        댓글 등록
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
        댓글 수정
        '''
        request_body = json.loads(flask.request.get_data(), encoding='utf-8')
        res = requests.put(f"http://{management_url}/{boardIndex}/comment/{commentIndex}", data=json.dumps(request_body), timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @community_ns.doc(responses={204: 'OK'})
    def delete(self,boardIndex,commentIndex):
        '''
        댓글 삭제
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
        게시물 파일 등록
        '''
        args = upload_parser.parse_args()
        fileList = args['files']
        res = requests.post(f"http://{management_url}/{boardIndex}/file", files=fileList, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code

    @community_ns.doc(responses={204: 'OK'})
    def delete(self,boardIndex):
        '''
        게시물 파일 삭제
        '''
        res = requests.delete(f"http://{management_url}/{boardIndex}/file", timeout=3)
        if res.status_code == 204:
            return None, res.status_code
        result = json.loads(res.text)
        return result, res.status_code