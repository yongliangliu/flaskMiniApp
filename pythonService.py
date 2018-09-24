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
from flask_socketio import SocketIO, rooms, join_room, leave_room


redisco.connection_setup(host='qianqiulin.com', port=6379, password='12345678')


app = Flask(__name__)
socketio = SocketIO(app)

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
    userNow = UserModel.objects.get_by_id(UserModel.objects.filter(openid=token)[0].id)


    province = request_data['userInfo']['province']
    city = request_data['userInfo']['city']
    language = request_data['userInfo']['language']
    avatarUrl = request_data['userInfo']['avatarUrl']
    gender = request_data['userInfo']['gender']
    country = request_data['userInfo']['country']
    nickName=request_data['userInfo']['nickName']
    try:
        tel=request_data['tel']
    except:
        tel=''
    
   
    userNow.province=province
    userNow.province = province
    userNow.city = city
    userNow.language = language
    userNow.avatarUrl = avatarUrl
    userNow.gender = str(gender)
    userNow.country = country
    userNow.nickName = nickName
    userNow.tel = tel

    userNow.save()    
    return jsonify({'success': True, 'ret_code': '', 'data': {'token': token, 'userInfo': userNow.attributes_dict}})


class UserModel(models.Model):

    gmtCreate = models.Attribute()
    openid = models.Attribute()
    nickName= models.Attribute()
    avatarUrl= models.Attribute()
    province= models.Attribute()
    city= models.Attribute()
    gender= models.Attribute()
    country= models.Attribute()
    language= models.Attribute()

    tel=models.Attribute()


class RoomModel(models.Model):
    roomId=models.Attribute()
    gmtCreate = models.DateTimeField(auto_now_add=True)
    users = models.ListField(str)




@socketio.on('joined')
def chat_joined(message):
    room_id = message['roomId']
    open_id =  message['openid']
    userInfo = UserModel.objects.filter(openid=open_id)[0]

    roomNow = RoomModel.objects.filter(roomId=room_id)

    if roomNow:
        room=RoomModel.objects.filter(roomId=room_id)[0]
        if userInfo.openid not in room.users:
            room.users.append(userInfo.openid)
            room.save()
        room_members_cnt=len(room.users)+1
        app.logger.debug(room)
        
    else:
        room=RoomModel(roomId=room_id)
        room_members_cnt=1
        room.users.append(userInfo.openid)
        room.save()
        # app.logger.debug('fffff'+room.attributes_dict)

    ret_data={}
    ret_data['userInfo']=userInfo.attributes_dict
    ret_data['message']=u'{nickName}已加入，当前在线{room_members_cnt}人'.format(nickName=userInfo.nickName,room_members_cnt=room_members_cnt)

    app.logger.debug(ret_data)

    join_room(room_id)
    socketio.emit('status', ret_data,room=room_id)


@socketio.on('left')
def chat_left(message):


    room_id = message['roomId']
    open_id =  message['openid']
    userInfo = UserModel.objects.filter(openid=open_id)[0]

    roomNow = RoomModel.objects.filter(roomId=room_id)

    if roomNow:
        room=RoomModel.objects.filter(roomId=room_id)[0]
        if userInfo.openid not in room.users:
            room.users=list(set(room.users))-list(set([userInfo.openid]))
            room.save()
        room_members_cnt=len(room.users)+1
        app.logger.debug(room)
        
    else:
        room=RoomModel(roomId=room_id)
        room_members_cnt=1
        room.users.append(userInfo.openid)
        room.save()

    ret_data={}
    ret_data['userInfo']=userInfo.attributes_dict
    ret_data['message']=u'{nickName}已离开，当前在线{room_members_cnt}人'.format(nickName=userInfo.nickName,room_members_cnt=room_members_cnt)


    leave_room(room)
    socketio.emit('status', ret_data,room=room_id)




@socketio.on('text')
def chat_text(message):

    room_id = message['roomId']
    open_id =  message['openid']
    userInfo = UserModel.objects.filter(openid=open_id)[0]

    roomNow = RoomModel.objects.filter(roomId=room_id)

    if roomNow:
        room=RoomModel.objects.filter(roomId=room_id)[0]
        if userInfo.openid not in room.users:
            room.users.append(userInfo.openid)
            room.save()
        room_members_cnt=len(room.users)+1
        
    else:
        room=RoomModel(roomId=room_id)
        room_members_cnt=1
        room.users.append(userInfo.openid)
        room.save()

    ret_data={}
    ret_data['userInfo']=userInfo.attributes_dict
    ret_data['message']=message['message']
    ret_data['gmtCreate']=message['gmtCreate']
    ret_data['id']=message['id']
    ret_data['type']=message['type']
    ret_data['roomId']=message['roomId']


    socketio.emit('text', ret_data,room=room_id)


class commentModel(models.Model):
    comentType=models.Attribute()
    author = models.Attribute()
    message = models.Attribute()
    gmtCreate = models.DateTimeField(auto_now_add=True)



class ContentModel(models.Model):
    contentId=models.Attribute()
    gmtCreate = models.DateTimeField(auto_now_add=True)
    author = UserModel
    comentList=models.ListField(commentModel)
    section=models.Attribute()
    content = models.Attribute()
    title=models.Attribute()
    imgList=models.ListField(str)





@app.route('/api/addContent.json', methods=['POST'])
def addContent():
    request_body = request.get_data()
    request_data = json.loads(request_body)

    token = request_data['token']
    section = request_data['section']
    content = request_data['content']
    imgList = request_data['imgList']
    title = request_data['title']
    contentId = request_data['contentId']
    userNow = UserModel.objects.filter(openid=token)[0]


    Content=ContentModel(contentId=contentId)
    Content.title=title
    Content.section=section
    Content.content=content
    Content.imgList.extend(imgList)
    Content.author=userNow
    Content.save()
    return jsonify({'success': True, 'ret_code': '', 'data': {'token': token, 'content': Content.attributes_dict}})




@app.route('/api/getContent.json', methods=['GET'])
def getContent():
    section = request.args.get('section').encode('utf-8')
    ContentList = ContentModel.objects.filter(section=section)
    ret_data=[]
    app.logger.debug(ContentList)
    for n in ContentList:
        dataOne=n.attributes_dict
        dataOne['commentCnt']=len(n.comentList)
        ret_data.append(dataOne)
    return jsonify({'success': True, 'ret_code': '', 'data': { 'content': ret_data}})






@app.route('/api/getContentDetail.json', methods=['POST'])
def getContentDetail():
    request_body = request.get_data()
    request_data = json.loads(request_body)

    contentId = request_data['contentId']
    Content =  ContentModel.objects.filter(contentId=contentId)[0]

    return jsonify({'success': True, 'ret_code': '', 'data': {'content': Content.attributes_dict}})


    

	
	
if __name__ == '__main__':
#     app.run(host='0.0.0.0',ssl_context='adhoc')
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler


    server = pywsgi.WSGIServer(('', 8888), app, handler_class=WebSocketHandler)
    server.serve_forever()

#     socketio.run(app, host='0.0.0.0', port=8888, debug=True)
