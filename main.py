# -*- coding:utf-8 -*-
import time
import sys
import re
import urllib2
import traceback
import logging


def get_wan_ip():
    server_list = (  # 获取wan ip的网站地址, 可以执行添加更多
                     'http://1111.ip138.com/ic.asp',
                     'http://city.ip138.com/ip2city.asp',
                     'http://www.ip38.com/',
    )

    ip = None
    for server in server_list:
        try:
            opener = urllib2.urlopen(server)
            result = re.search(
                '((?:(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d))))',
                opener.read())
            if not result:
                raise
            ip = result.group(0)
        except urllib2.HTTPError:
            logging.warning(server + '地址无法联通, 正在尝试其他地址')
        except:
            logging.error(server + '地址无法获取外网ip地址')
            continue
        else:
            break

    return ip


print get_wan_ip()