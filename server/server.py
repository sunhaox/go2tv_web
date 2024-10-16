import json
from flask import Flask, render_template, request
import re
import subprocess
import os
from flask_cors import CORS
from gevent import pywsgi
app = Flask(__name__)
CORS(app)


root_folder = ''


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/ps', methods=['GET', 'POST'])
def shell_ps():
    result = subprocess.run(['ps', '-C', 'go2tv'], capture_output=True, text=True)
    output = result.stdout

    if result.stderr:
        output = result.stderr
        return output
    
    pid_pattern = re.compile(r'\s+(\d+)\s')

    output = pid_pattern.findall(output)
    return output

@app.route('/ls', methods=['GET', 'POST'])
def list_files():
    last_file = ''
    with open('config.json', 'r') as ifile:
        data = json.load(ifile)
        last_file = data['recent']
        
    if request.is_json:
        json_data = request.get_json()
        
        folder = json_data['folder']
    
        file_paths = get_files_and_folders(root_folder + folder, last_file)
        
        return file_paths
    else:
        raw_data = request.get_data(as_text=True)
        print(raw_data)
    return "123"

def get_files_and_folders(folder, last_file = ''):
    file_paths = {}
    file_paths['files'] = []
    file_paths['folders'] = []
    
    if folder.startswith(root_folder):
        path = folder[len(root_folder):]
    else:
        path = folder
    file_paths['path'] = path
    
    with os.scandir(folder) as entries:
        for file_path in entries:
            if file_path.is_file():
                if (file_path == last_file):
                    file_paths['files'].append(file_path.name + "*")
                else:
                    file_paths['files'].append(file_path.name)
            else:
                file_paths['folders'].append(file_path.name)
    
    file_paths['files'].sort()
    file_paths['folders'].sort()
    return file_paths

@app.route('/go2tv_l', methods=['GET', 'POST'])
def shell_go2tv_l():
    result = subprocess.run(['go2tv', '-l'], capture_output=True, text=True)
    output = result.stdout
    
    '''
    Device 1
    --------
    Model: 咪咕投屏-20F
    URL:   http://192.168.1.5:53141/upnp/dev/a003a3a7de2f31af96041aac27414292/desc

    Device 2
    --------
    Model: 魔百和_11820F
    URL:   http://192.168.1.5:25826/description.xml
    '''

    if result.stderr:
        output = result.stderr
        return output
    else:
        pattern = r'Model: (.*)\nURL:\s+(.*)'
        
        # There are some invisible chars need to remove first
        sub1_chr = [chr(27), chr(91), chr(48), chr(109)]
        sub1_str = ''.join((chr) for chr in sub1_chr)
        
        sub2_chr = [chr(27), chr(91), chr(49), chr(109)]
        sub2_str = ''.join((chr) for chr in sub2_chr)
        
        output = output.replace(sub1_str, '')
        output = output.replace(sub2_str, '')

        matches = re.findall(pattern, output)
        output = {'devices': []}

        for match in matches:
            output['devices'].append({'model': match[0], 'URL': match[1]})

    print(output)
    return output
    # For test
    # return {"devices": [
    #     {'model': 'models1', 'url': 'http://example.com/xml'},
    #     {'model': 'models2', 'url': 'http://example.com/xml'}
    # ]}

@app.route('/go2tv_s', methods=['GET', 'POST'])
def shell_go2tv_s():
    if request.is_json:
        json_data = request.get_json()
        
        url = json_data['url']
        fileName = json_data['filename']
        filePath = root_folder + fileName
    
        completion = subprocess.Popen(['go2tv', '-t', url, '-v', filePath], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # store the filename in config file
        with open('config.json', 'r') as ifile:
            data = json.load(ifile)
            
            data['recent'] = fileName
            
            with open('config.json', 'w') as ofile:
                json.dump(data, ofile, indent=4)
 
        return str(completion.pid)
    else:
        raw_data = request.get_data(as_text=True)
        print(raw_data)
    return "123"

@app.route('/df', methods=['GET', 'POST'])
def shell_df():
    sdx = ''
    with open('config.json', 'r') as ifile:
        data = json.load(ifile)
        sdx = data['sdx']
    
    result = subprocess.run(['df', '-h'], capture_output=True, text=True)
    output = result.stdout

    if result.stderr:
        output = result.stderr
        return output
    
    str_list = output.split('\n')
    for str in str_list:
        if str.startswith(sdx):
            match = re.search(r'\S+\s+(\S+)\s+(\S+)\s+\S+\s+(\S+)\s+\S+', str)
            if match:
                total = match.group(1)
                used = match.group(2)
                persent = match.group(3)
                persent = int(persent[:-1])
                return {'total': total, 'used': used, 'persent': persent}
    
    return {'total': 'x', 'used': 'x', 'persent': 0}

@app.route('/kill', methods=['GET', 'POST'])
def shell_kill():
    if request.is_json:
        json_data = request.get_json()
        
        pid = json_data['pid']
    
        result = subprocess.run(['kill', pid], capture_output=True, text=True)
        output = result.stdout

        if result.stderr:
            output = result.stderr
            return output
        
        return output
    else:
        raw_data = request.get_data(as_text=True)
        print(raw_data)
    return "123"

@app.route('/delete', methods=['GET', 'POST'])
def delete_file():
    if request.is_json:
        json_data = request.get_json()
        
        fileName = json_data['file']
        
        # TODO: handle the error
        if os.path.isfile(root_folder + fileName):
            os.remove(root_folder + fileName)
        elif os.path.isdir(root_folder + fileName):
            os.rmdir(root_folder + fileName)
        
        return ''
    else:
        raw_data = request.get_data(as_text=True)
        print(raw_data)
        return raw_data

if __name__ == '__main__':
    
    # check the config file
    if (not os.path.exists("config.json")):
        # create the config file if not exist
        data = {}
        data['recent'] = ''
        data['root'] = '/storage/media/'
        data['sdx'] = '/dev/sda1'
        with open('config.json', 'w') as ofile:
            json.dump(data, ofile, indent=4)
    else:
        with open('config.json', 'r') as ifile:
            data = json.load(ifile)
            root_folder = data['root']
    
    # app.run(debug=True, port=8088)
    server = pywsgi.WSGIServer(('0.0.0.0', 8088), app)
    server.serve_forever()
