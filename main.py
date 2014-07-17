#!/usr/bin/env python3

import json
import os
import os.path
import urllib.parse

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
app = Flask(__name__)

import requests

from ini_parser import ini_parser

# logger shortcut
debug = app.logger.debug
warn = app.logger.warning
error = app.logger.error


#################### settings ####################
HOST, PORT = '0.0.0.0', 8000
UPLOAD_DIR = './upload/'
DEBUG = True


#################### utils ####################
def parse_headers(headers):
    """Multi-line string of headers -> dict"""
    rst = {}
    for line in headers.split('\n'):
        entry = line.split(':')
        if len(entry) < 2: continue
        rst.update({entry[0].strip(): entry[1].strip()})
    return rst


#################### routing ####################
@app.route('/hello/<name>', methods=['GET'])
def hello_get(name):
    return render_template('hello.html')


@app.route('/hello/<name>', methods=['POST'])
def hello_post(name):
    #print(request.data)
    #print(request.form)
    #print(request.headers)
    data = dict(urllib.parse.parse_qsl(request.data.decode()))
    return 'haha ' + name + ' : ' + data['name']


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')

    if request.method == 'POST':
        file = request.files['file']
        if not file:
            return render_template(
                'upload.html',
                error='Please select a valid file.'
            )

        filename = request.form['filename']
        full_name = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(full_name):
            return render_template(
                'upload.html',
                error='File already exists.'
            )
        file.save(full_name)
        return redirect(url_for('index'))


#################### AJAX end ####################
@app.route('/action', methods=['POST'])
def action():
    url = request.form['url']
    method = request.form['method']
    headers = request.form.get('headers', '')
    data = request.form.get('data', '')

    if   method == 'GET':       query_func = requests.get
    elif method == 'POST':      query_func = requests.post
    elif method == 'PUT':       query_func = requests.put
    elif method == 'DELETE':    query_func = requests.delete
    else:
        return 'Unknown method.', 500

    headers = parse_headers(headers)

    print(headers)
    print(data)
    r = query_func(url, data=data, headers=headers)

    print(dict(r.headers))
    ret = {
        'status_code': r.status_code,
        'headers': dict(r.headers),
        'data': r.text,
    }
    return json.dumps(ret)


@app.route('/get_list', methods=['GET'])
def get_list():
    ret = []
    for filename in os.listdir(UPLOAD_DIR):
        apis = ini_parser(os.path.join(UPLOAD_DIR, filename))
        ret.append({
            'name': os.path.splitext(filename)[1],
            'apis': apis,
        })
    return json.dumps(ret)


#################### main ####################
def main():
    if not os.path.exists(UPLOAD_DIR):
        os.mkdir(UPLOAD_DIR)

    app.run(
        host = HOST, port = PORT,
        threaded = True,
        debug = DEBUG,
    )


if __name__ == '__main__':
    main()
