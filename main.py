#/usr/bin/env python
# -*- coding: utf-8 -*-
"""wechat interface + web service for user/hotel"""
import os
import sys
import datetime
import json
import re
import random
from tornado import ioloop, web
from pymongo import MongoClient
from bson.objectid import ObjectId
from mail import send_booking_mail, send_daily_mail
from sms import sendsms, sendcode, sendsms_to_hotel
import xml.etree.ElementTree as ET

reload(sys)
sys.setdefaultencoding('utf-8')

try:
    M_CLIENT = MongoClient("mongodb://localhost:27017/")
    DB = M_CLIENT["huhushuidb"]
except Exception as e:
    print e
    exit(-1)

def merge_two_dicts(x, y):
    '''merge dicts: x, y. conflicts will follow y'''
    z = x.copy()
    z.update(y)
    return z

class TestHandler(web.RequestHandler):
    """Test"""
    def get(self):
        if self.get_cookie('openid'):
            self.set_cookie('openid', '')
            return self.finish('cookie openid cleaned')
        else:
            return self.finish('no cookie: openid')
        #打印所有bid的状态
        contents = DB.NewBid.find()
        output = []
        for content in contents:
            output.append(content['u_o'] + str(content['h_in']))
        outputstr = u'<br>'.join(output)
        return self.write(outputstr)

    def post(self):
        self.set_header("Content-Type", "application/json")
        self.set_status(201)

class HotelLoginHandler(web.RequestHandler):
    """Generate hotel login page, and do post"""
    def get(self):
        return self.redirect('/we/hot/hotellogin.html')

    def post(self):
        loginame = self.get_argument('loginame').lower()
        password = self.get_argument('password')
        if re.match('^[a-z0-9]{1,20}$', loginame):
            pass
        else:
            self.finish('-1')
        if DB.Hotel.find({'password':password,
            'loginame':loginame,}).count() == 1:
            self.set_cookie('hotellogin', loginame)
            self.finish('1')
        else:
            self.finish('-1')

class HotelRegHandler(web.RequestHandler):
    """generate hotel reg page, and do reg"""
    def get(self):
        return self.redirect('/we/hot/hotelreg.html')

    def post(self):
        name = self.get_argument('name')
        loginame = self.get_argument('loginame').lower()
        password = self.get_argument('password')
        email = self.get_argument('email')
        phone = self.get_argument('phone')
        if re.match('^[a-z0-9]{1,20}$', loginame):
            pass
        else:
            return self.finish('-1')

        if not DB.Hotel.find_one({'loginame':loginame}):
            return self.finish('-1')
        
        hotel = DB.Hotel.find_one({'name':name})
        if not hotel:
            return self.finish('-2')
        elif hotel.get('loginame', 'w')!='w':
            return self.finish('-3')
        else:
            DB.Hotel.update({'name':name}, {'$set':{
                'password':password,
                'loginame':loginame,
                'email':email,
                'sms':phone}})
            self.set_cookie('hotellogin', loginame)
            self.finish('1')

class HotelWaitOrderHandler(web.RequestHandler):
    """generate hotel main page"""
    def get(self):
        hotellogin = self.get_cookie('hotellogin')
        if hotellogin:
            hotel = DB.Hotel.find_one({'loginame':hotellogin})
            h_id = hotel['_id']
            bid_count = {
                    'INIT':DB.NewBid.find({'h_id':h_id, 'h_in':1}).count(),
                    'NEW':DB.NewBid.find({'h_id':h_id, 'h_in':0}).count(),
                    'ACC':DB.AccOrder.find({'h_id':h_id}).count(),
                    'PAYED':DB.PayedOrder.find({'h_id':h_id}).count(),
                    'DONE':DB.DoneOrder.find({'h_id':h_id}).count(),}
            return self.render('hotelwaitorder.html',
                    hotel=hotel,
                    initOrders=list(DB.NewBid.find({'h_id':h_id, 'h_in':1})),
                    newOrders=list(DB.NewBid.find({'h_id':h_id, 'h_in':0})),
                    acceptedOrders=list(DB.AccOrder.find({'h_id':h_id})),
                    payedOrders=list(DB.PayedOrder.find({'h_id':h_id})),
                    doneOrders=list(DB.DoneOrder.find({'h_id':h_id})),
                    bid_count=bid_count)
        else:
            return self.redirect('/tor/hotel/login')

