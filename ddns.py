# -*- coding:utf-8 -*-
import time
import sys
import json
import re
import urllib
import urllib2
import logging

# dnspos 的账号密码, 用于api的访问
DNSPOD_ACCOUNT = '4199191@qq.com'
DNSPOD_PASSWORD = ''

# 需要使用 DDNS 服务的域名地址
DOMAIN = 'chenof.com'
SUB_DOMAIN_LIST = ['@', 'www']  # 指定需要修改的主机记录
RECORD_LINE = '默认'  # 记录线路 默认|电信|联通|教育网|百度|搜索引擎 推荐保持默认
REST_TIME = 30  # 同步频率

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', )


def http_request(url, data=()):
    response = None
    try:
        opener = urllib2.Request(url)
        opener.add_header('User-Agent', 'DDNSByDNSPod/1.0(4199191@qq.com)')  # DNSPod要求的User-Agent
        response = urllib2.urlopen(opener, urllib.urlencode(data)).read()
    except urllib2.HTTPError:
        logging.error(url + '地址无法联通')
    except Exception, e:
        logging.error(e)

    return response


def fetch_ip(content):
    result = re.search(
        '((?:(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d))))',
        content)
    if not result:
        return None
    return result.group(0)


def get_wan_ip():
    server_list = (  # 获取wan ip的网站地址, 可以自己添加更多
                     'http://1111.ip138.com/ic.asp',
                     'http://city.ip138.com/ip2city.asp',
                     'http://www.ip38.com/',
    )

    ip = None
    for server in server_list:
        try:
            html = http_request(server)
            ip = fetch_ip(html)
            if not ip:
                raise Exception(server + '响应的内容中无匹配的IP地址')

        except Exception, e:
            logging.error(e)
            continue
        else:
            break

    return ip


class DNSPod():
    common_data = {'format': 'json', 'login_email': DNSPOD_ACCOUNT, 'login_password': DNSPOD_PASSWORD, }

    def __init__(self):
        pass

    def domain_info(self):
        post_data = self.common_data
        post_data['domain'] = DOMAIN

        response = http_request('https://dnsapi.cn/Domain.Info', post_data)
        if not response:
            return None

        return json.loads(response)

    def record_list(self, domain_id):
        post_data = self.common_data
        post_data['domain_id'] = domain_id

        response = http_request('https://dnsapi.cn/Record.List', post_data)
        if not response:
            return None

        return json.loads(response)

    def record_ddns(self, domain_id, record_id, sub_domain, record_line, value):
        post_data = self.common_data
        post_data['domain_id'] = domain_id
        post_data['record_id'] = record_id
        post_data['sub_domain'] = sub_domain
        post_data['record_line'] = record_line
        post_data['value'] = value

        response = http_request('https://dnsapi.cn/Record.Ddns', post_data)
        if not response:
            return None

        return json.loads(response)


def main():
    wan_id = get_wan_ip()
    if not wan_id:
        logging.info('无法获取本地的外网IP')
        return
    d = DNSPod()

    # 获取域名信息
    domain_info = d.domain_info()
    if not domain_info:
        logging.info(DOMAIN + ' 无法获取该域名信息')
        return

    if int(domain_info['status']['code']) == -1:
        logging.error('可能是账号密码不对, 暂停一段时间, 避免被禁')
        time.sleep(1000)  # 账号密码不对的情况下, 暂停一段时间, 避免被禁
        return

    if not int(domain_info['status']['code']) == 1:
        logging.warning(domain_info['status']['message'])
        return

    domain_id = domain_info['domain']['id']

    # 获取域名下的解析记录
    record_list = d.record_list(domain_id)
    if not int(record_list['status']['code']) == 1:
        logging.warning(record_list['status']['message'])
        return

    records = record_list['records']
    if not records:
        logging.info(DOMAIN + ' 无法获取该域名下的记录信息')
        return

    # 过滤部分record
    change_records = []
    for row in records:
        old_ip = fetch_ip(row['value'])
        if not old_ip:
            continue
        if not row['name'] in SUB_DOMAIN_LIST:
            continue

        if old_ip == wan_id:  # 如果跟现在的IP相同则过掉
            continue

        change_records.append(
            {'domain_id': domain_id, 'record_id': row['id'], 'sub_domain': row['name'], 'record_line': RECORD_LINE,
             'value': wan_id, })

    if not change_records:
        return

    # 执行DNS记录修改,实现DDNS
    index = 0
    for row in change_records:
        index += 1
        change_result = d.record_ddns(row['domain_id'], row['record_id'], row['sub_domain'], row['record_line'],
                                      row['value'])
        sub_domain = '' if row['sub_domain'] == '@' else row['sub_domain'] + '.'
        print str(index) + ': ' + sub_domain + record_list['domain']['name'] + ': ' + change_result['status']['message']


while True:
    try:
        main()
    except:
        pass

    time.sleep(REST_TIME)