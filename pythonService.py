# -*- coding: utf-8 -*-
from flask import Flask,send_file, send_from_directory
from flask import request
import json,os
import redis
import hashlib
import time
from PIL import Image,ImageDraw,ImageFont

app = Flask(__name__)

r = redis.Redis(host='127.0.0.1', port=6379, password='12345678')


def md5(strs):
    hl = hashlib.md5()
    hl.update(strs.encode(encoding='utf-8'))
    return hl.hexdigest()


def getAllAppointMentFromRedis(type):
    data = r.hgetall(type)
    ret_data = []
    
    for n in data.keys():
        data_one=json.loads(data[n])
        try:
            if data_one['status']=='offline':
                continue
            else:
                ret_data.append(data_one)
        except:
            ret_data.append(data_one)
    # ret_data = [json.loads(data[n]) for n in data.keys()]
    try:
        ret_data=sorted(ret_data, key=lambda student: student['gmt_create'],reverse=True)
    except:
        pass    
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
    ret_data={}
    ret_data['success']='true'
    ret_data['data']=getAllAppointMentFromRedis('passenger')
    return json.dumps(ret_data, ensure_ascii=False) ,{'Content-Type': 'application/json'}


@app.route('/getCar.json', methods=['GET'])
def getCar():
    ret_data={}
    ret_data['success']='true'
    ret_data['data']=getAllAppointMentFromRedis('car')
    return json.dumps(ret_data, ensure_ascii=False) ,{'Content-Type': 'application/json'}

@app.route('/getNoticebarData.json', methods=['GET'])
def getNoticebarData():
    ret_data={}
    ret_data['success']='true'
    ret_data['data']=getAllAppointMentFromRedis('notice')[0]
    return json.dumps(ret_data, ensure_ascii=False) ,{'Content-Type': 'application/json'}


def drawText(content,size,x,y,color,canvasObject):
    draw = ImageDraw.Draw(canvasObject)
    fnt = ImageFont.truetype('Hiragino Sans GB.ttc', size)
    draw.text((x,y),unicode(content,'utf-8'), fill=color,font=fnt)
    return canvasObject


def drawShareImgCar(appoint,key):
    canvas = Image.open("./img/车找人.jpg")
    tel=appoint['tel']
    fromName=appoint['from']['name']
    toName=appoint['to']['name']
    passed=appoint['pass']
    earliestDepartureTime=appoint['earliestDepartureTime']
    latestDepartureTime=appoint['latestDepartureTime']

    if len(earliestDepartureTime)>0 and len(latestDepartureTime)>0:
        times=earliestDepartureTime+'-'+latestDepartureTime
    if len(earliestDepartureTime)==0 or len(latestDepartureTime)==0:
        times=earliestDepartureTime+latestDepartureTime

    canvas=drawText(content=times,size=30,x=400,y=400,color='#000000',canvasObject=canvas)
    canvas=drawText(content=passed,size=40,x=320,y=820,color='#000000',canvasObject=canvas)
    canvas=drawText(content=fromName,size=40,x=320,y=660,color='#000000',canvasObject=canvas)
    canvas=drawText(content=tel,size=30,x=400,y=445,color='#000000',canvasObject=canvas)
    canvas=drawText(content=toName,size=40,x=320,y=975,color='#000000',canvasObject=canvas)

    canvas.save("./img/"+key+'.jpg')
    canvas.show()


def drawShareImgPassenger(appoint,key):
    canvas = Image.open("./img/车找人.jpg")
    tel=appoint['tel']
    fromName=appoint['from']['name']
    toName=appoint['to']['name']
    earliestDepartureTime=appoint['earliestDepartureTime']
    latestDepartureTime=appoint['latestDepartureTime']

    if len(earliestDepartureTime)>0 and len(latestDepartureTime)>0:
        times=earliestDepartureTime+'-'+latestDepartureTime
    if len(earliestDepartureTime)==0 or len(latestDepartureTime)==0:
        times=earliestDepartureTime+latestDepartureTime

    canvas=drawText(content=times,size=30,x=400,y=400,color='#000000',canvasObject=canvas)
    canvas=drawText(content=toName,size=40,x=320,y=820,color='#000000',canvasObject=canvas)
    canvas=drawText(content=fromName,size=40,x=320,y=660,color='#000000',canvasObject=canvas)
    canvas=drawText(content=tel,size=30,x=400,y=445,color='#000000',canvasObject=canvas)

    canvas.save("./img/"+key+'.jpg')
    canvas.show()




if __name__ == '__main__':
    app.run(host='0.0.0.0',ssl_context='adhoc')
