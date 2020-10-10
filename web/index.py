import csv
import queue
import requests
from tqdm import tqdm

from flask import Flask
from flask import render_template, jsonify
app = Flask(__name__, template_folder='public')

from pymongo import MongoClient
uri = "mongodb://bitcoin_tracing:bt2018@localhost:27017/BT" 
client = MongoClient(uri)
db = client['BT']
mixer_collection = db['mixer']
tager_collection = db['tager']

limit = 5
expand_limit = 2

mixer = {}
tager = {}

@app.route('/')
def index():
    return render_template('html/index.html')

@app.route('/query_graph/<string:address>', methods=['GET'])
def query_graph(address):
    
    if get_transactions_by_address(address, tag_search=False)['valid'] == False:
        return jsonify({'addr_info':{address:{'type':'not_address'}}, 'graph':{}})
    
    graph = bfs_address(address)
    addr_info = {}
    for k in tqdm(list(graph.keys())):
        addr_info[k] = retrive_address(k, from_mem=True)
    return jsonify({'addr_info':addr_info, 'graph':graph})
    
def retrive_address(address, from_mem=False):
    
    res = {}
    res['type'] = 'unknown'
    
    if from_mem:
        if address in mixer.keys():
            res['type'] = 'mixer'
            res['data'] = mixer[address]
            return res
        if address in tager.keys():
            res['type'] = 'tager'
            res['data'] = tager[address]
            return res
    else:
        mix_res = mixer_collection.find_one({'address':address})
        if mix_res != None:
            del mix_res['_id']
            res['type'] = 'mixer'
            res['data'] = mix_res
            return res
        tag_res = tager_collection.find_one({'address':address})
        if tag_res != None:
            del tag_res['_id']
            res['type'] = 'tager'
            res['data'] = tag_res
            return res
    return res

def get_transactions_by_address(address, tag_search=False):
    r = requests.get('https://www.bitgo.com/api/v1/address/%s/tx'%address)
    
    if r.text == 'Checksum does not validate':
        return { 'from':[], 'to':[] , 'valid':False}
    
    print(r.text)
    res = r.json()
    
    txs = res['transactions']
    
    ans = {
        'from':[],
        'to':[],
        'valid':True
    }
    
    in_count = 0
    out_count = 0
    
    if tag_search:
        for tx in tqdm(txs):
            for inp in tx['entries']:
                if inp['account'] != address and retrive_address(inp['account'], from_mem=True)['type'] != 'unknown':
                    ans['from'].append(inp['account'])
                    
            for outs in tx['outputs']:
                if outs['account'] != address and retrive_address(outs['account'], from_mem=True)['type'] != 'unknown':
                    ans['from'].append(outs['account'])

    else:
        for tx in tqdm(txs):
            for inp in tx['entries']:
                if in_count == limit:
                        break
                if inp['account'] != address:
                    ans['from'].append(inp['account'])
                    in_count += 1
                    
            for outs in tx['outputs']:
                if out_count == limit:
                        break
                if outs['account'] != address:
                    ans['to'].append(outs['account'])
                    out_count += 1
    return ans

def bfs_address(address):
    
    graph = {}
    
    q = queue.Queue(maxsize = 1000)
    q.put((address, 0))
    while q.qsize() != 0:
        data = q.get()
        addr = data[0]
        expand = data[1]
        
        
        print(addr, expand)
        
        graph[addr] = {'from':[], 'to':[], 'valid':True}
        
        if expand >= expand_limit:
            continue
        
        res = get_transactions_by_address(addr, tag_search=(expand > 0))
        graph[addr] = res
        
        print(len(res['from']), len(res['to']))
        
        for addr2 in res['from']:
            if addr2 not in graph.keys():
                graph[addr2] = {'from':[], 'to':[], 'valid':True}
                q.put((addr2, expand+1))
        for addr2 in res['to']:
            if addr2 not in graph.keys():
                graph[addr2] = {'from':[], 'to':[], 'valid':True}
                q.put((addr2, expand+1))
    return graph

def read_from_csv():
    print('load mixer')
    with open('../data_loader/Mixer.csv', newline='') as csvfile:

        rows = csv.reader(csvfile)

        for row in rows:
            mixer[row[1]] = row
    
    print('load tager')
    with open('../data_loader/dataset_IEEEBlockchain2018.csv', newline='', encoding="utf-8") as csvfile:

        rows = csv.reader(csvfile)

        for row in rows:
            tager[row[1]] = row

if __name__ == '__main__':
    read_from_csv()
    app.run(host='')
