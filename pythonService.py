# -*- coding: utf-8 -*-
from flask import Flask,send_file, send_from_directory,jsonify
from flask import request
import json,os
import redis
import hashlib
import time
from PIL import Image,ImageDraw,ImageFont
from redisco import models
import redisco
import requests

from flask_sockets import Sockets


redisco.connection_setup(host='qianqiulin.com', port=6379, password='12345678')


app = Flask(__name__)
sockets = Sockets(app)

r = redis.Redis(host='127.0.0.1', port=6379, password='12345678')


def md5(strs):
    hl = hashlib.md5()
    hl.update(strs.encode(encoding='utf-8'))
    return hl.hexdigest()


def getAllAppointMentFromRedis(type,area):
    data = r.hgetall(type)
    ret_data = []

    for n in data.keys():
        data_one=json.loads(data[n])
        if data_one['status']=='offline':
            continue
        else:
            if area=='all' or area==None:
                ret_data.append(data_one)
            else:
                if 'area' in data_one.keys():
                    if data_one['area']==area:
                        ret_data.append(data_one)
    
    ret_data=sorted(ret_data, key=lambda student: student['gmt_create'],reverse=True)
      
    return ret_data

def add(content, redisName):
    content = content.decode('utf-8')
    key = md5(content)
    data=json.loads(content)

    if redisName=='car':
        drawShareImgCar(data,key)
    elif redisName=='passenger':
        drawShareImgPassenger(data,key)

    data['shareImage']='https://lyl.qianqiulin.com/img/'+key+'.jpg'
    data['gmt_create']=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    data['dataId']=key
    data['status']='online'

    r.hset(name=redisName, key=key, value=json.dumps(data,ensure_ascii=False))



@app.route('/img/<path:filename>')
def download_file(filename):
    directory = './img/'
    return send_from_directory(directory, filename, as_attachment=True)


def delFromRedisByIdAndType(types,key):
    try:
        data=json.loads(r.hget(types,key))
        data['status']='offline'
        r.hset(name=types,key=key,value=json.dumps(data,ensure_ascii=False))
        ret_code=True
    except:
        ret_code=False
    return ret_code


@app.route('/delAppointment.json', methods=['POST'])
def delAppointment():
    request_body = request.get_data()
    request_data=json.loads(request_body)
    ret_code=delFromRedisByIdAndType(request_data['type'],request_data['dataId'] )
    
    return json.dumps({"success":ret_code})

@app.route('/addCar.json', methods=['POST'])
def addCar():
    request_body = request.get_data()
    add(request_body, 'car')
    return ''


@app.route('/addPassenger.json', methods=['POST'])
def addPassenger():
    request_body = request.get_data()
    add(request_body, 'passenger')
    return ''


@app.route('/getPassenger.json', methods=['GET'])
def getPassenger():
    area = request.args.get('area')
    ret_data={}
    ret_data['success']='true'
    ret_data['data']=getAllAppointMentFromRedis('passenger',area=area)
    return json.dumps(ret_data, ensure_ascii=False) ,{'Content-Type': 'application/json'}


@app.route('/getCar.json', methods=['GET'])
def getCar():
    area = request.args.get('area')
    orderBy=request.args.get('orderBy')
    ret_data={}
    ret_data['success']='true'
    ret_data['data']=getAllAppointMentFromRedis(type='car',area=area)
    return json.dumps(ret_data, ensure_ascii=False) ,{'Content-Type': 'application/json'}

@app.route('/getNoticebarData.json', methods=['GET'])
def getNoticebarData():
    ret_data={}
    ret_data['success']='true'
    ret_data['data']=getAllAppointMentFromRedis('notice',area='all')[0]
    return json.dumps(ret_data, ensure_ascii=False) ,{'Content-Type': 'application/json'}


def drawText(content,size,x,y,color,canvasObject):
    draw = ImageDraw.Draw(canvasObject)
    fnt = ImageFont.truetype('Hiragino Sans GB.ttc', size)
    draw.text((x,y),content, fill=color,font=fnt)
    return canvasObject


