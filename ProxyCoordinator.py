#!/usr/vin/env python3
# -*- coding: utf-8 -*-

' this module used to manage proxies'

__author__ = "Mr.Bingo"
__version__ = "0.1"

import requests
import re
import threading
import queue

# 1 导入Proxy列表       # 文件导入
# 2 处理策略：
#   2.1 限定代理的使用次数    # todo 先实现这一种
#   2.2 对单一目标(ip:port)限定代理的使用次数
#   2.3 指定判断条件：指定方法(GET或HEAD）访问目标某URL，得到200反应。

# 管理代理池
class ProxyCoordinator(object):
    def __init__(self, multipletimes=1):
        self.ipViewURL = "http://api.ipify.org"
        self.localPublicIP = self.getPublicIP()
        self.proxyDict = {}
        self.availableTimes = multipletimes     # 每个代理可被使用的次数
        self.rawProxyList = queue.Queue()
        self.proxyDictUsage = {}     # 每个目标作为一个key,value为各自的一个proxyDict。

        print("本地IP :: "+ self.localPublicIP)


    def importPorxies(self,proxyListFile):
        """导入Proxy列表文件,一行一个proxy:
        http://127.0.0.1:8080
        https://10.20.30.40:999
        """
        print("导入代理池:::\t%s"%proxyListFile)
        with open(proxyListFile,'r') as f:
            for line in f.readlines():
                try:
                    proxy = re.match(r"^https?://(\d{1,3}[\.:]){4}\d+$", line.lower()).group()
                    self.rawProxyList.put(proxy)
                except:
                    pass
            thread_arr=[]
            for i in range(50): # 多线程进行代理可用性及匿名性验证
                t = threading.Thread(target=self.__verifyAndImportProxy)
                thread_arr.append(t)
            for t in thread_arr:
                t.start()
            for t in thread_arr:
                t.join()
        print("导入完成")

    def getPublicIP(self, proxy=None):
        """获取通过Proxy上网的公网IP地址，若Proxy为None，则获取本地主机的公网IP"""
        if proxy is None:   # 获取本地IP
            r = requests.get(self.ipViewURL, timeout=15)
            return r.text
        else:
            try:
                proxy = re.match(r"^https?://(\d{1,3}[\.:]){4}\d+$", proxy.lower().replace(' ', '')).group()
                r = requests.get(self.ipViewURL, proxies={proxy.split("://")[0]: proxy}, verify=False, timeout=15)
                # logging.info("返回数据:%s" % r.text.replace(' ', '')[:300])
                ip = re.match(r"((\d{1,3}\.){3}\d{1,3})", r.text.replace(' ', '')).group()
                # logging.info(" IP :%s" % ip)
                return ip
            except:
                return None

    def __verifyAndImportProxy(self):
        while not self.rawProxyList.empty():
            proxy = self.rawProxyList.get()
            if self.proxyDict.get(proxy) is None:   # 判断是否已经读取(proxy列表可能存在重复)
                currentIP = self.getPublicIP(proxy)
                if (currentIP != self.localPublicIP) and (currentIP is not None):
                    self.proxyDict[proxy] = self.availableTimes
                    print("%s\t::\t%s\t|%d"%(proxy,currentIP,self.rawProxyList.qsize()))
                else:
                    self.proxyDict[proxy] = 0

    def dispatchProxy(self, target=None):
        """为某个目标主机分配代理"""
        if target is None:
            target = "DefaultTarget"

        if target not in self.proxyDictUsage: # 针对该target进行代理字典的初始化
            dict = {}
            for item in self.proxyDict:
                if self.proxyDict[item] > 0:
                    dict[item] = self.proxyDict[item]
            self.proxyDictUsage[target] = dict
            if len(dict) <= 0:
                return None

        for item in self.proxyDictUsage[target]:
            if self.proxyDictUsage[target][item] > 0:
                self.proxyDictUsage[target][item] -= 1
                return item
        return None

if __name__=="__main__":
    pc = ProxyCoordinator(multipletimes=2)
    pc.importPorxies("../../pythonCode/kuaidaili_list.txt")

    target1 = ("10.1.1.1", 80)
    target2 = ("20.2.2.2", 8080)

    print("\t\t\ttarget1")
    while True:
        proxy = pc.dispatchProxy(target1)
        if proxy:
            print(proxy)
        else:
            print('无可用Proxy')
            break

    print("\t\t\ttarget2")
    while True:
        proxy = pc.dispatchProxy(target2)
        if proxy:
            print(proxy)
        else:
            print('无可用Proxy')
            break
