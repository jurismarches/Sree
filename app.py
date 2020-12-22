#! /usr/bin/python
#encoding=utf-8

import json
import os

from flask import Flask
from flask import json
from flask import request
from flask import send_from_directory
from flask import Response
import requests

import xmlparser
import base64
import hashlib

app = Flask(__name__, static_url_path='')

try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse


def get_url_from_req(request):
    url = from_request(request, 'url')
    parsed = urlparse(url)
    s3_endpoint = app.config['S3_ENDPOINT']
    return urlunparse((parsed[0], s3_endpoint, parsed[2], parsed[3], parsed[4], parsed[5]))


def from_request(request, k):
    if not request.json:
        raise Exception("Invalid Request")
    return str(request.json[k])


def req(url, method):
    command = requests.get
    if method == 'DELETE':
        command = requests.delete
    elif method == 'PUT':
        command = requests.put
    elif method == 'POST':
        command = requests.post
    r = command(url)
    return r.status_code


@app.route("/createbucket", methods = ['POST'])
def create():
  url = get_url_from_req(request)
  statuscode = req(url, 'PUT')

  if statuscode == 200:
     resp = Response(response='Success', status=statuscode)
  elif statuscode == 400:
      resp = Response(response='Invalid Bucket Name', status=statuscode)
  elif statuscode == 409:
     resp = Response(response='Conflict: Bucket already Exists',
                     status=statuscode)
  elif statuscode == 403:
     resp = Response(response='Access Denied', status=statuscode)
  else:
     resp = Response(response='Unknown Error', status=500)
  return resp


@app.route("/deletebucket", methods = ['DELETE'])
def delete():
  url = get_url_from_req(request)
  statuscode = req(url, 'DELETE')

  if statuscode == 204:
     resp = Response(status=200)
  elif statuscode == 404:
     resp = Response(response='Bucket Not Exist', status=statuscode)
  elif statuscode == 403:
     resp = Response(response='Access Denied', status=statuscode)
  elif statuscode == 409:
     resp = Response(response='Confilct: Object Still Exists',
                     status=statuscode)
  else:
     resp = Response(response='Unknown Error', status=500)
  return resp

@app.route("/putcors", methods = ['PUT'])
def putcors():
  corsurl = get_url_from_req(request)
  s3auth = from_request(request, 's3auth')
  date = from_request(request, 'date')

  cors = '''
<CORSConfiguration>
  <CORSRule>
      <AllowedMethod>PUT</AllowedMethod>
      <AllowedMethod>GET</AllowedMethod>
      <AllowedMethod>POST</AllowedMethod>
      <AllowedMethod>DELETE</AllowedMethod>
      <AllowedOrigin>*</AllowedOrigin>
      <AllowedHeader>*</AllowedHeader>
      <ExposeHeader>x-amz-acl</ExposeHeader>
      <ExposeHeader>ETag</ExposeHeader>
  </CORSRule>
</CORSConfiguration>'''
  content_md5 = base64.b64encode(hashlib.md5(cors.encode('utf8')).digest())

  headers = {
      'Content-type':'text/xml',
      'Content-MD5':content_md5,
      'Authorization':s3auth,
      'Date' : date
  }

  r  = requests.put(corsurl, headers=headers, data=cors)
  statuscode = r.status_code

  if statuscode == 200:
     resp = Response(status=statuscode)
  elif statuscode == 403:
     resp = Response(response='Access Denied', status=statuscode)
  else:
     resp = Response(response='Unknown Error', status=500)
  return resp

@app.route("/getservice", methods = ['POST'])
def listbucketsurl():
  url = get_url_from_req(request)
  s3auth = from_request(request, 's3auth')
  date = from_request(request, 'date')

  headers = {'Authorization':s3auth, 'x-amz-date': date}

  r = requests.get(url, headers=headers)

  statuscode = r.status_code

  if statuscode != 200:
     if statuscode == 403:
        resp = Response(response='Access Denied', status=statuscode)
     else:
        resp = Response(response='Unknown Error', status=500)
     return resp

  content = r.text

  buckets = xmlparser.getListFromXml(content, 'Bucket')
  resp = Response(response=json.dumps(buckets), status=statuscode)
  resp.headers['Content-type'] = 'application/json; charset=UTF-8'
  return resp

@app.route("/")
def root():
    return app.send_static_file('buckets.html')

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory('static', path)

@app.route("/gets3config")
def s3_config():
    config = dict()
    config["endpoint"] = app.config['S3_EXT_ENDPOINT']
    config["accessKeyId"] = app.config['S3_ACCESS_KEY']
    config["secretAccessKey"] = app.config["S3_SECRET_KEY"]
    config["region"] = app.config["S3_REGION"]

    resp = Response(response=json.dumps(config))
    resp.headers['Content-type'] = 'application/json; charset=UTF-8'
    return resp

if __name__ == '__main__':
    app.config['SREE_PORT'] = os.environ.get('SREE_PORT', 5000)
    app.config['FLASK_DEBUG'] = os.environ.get('FLASK_DEBUG', False)
    app.config['S3_ENDPOINT'] = os.environ.get('S3_ENDPOINT', 'http://s3.amazonaws.com')
    app.config['S3_EXT_ENDPOINT'] = os.environ.get('S3_EXT_ENDPOINT', app.config['S3_ENDPOINT'])
    app.config['S3_ACCESS_KEY'] = os.environ.get('S3_ACCESS_KEY')
    app.config['S3_SECRET_KEY'] = os.environ.get('S3_SECRET_KEY')
    app.config['S3_REGION'] = os.environ.get('S3_REGION')

    flask_port = app.config['SREE_PORT']
    flask_debug = app.config['FLASK_DEBUG']

    app.run(host='0.0.0.0', port=flask_port, threaded=True, debug=flask_debug)
