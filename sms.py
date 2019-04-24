#/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import httplib

def sendsms_confirm_hotel(mobile, price):
    content = price + ''
    sendtriggersms(mobile, content, 3593)

def sendsms_to_hotel(mobile, price, nights, roomcnt, extnum=None):
    content = price+'|'+nights+'|'+roomcnt
    sendtriggersms(mobile, content, 3578, extnum)

def sendsms(mobile, hotel, roomtype, price):
    content = hotel+'|'+roomtype+'|'+price
    sendtriggersms(mobile, content, 3459)

def sendcode(mobile, code):
    sendtriggersms(mobile, code, 3387)

def sendtriggersms(mobile, content, codeid, extnum=None):
    httpClient = None
    try:
        params = {
            'action':'code',
            'username':'',
            'userpass':'',
            'mobiles':mobile,
            'content':content,
            'codeid':codeid,
            }
        if extnum:
            params['extnum'] = extnum
        print params
        params = urllib.urlencode(params)
        headers = {
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"}
        httpClient = httplib.HTTPConnection("sms.jiangukj.com", 80, timeout=30)
        httpClient.request("POST", "/SendSms.aspx", params, headers)
        response = httpClient.getresponse()
        print response.status
        print response.reason
        print response.read()
        print response.getheaders()
    except Exception as e:
        print e
    finally:
        if httpClient:
            httpClient.close()

if __name__ == '__main__':
    sendsms('13818888888', '希尔顿', '大床房', '250')
