#!/usr/bin/env python3

import json
import os
import os.path
import urllib.parse
import subprocess

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
app = Flask(__name__)

import requests

#from ini_parser import ini_parser

# logger shortcut
debug = app.logger.debug
warn = app.logger.warning
error = app.logger.error


#################### settings ####################
HOST, PORT = '0.0.0.0', 7788
UPLOAD_DIR = './upload/'
DEBUG = True

db_host = "openmtc.darkgerm.com"  
db_usr = "yb"  
db_passwd = "iloveliny"
db_name = "easyconnect"
db_port = 3306

#################### utils ####################

def sql_query(SQL):
    #result = subprocess.Popen('mysql -h%s -u%s -p%s -D%s -Bse%s' %(db_host, db_usr, db_passwd, db_name, SQL), stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
    p = subprocess.Popen([
        'mysql',
        '-h' + db_host,
        '-s',
        '-u' + db_usr,
        '-p' + db_passwd,
        '-D' + db_name,
    ], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    return p.communicate(input=SQL.encode())[0].decode()

@app.route('/device_mapping', methods=['GET'])
def device_mapping():
    input_devices = {} 
    output_devices = {} 
    mapping_functions = []
    input_device_SQL = """   
                          SELECT dm_name, df_name FROM DeviceModel
                          LEFT JOIN ModelFeature USING (dm_id)
                          LEFT JOIN DeviceFeature USING (df_id)
                          WHERE type='input';
                       """
    functions_SQL = """   
                        SELECT mf_name FROM MappingFunc;
                    """
    output_device_SQL = """   
                           SELECT dm_name, df_name FROM DeviceModel
                           LEFT JOIN ModelFeature USING (dm_id)
                           LEFT JOIN DeviceFeature USING (df_id)
                           WHERE type='output';
                        """

    device_result = sql_query(input_device_SQL)
    result_list = device_result.split("\n")
    for i in result_list:
        data = i.split("\t")
        if data[0]:
            if data[0] in input_devices:
                input_devices[data[0]].append(data[1].strip())
                continue
            input_devices.update({data[0].strip(): [data[1].strip()]})

    functions_result = sql_query(functions_SQL)
    mapping_functions = functions_result.split("\n")
    mapping_functions = filter(None, mapping_functions)
   
    device_result = sql_query(output_device_SQL)
    result_list = device_result.split("\n")
    for i in result_list:
        data = i.split("\t")
        if data[0]:
            if data[0] in output_devices:
                output_devices[data[0]].append(data[1].strip())
                continue
            output_devices.update({data[0].strip(): [data[1].strip()]})


    return render_template('device_mapping.html', 
                             input_devices = input_devices,
                             mapping_functions = mapping_functions,
                             output_devices = output_devices)


@app.route('/connection', methods=['GET'])
def connection():
    return render_template('connection.html')
	

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
        #apis = ini_parser(os.path.join(UPLOAD_DIR, filename))
        ret.append({
            'name': os.path.splitext(filename)[1],
            'apis': apis,
        })
    return json.dumps(ret)


