# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import sys

import flask
from flask_restx import Api, Resource, Namespace, fields, reqparse
from flask_jwt_extended import jwt_required
import werkzeug
import requests
import json
import yaml

etc_ns = Namespace('ETC', version="1.0", title='ETC API List', description='ETC API List')

office_query_parser = reqparse.RequestParser()
office_query_parser.add_argument('keyword', type=str, help='search keyword')

office_list_fields = etc_ns.model('office drop box fields', {
    'officeTag':fields.Integer(description='office tag',required=True,example=1),
    'officeName':fields.String(description='office name',required=True,example='name')
})

office_list_response_fields = etc_ns.model('office drop box response fields', {
    'result':fields.String(description='result',required=True,example='SUCCESS'),
    'list':fields.List(fields.Nested(office_list_fields))
})

#config 불러오기
f = open('../config/config.yaml')
config = yaml.load(f, Loader=yaml.FullLoader)
f.close()
apiconfig = config['etc_management']

management_url = apiconfig['ip'] + ':' + str(apiconfig['port'])

@etc_ns.route('/offices')
class officeDropBox(Resource):

    @etc_ns.expect(office_query_parser)
    @etc_ns.response(200, 'OK', office_list_response_fields)
    @etc_ns.doc(responses={200:'OK', 404:'Not Found', 500:'Internal Server Error'})
    @jwt_required()
    def get(self):
        '''
        get office drop box list 
        '''
        args = office_query_parser.parse_args()
        res = requests.get(f"http://{management_url}/offices", params=args, timeout=3)
        result = json.loads(res.text)
        return result, res.status_code