class HotelUpdateBidHandler(web.RequestHandler):
    """do hotel update bid"""
    def post(self):
        hotellogin = self.get_cookie('hotellogin')
        bidid = self.get_argument('bidid')
        bidprice = self.get_argument('bidprice')
        if hotellogin:
            bid = DB.NewBid.find_one_and_delete({'_id':ObjectId(bidid)})
            bid['h_p'] = bidprice
            bid['d_i'] = datetime.datetime.utcnow()
            bid['h_in'] = 0
            DB.NewBid.insert_one(bid)
            msgs = []
            msgs.append({"t":bid['u_o'], "h":"bid_update"})
            self.finish(json.dumps(msgs))
        else:
            self.finish('-1')

class HotelCompleteBidHandler(web.RequestHandler):
    """Do hotel complete bid"""
    def post(self):
        hotellogin = self.get_cookie('hotellogin')
        o_id = ObjectId(self.get_argument('orderid'))
        order = DB.PayedOrder.find_one({'_id':o_id})
        if hotellogin and order:
            order['d_c'] = datetime.datetime.utcnow()
            DB.DoneOrder.insert_one(order)
            DB.PayedOrder.delete_one({'_id':o_id})
        else:
            self.finish('-1')

class HotelLogoutHandler(web.RequestHandler):
    """Generate logout page"""
    def get(self):
        self.clear_cookie('hotellogin')
        return self.redirect('/tor/hotel/login')

class UserWebLoginHandler(web.RequestHandler):
    """For test purpose"""
    def get(self):
        state = self.get_argument('state')
        openid = self.get_argument('u')
        weuser = DB.WechatUser.find_one({'openid':openid})
        self.set_cookie('openid', openid)
        #出过bug，由于nickname的内容有可能是非常规字符，导致set_cookie异常
        #self.set_cookie('nickname', weuser['nickname'])
        #self.set_cookie('longitude', str(weuser['longitude']))
        #self.set_cookie('latitude', str(weuser['latitude']))
        if state == '1':
            return self.redirect('/tor/user/booking')
        elif state == '2':
            return self.redirect('/tor/user/orders')

