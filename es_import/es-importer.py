#!/usr/bin/python
import json
import http.client
import os
import argparse
import logging
import sys


def _set_es_host_and_port(es_host, es_port):
    global ES_HOST
    global ES_PORT
    ES_HOST = es_host
    ES_PORT = es_port


def read_file(filename):
    f_path = "{}/{}".format(os.path.dirname(os.path.realpath(__file__)), filename)
    logging.info("Reading file: {}".format(f_path))
    with open(f_path, "r") as f:
        file_content = f.read()
    f.close()
    return file_content


def send_api_request(uri, body_dict):
    logging.info("Executing API call: http://{}:{}{}".format(ES_HOST, ES_PORT, uri))
    conn = http.client.HTTPConnection(ES_HOST, ES_PORT)
    headers = {'Content-type': 'application/json'}
    json_data = json.dumps(body_dict)
    conn.request('PUT', uri, json_data, headers)
    response = conn.getresponse()
    logging.info(response.read().decode())


def load_index_templates():
    res = json.loads(read_file("index_templates.json"))
    logging.info("Loading index templates")
    for key, value in res.items():
        uri = "/_template/{}".format(key)
        send_api_request(uri, value)


def load_index_patterns():
    index_patterns_names = json.loads(read_file("index_patterns_names.json"))
    index_pattern = json.loads(read_file("index_pattern.json"))
    logging.info("Loading index patterns and index patterns names")
    for index_pattern_name in index_patterns_names:
        uri = "/.kibana/index-pattern/{}".format(index_pattern_name)
        index_pattern['title'] = index_pattern_name
        send_api_request(uri, index_pattern)


if __name__ == '__main__':
    log_format = '[%(asctime)s %(levelname)s] %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        stream=sys.stdout
    )
    parser = argparse.ArgumentParser()
    parser.add_argument('es_host', nargs='?', default=None, help="ElasticSearch host")
    parser.add_argument('es_port', nargs='?', default=9200, help="ElasticSearch port")
    args = parser.parse_args()
    if args.es_host is None:
        logging.error("Missing ElasticSearch HOST. Usage example: es-importer.py 127.0.0.1 9200")
        parser.print_help()
        exit(1)
    if args.es_port is None:
        logging.error("Missing ElasticSearch PORT. Usage example: es-importer.py 127.0.0.1 9200")
        parser.print_help()
        exit(1)
    _set_es_host_and_port(args.es_host, args.es_port)
    load_index_templates()
    load_index_patterns()
