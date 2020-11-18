#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File   : console.py
@Author : DEADF1SH_CAT
@Date   : 2020/11/16 20:06

Description:

Usage:

'''

import sys
import os
import re
import argparse
import datetime,time

from celery_app.tasks import *

def init():
    os.system('start powershell -Command ^&{celery -A celery_app worker -l info -P=solo}')
    #os.system('start cmd /k celery -A celery_app worker -l info -P eventlet')  --CMD
    #os.system('gnome-terminal -x bash -c "celery -A celery_app worker -l info") --Ubuntu(未测试)
    #os.system("gnome-terminal -e 'celery -A celery_app worker -l info'") --CentOS(未测试)

def init_redis():
    os.system('start powershell -Command ^&{redis-server config/redis.conf}')
    #os.system('gnome-terminal -x bash -c "redis-server config/redis.conf") --Ubuntu(未测试)

def run(url, start, end, flag):
    result = (PortScanner_T.s(url, start, end, flag) | WebFinger_T.s(url, flag))()
    #result = PortScanner_T.delay(url, start, end, flag)
    print(result.get())

def Console():
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    parser = argparse.ArgumentParser(description='Web Information Collector')
    active_modules = parser.add_argument_group('Active Modules')
    passive_modules = parser.add_argument_group('Passive Modules')
    ext_modules = parser.add_argument_group('Ext Modules')
    data_modules = parser.add_argument_group('Data Modules')

    parser.add_argument('-u','--url',dest="url",default=None,help='目标URL',type=str)
    parser.add_argument('-p','--port',dest="port",default="1-65535",help='待扫描的端口范围(默认1-65535)')
    parser.add_argument('-m','--max',dest="max",default=None,help='最高线程模式(max=100)',action="store_true")
    parser.add_argument('-i','--init',dest="init",default=None,help='初始化环境(Redis/Celery/All)[小写]',type=str)
    
    #主动式收集模块
    active_modules.add_argument('-cms',dest="cms",help="Web应用指纹识别",action="store_true")
    active_modules.add_argument('-portscan',dest="portscan",help="端口扫描",action="store_true")
    active_modules.add_argument('-cdnwaf',dest="cdnwaf",help="CDN/waf识别",action="store_true")

    #被动式收集模块
    passive_modules.add_argument('-subdomain',dest="subdomain",help="子域名收集")
    passive_modules.add_argument('-whois', dest="whois",help="Whois查询",action="store_true")
    passive_modules.add_argument('-cidr', dest="cidr",help="C段扫描")
    # passive_modules.add_argument('-gsil',dest="gsil",help="Github敏感信息收集")

    #数据处理模块
    # data_modules.add_argument('-xls',dest="xls",help="将数据导出为excel")

    args = parser.parse_args()

    if args.max:
        flag = 1
    else:
        flag = 0

    if args.url:
        try:
            url = re.sub('(http|https)://',"",args.url, re.I)
            url = re.sub('/',"",url, re.I)
        except:
            print("Args ERROR!")
            exit()

    if args.port:
        try:
            port = args.port.split("-")
            if len(port) > 2:
                print("Args for Port ERROR!")
                exit()
            else:
                start = port[0]
                end = port[1]
        except:
            start = args.port
            end = args.port

    if args.init == 'redis':
        init_redis()
    elif args.init == 'celery':
        init()
    elif args.init == 'all':
        init()
        init_redis()

    start_time = datetime.datetime.now()

    if args.portscan:
        result = PortScanner_T.delay(url, start, end, flag).get()

    if args.cms:
        if args.portscan:
            WebFinger_T.delay(result,url, flag)
        else:
            WebFinger_T.delay([i for i in range(start,end + 1)],url, flag)

    if args.cdnwaf:
        if args.portscan:
            CDN_WAF_Finger_T.delay(result,url)
        else:
            CDN_WAF_Finger_T.delay([i for i in range(start,end + 1)],url)

    if args.subdomain:
        SubdomainScan_T.delay()

    if args.whois:
        Whois_Scan_T.delay(url)
    
    if args.cidr:
        CIDR_Scan_T.delay()

    # if args.gsil:
    #     GSIL_Scan_T.delay()

    spend_time = (datetime.datetime.now() - start_time).seconds
    print("Total time: " + str(spend_time) + " seconds")