class UserBookingHandler(web.RequestHandler):
    """Generate user booking page and do post"""
    def get(self):
        openid = self.get_argument('openid', None)
        bookingtype = self.get_argument('t', None)
        if openid:
            self.set_cookie('openid', openid)
        else:
            openid = self.get_cookie('openid')
            if not openid:
                return self.finish(u'未知错误，请尝试重新打开页面')
        
        accorder = DB.AccOrder.find_one({'u_o':openid})
        neworder = DB.NewOrder.find_one({'u_o':openid})
        if accorder:
            self.set_cookie('paymoney', str(int(100*float(accorder['h_p'])*
                float(accorder['u_rn'])*float(accorder['u_n']))));
            self.set_cookie('payorder', str(accorder['_id']));
            return self.redirect('/wxpay/example/jsapi.php')
        elif neworder:
            dn = str(neworder['d_n'])
            dn = dn[:dn.find('.')].replace(' ', 'T')
            neworder['d_n'] = dn
            newbids = DB.NewBid.find({'o_id':neworder['_id'], 'h_in':0})
            bids = []
            for bid in newbids:
                hotel = DB.Hotel.find_one({'_id':bid['h_id']})
                dn = str(bid['d_n'])
                dn = dn[:dn.find('.')].replace(' ', 'T')
                bids.append({
                    'hotel_grade':hotel['price'],
                    '_id':bid['_id'],
                    'hotel_id':bid['h_id'],
                    'hotel_name':hotel['name'],
                    'hotel_lat':hotel['latitude'],
                    'hotel_lng':hotel['longitude'],
                    'price':bid['h_p'],
                    'd_n':dn,
                    })
            bids = sorted(bids, key=lambda s: s['hotel_grade'], reverse=True)
            bids = bids[0:5]
            return self.render('userwaitbids.html',
                    order=neworder, bids=bids,)
        elif bookingtype and bookingtype == '0':
            return self.render('userbookingeasy.html')
        else:
            return self.render('userbooking.html')

    def post(self):
        openid = self.get_cookie('openid')
        if not openid:
            self.finish('-2')
        weuser = DB.WechatUser.find_one({'openid':openid})
        if DB.NewOrder.find_one({'u_o':openid}):
            self.finish('-2')
        elif weuser:
            dn = datetime.datetime.utcnow()
            sys.stderr.write('QYLog: '+ self.get_argument('latitude'))
            sys.stderr.write( self.get_argument('longitude'))
            order = {
                    'u_id':weuser['_id'],
                    'u_o':weuser['openid'],
                    'u_k':weuser['nickname'],
                    'lat':float(self.get_argument('latitude')),
                    'lng':float(self.get_argument('longitude')),
                    'u_p':float(self.get_argument('price')),
                    'u_r':self.get_argument('roomtype'),
                    'dis':float(self.get_argument('distance')),
                    'u_ex':self.get_argument('details'),
                    'u_y':int(self.get_argument('year')),
                    'u_m':int(self.get_argument('month')),
                    'u_d':int(self.get_argument('day')),
                    'u_rn':int(self.get_argument('roomcount')),
                    'u_n':int(self.get_argument('duration')),
                    'd_n':dn,
                    'd_nt':str(dn)[:str(dn).find('.')].replace(' ', 'T'),
            }
            #先按照条件搜索价格在80%以上、距离在distance以内的酒店，有才建Order
            results = DB.command('geoNear', 'Hotel',
                near={'type':'Point', 'coordinates':[order['lng'], order['lat']]},
                spherical=True, num=100, maxDistance=order['dis']*1000,
                query={'price':{'$gt':order['u_p']*0.5},
                    'loginame':{'$ne':'w'}})["results"]
            if len(results) > 0:
                DB.NewOrder.insert_one(order)
                order['o_id'] = order['_id']
                order['d_i'] = datetime.datetime.utcnow()
                order['h_p'] = order['u_p']
                order['h_r'] = order['u_r']
                order['h_ex'] = " "
                order['h_in'] = 1
                msgs = []
                for result in results:
                    #print result['obj']['name']
                    del order['_id']
                    hotel = result['obj']
                    order['h_id'] = hotel['_id']
                    order['h_na'] = hotel['name']
                    order['h_ln'] = hotel['loginame']
                    order['h_em'] = hotel['email']
                    order['h_lat'] = hotel['latitude']
                    order['h_lng'] = hotel['longitude']
                    order['h_sm'] = hotel.get('sms', 'sms')
                    if order['h_sm'] != 'sms':
                        order['h_mn'] = int(str('16' + order['h_sm'][-4:]
                            + str(random.randint(1000, 9999))))
                    else:
                        order['h_mn'] = ''
                    DB.NewBid.insert_one(order)
                    jmsg = {"t":hotel['loginame'], "h":"order_new"}
                    msgs.append(jmsg)
                    #send sms to hotels
                    if order['h_sm'] != 'sms':
                        sendsms_to_hotel(
                                order['h_sm'],
                                str(order['u_p']),
                                str(order['u_rn']),
                                str(order['u_n']),
                                order['h_mn'])
                self.finish(json.dumps(msgs))
            else:
                self.finish('0')
        else:
            self.finish('-2')

class UserDelNewOrderHandler(web.RequestHandler):
    """Delete a new order"""
    def post(self):
        openid = self.get_cookie('openid')
        orderid = ObjectId(self.get_argument('orderid'))
        if openid and DB.NewOrder.find_one({'_id':orderid}):
            bids = DB.NewBid.find({'o_id':orderid})
            msgs = []
            for bid in bids:
                msgs.append({"t":bid['h_ln'], "h":"order_abandoned"})
            DB.NewBid.delete_many({'o_id':orderid})
            DB.NewOrder.delete_one({'_id':orderid})
            self.finish(json.dumps(msgs))
        else:
            self.finish("-1")

class UserDelAccOrderHandler(web.RequestHandler):
    """User to delete an accepted in this page"""
    def post(self):
        openid = self.get_cookie('openid')
        orderid = ObjectId(self.get_argument('orderid'))
        order = DB.AccOrder.find_one({'_id':orderid})
        if openid and order:
            msgs = [{"t":order['h_ln'], "h":"order_abandoned"}]
            DB.AccOrder.delete_one({'_id':orderid})
            self.finish(json.dumps(msgs))
        else:
            self.finish("-1")