def drawShareImgCar(appoint,key):
    canvas = Image.open("./img/车找人.jpg")
    tel=appoint['tel']
    fromName=cutContent(appoint['from']['name'])
    toName=cutContent(appoint['to']['name'])
    passed=cutContent(appoint['pass'])
    earliestDepartureTime=appoint['earliestDepartureTime']
    latestDepartureTime=appoint['latestDepartureTime']

    if len(earliestDepartureTime)>0 and len(latestDepartureTime)>0:
        times=earliestDepartureTime+'-'+latestDepartureTime
    if len(earliestDepartureTime)==0 or len(latestDepartureTime)==0:
        times=earliestDepartureTime+latestDepartureTime

    canvas=drawText(content=times,size=30,x=400,y=400,color='#000000',canvasObject=canvas)
    canvas=drawText(content=passed,size=40,x=260,y=822,color='#000000',canvasObject=canvas)
    canvas=drawText(content=fromName,size=40,x=260,y=665,color='#000000',canvasObject=canvas)
    canvas=drawText(content=tel,size=30,x=400,y=445,color='#000000',canvasObject=canvas)
    canvas=drawText(content=toName,size=40,x=260,y=975,color='#000000',canvasObject=canvas)

    canvas.save("./img/"+key+'.jpg')
    #canvas.show()

def cutContent(str):
	if len(str)>18:
		str=str[:17]+'...'
	return str
    
def drawShareImgPassenger(appoint,key):
    canvas = Image.open("./img/人找车.jpg")
    tel=appoint['tel']
    fromName=cutContent(appoint['from']['name'])
    toName=cutContent(appoint['to']['name'])
    earliestDepartureTime=appoint['earliestDepartureTime']
    latestDepartureTime=appoint['latestDepartureTime']

    if len(earliestDepartureTime)>0 and len(latestDepartureTime)>0:
        times=earliestDepartureTime+'-'+latestDepartureTime
    if len(earliestDepartureTime)==0 or len(latestDepartureTime)==0:
        times=earliestDepartureTime+latestDepartureTime

    canvas=drawText(content=times,size=30,x=400,y=400,color='#000000',canvasObject=canvas)
    canvas=drawText(content=toName,size=40,x=260,y=822,color='#000000',canvasObject=canvas)
    canvas=drawText(content=fromName,size=40,x=260,y=665,color='#000000',canvasObject=canvas)
    canvas=drawText(content=tel,size=30,x=400,y=445,color='#000000',canvasObject=canvas)

    canvas.save("./img/"+key+'.jpg')
    #canvas.show()

@app.route('/api/login.json', methods=['POST'])
def login():
    request_body = request.get_data()
    request_data = json.loads(request_body)

    token = request_data['token']

    userNow = UserModel.objects.filter(openid=token)

    if not userNow:
        JSCODE = request_data['code']
        APPID = 'wx17bb70bf8838e26a'
        SECRET = 'f0535a7ebe9e43e0b9584d613d59e814'
        url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % (
            APPID, SECRET, JSCODE)

        jscode2session = json.loads(requests.post(url).content)
        openid = jscode2session['openid']

        user = UserModel(openid=openid)
        user.save()

        return jsonify({'success': True, 'ret_code': '', 'data': {'token': openid, 'userInfo': user.attributes_dict}})
    else:
        return jsonify(
            {'success': True, 'ret_code': '', 'data': {'token': token, 'userInfo': userNow[0].attributes_dict}})


@app.route('/api/userInfo.json', methods=['POST'])
def updateUserInfo():
    request_body = request.get_data()
    request_data = json.loads(request_body)

    token = request_data['token']
    tel = request_data['tel']

    userNow = UserModel.objects.filter(openid=token)[0]

    userNow.tel = tel
    userNow.save()

    return jsonify({'success': True, 'ret_code': '', 'data': {'token': token, 'userInfo': userNow.attributes_dict}})


class UserModel(models.Model):
    userName = models.Attribute()
    gmtCreate = models.DateTimeField(auto_now_add=True)
    passWord = models.Attribute()
    openid = models.Attribute()
    tel=models.Attribute()

@sockets.route('/echo')
def echo_socket(ws):
    while not ws.closed:

        now = '我在这里'
        ws.send(now)  #发送数据
        time.sleep(1)

if __name__ == '__main__':
#     app.run(host='0.0.0.0',ssl_context='adhoc')
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler


    server = pywsgi.WSGIServer(('', 8888), app, handler_class=WebSocketHandler)
    server.serve_forever()
