#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pymongo import MongoClient, GEOSPHERE, ASCENDING
import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['huhushuidb']

remote_client = MongoClient('')
redb = remote_client['ctrip']

if __name__ == "__main__":

    '''从爬虫导入酒店数据用
    '''
    name = u'成都云泽酒店'
    print redb.hotel.find({'name':name}).count()
    for h in redb.hotel.find({'name':name}):
        if db.Hotel.find_one({'name':h['name']}):
            print h['name'] + '----already exists'
        else:
            print h['name'] + '@@@@need to add'
            del h['_id']
            if h['price']!=u"专享价":
                h['price'] = float(h['price'])
            else:
                h['price'] = 999.99
            h['password'] = ''
            h['loginame'] = ''
            h['loc'] = {'type':'Point', 'coordinates': [float(h['longitude']), float(h['latitude'])]}
            db.Hotel.insert_one(h)


    '''创建了地理位置索引
    for doc in db.hotel.find():
        db.hotel.update_one({'_id':doc['_id']}, {'$set':{'loc':{'type':'Point', 'coordinates': [float(doc['longitude']),float(doc['latitude'])]}}})
        db.hotel.update_one({'_id':doc['_id']}, {'$set':{'password':''}})
        db.hotel.update_one({'_id':doc['_id']}, {'$set':{'loginame':''}})
    db.hotel.create_index([('loc', GEOSPHERE)])
    '''

    '''将所有的价格都转换为数字
    for doc in db.Hotel.find({'price':{'$type':2}}):
        pricef = 999.99
        if doc['price']!=u"专享价":
            pricef = float(doc['price'])
        db.Hotel.update_one({'_id':doc['_id']},{'$set':{'price':pricef}})
    '''
        
    '''根据地理位置、价格等进行查询
    results = db.command(
        'geoNear', 'Hotel',
        near={'type': 'Point','coordinates': [104.098806,30.672721]},
        spherical=True,num=100,maxDistance=2000,
        query={'price':{'$gt':250},'loginame':{'$ne':'w'}})["results"]
    print len(results)
    '''

    '''查找bid并且按照某些条件排序
    bids = db.Bid.find({'bidstatus':'NEW'}).sort('price', ASCENDING).limit(2)
    for bid in bids:
        print bid
    '''