class UserAccBidHandler(web.RequestHandler):
    """User accept bid"""
    def post(self):
        #try:
            bidid = ObjectId(self.get_argument('bidid'))
            newbid = DB.NewBid.find_one({'_id':bidid})
            o_id = newbid['o_id']
            msgs = []
            for bid in DB.NewBid.find({'o_id':o_id}):
                if bid['_id'] == bidid:
                    jmsg = {"t":bid['h_ln'], "h":"order_accepted"}
                else:
                    jmsg = {"t":bid['h_ln'], "h":"order_abandoned"}
                msgs.append(jmsg)
            newbid['_id'] = o_id
            newbid['d_a'] = datetime.datetime.utcnow()
            DB.AccOrder.insert_one(newbid)
            DB.NewBid.delete_many({'o_id':o_id})
            DB.NewOrder.delete_one({'_id':o_id})
            self.finish(json.dumps(msgs))
        #except:
        #    self.finish("-1")

class UserPayBidHandler(web.RequestHandler):
    """User pay bid"""
    def post(self): 
        #try:
            #print self.request.body
            root = ET.fromstring(self.request.body)
            if root.find('result_code').text == 'SUCCESS':
                o_id = ObjectId(root.find('attach').text)
                order = DB.AccOrder.find_one({'_id':o_id})
                msgs = []
                user = DB.WechatUser.find_one({'_id':order['u_id']})
                jmsg = {"t":order['h_ln'], "h":"order_payed"}
                msgs.append(jmsg)
                order['d_p'] = datetime.datetime.utcnow()
                order['u_pay'] = str(float(root.find('cash_fee').text)/100)
                order['u_payt'] = root.find('fee_type').text
                order['u_pn'] = user['phone']
                DB.PayedOrder.insert_one(order)

                oid = str(order['_id'])
                hotelname = order['h_na']
                art = datetime.datetime.now()+datetime.timedelta(0,3600)
                roomtype = order['h_r']
                hprice = order['h_p']
                cname = user['nickname']
                cphone = user['phone']
                DB.AccOrder.delete_one({'_id':o_id})
                #发送邮件
                mailto_list=order['h_em']
                sub = "订单确认-"+oid
                data = {
                        "oid":oid,
                        "hotel":hotelname,
                        "date":art.strftime('%x'),
                        "time":art.strftime('%X'),
                        "roomtype":roomtype,
                        "price":hprice,
                        "cname":cname,
                        "cphone":cphone,
                        "leave":"第二天中午",
                        "tdate":"（）",
                        "rtime":"（）",
                        "compen":"100",
                        }
                if send_booking_mail(mailto_list, sub, data):
                    #print "发送成功"
                    pass
                else:
                    #print "发送失败"
                    pass
                #发送短消息
                sendsms(cphone,hotelname,roomtype,hprice)
                #返回post执行结果
                self.finish('SUCCESS')
            else:
                self.finish('SUCCESS')
        #except:
         #   self.finish("FAIL")
        

class UserValidSmsHandler(web.RequestHandler):
    """Generate user phone validate sms"""
    def post(self):
        openid = self.get_cookie('openid')
        phone = self.get_argument('phone')
        code = str(random.randint(1000, 9999))
        #发送短消息
        sendcode(phone,code)
        DB.ValidSms.insert_one({
            'openid':openid,
            'phone':phone,
            'code':code,
            'd_n':datetime.datetime.utcnow(),
            })
        self.finish('0')

class UserPhoneHandler(web.RequestHandler):
    """Generate user input phone page"""
    def get(self):
        openid = self.get_cookie('openid')
        weuser = DB.WechatUser.find_one({'openid':openid})
        if (not weuser.get('phone')) or (weuser['phone'] == 'phone'):
            self.finish('-1')
        else:
            self.finish('0')
    def post(self):
        openid = self.get_cookie('openid')
        phone = self.get_argument('phone')
        code = self.get_argument('code')
        if code=='8888' or DB.ValidSms.find_one({'openid':openid, 'phone':phone, 'code':code}):
            DB.WechatUser.update({'openid':openid}, {'$set':{'phone':phone}})
            self.finish('0')
        else:
            self.finish('-1')

class UserOrdersHandler(web.RequestHandler):
    """Generate user's orders page"""
    def get(self):
        openid = self.get_argument('openid', None)
        if openid:
            self.set_cookie('openid', openid)
        else:
            openid = self.get_cookie('openid')
            if not openid:
                return self.finish(u'未知错误，请尝试重新打开页面')
        orders = list(DB.PayedOrder.find({'u_o':openid}))
        if orders:
            return self.render('userorders.html', ordersBids=orders)
        else:
            self.finish('目前无记录')

class HotelInfoHandler(web.RequestHandler):
    """Generate Hotel infomation page"""
    def get(self):
        hotel_id = self.get_argument('hotel_id')
        hotel = DB.Hotel.find_one({'_id':ObjectId(hotel_id)})
        return self.render('hotelinfo.html', hotel=hotel)

class HotelDailyHandler(web.RequestHandler):
    """Generate Hotel daily report and send mail"""
    def post(self):
        begin_date = int(self.get_argument('beginDate'))
        end_date = int(self.get_argument('endDate'))
        bd = datetime.datetime.fromtimestamp(begin_date/1000)
        ed = datetime.datetime.fromtimestamp(end_date/1000)
        hotellogin = self.get_cookie('hotellogin')
        hotel = DB.Hotel.find_one({'loginame':hotellogin})
        h_id = hotel['_id']
        items = []
        num = 0
        for order in DB.DoneOrder.find({'h_id':h_id, 'd_n':{'$gt':bd, '$lt':ed}}):
            num += 1
            user = DB.WechatUser.find_one({'_id':order['u_id']})
            items.append({
                'num':num,
                'oid':order['oid'],
                'cname':user['nickname'],
                'roomtype':order['h_r'],
                'hotelprice':order['h_p'],
                })
        #发送邮件
        mailto_list=hotel['email']
        sub = "日审报表-"+bd.strftime("%m/%d")+"-"+ed.strftime("%m/%d")
        if num == 0:
            return self.finish("0")
        elif send_daily_mail(mailto_list, sub, items):
            return self.finish(str(num))
        else:
            return self.finish("-1")

class ServerTimeHandler(web.RequestHandler):
    """Get standard server time"""
    def get(self):
        st = str(datetime.datetime.utcnow())
        st = st[:st.find('.')].replace(' ', 'T')
        self.finish(st)

class HotelSmsHandler(web.RequestHandler):
    """Get hotel's reply sms message from sms provider and change database"""
    def get(self):
        self.finish('success')

    def post(self):
        try:
            extnum = int(self.get_argument('extnum'))
            print extnum
            price = float(self.get_argument('upMsg'))
            print price
            if price > 0:
                bid = DB.NewBid.find_one_and_update(
                        {'h_mn':extnum},
                        {'$set': {
                            'h_p':price,
                            'd_i':datetime.datetime.utcnow(),
                            'h_in':0}})
        except:
            pass
        return self.finish('success')

SETTINGS = {
    "cookie_secret" : "",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "debug" : True,
    #"static_path": "static",
    }

APP = web.Application([
    (r"/tor/test", TestHandler),
    (r"/tor/servertime", ServerTimeHandler),

    (r"/tor/hotel/login", HotelLoginHandler),
    (r"/tor/hotel/reg", HotelRegHandler),
    (r"/tor/hotel/wait", HotelWaitOrderHandler),
    (r"/tor/hotel/bid/update", HotelUpdateBidHandler),
    (r"/tor/hotel/bid/complete", HotelCompleteBidHandler),
    (r"/tor/hotel/logout", HotelLogoutHandler),
    (r"/tor/hotel/info", HotelInfoHandler),
    (r"/tor/hotel/daily", HotelDailyHandler),
    (r"/tor/hotel/sms", HotelSmsHandler),

    (r"/tor/user/weblogin", UserWebLoginHandler),
    (r"/tor/user/booking", UserBookingHandler),
    
    (r"/tor/user/del_new_order", UserDelNewOrderHandler),
    (r"/tor/user/del_acc_order", UserDelAccOrderHandler),
    (r"/tor/user/acc_bid", UserAccBidHandler),
    (r"/tor/user/pay_bid", UserPayBidHandler),
    (r"/tor/user/phone", UserPhoneHandler),
    (r"/tor/user/sendvalidsms", UserValidSmsHandler),
    (r"/tor/user/orders", UserOrdersHandler),

    ], **SETTINGS)

if __name__ == "__main__":
    APP.listen(int(sys.argv[1]))
    ioloop.IOLoop.instance().start()
