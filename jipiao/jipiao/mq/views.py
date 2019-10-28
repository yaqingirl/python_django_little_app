# coding: utf-8
import socket

from django.shortcuts import render_to_response,HttpResponseRedirect, render
from django.http import  HttpResponse
#from jipiao.mq.models import AirAirplaneOrder
# import MySQLdb
import pymysql
import requests
import random
import string
import time
import re
import json

s = requests.Session()
def queryDB(orderCode):
    conn = pymysql.connect(
        host='***.***.***.***', #主机名
        port=3306,        #端口号(默认的)
        user='i******',  #用户名
        passwd='*********',   #密码
        db='***',  #数据库名
        charset='utf8', #这里设置编码是为了输出中文
    )
    cursor = conn.cursor()
    sql = 'select order_code,user_id,order_money,cost_money from air_airplane_order where order_code=%s' % orderCode
    cursor.execute(sql)
    resultdb  = cursor.fetchmany(1)
    print("resultdb:")
    print(resultdb[0][2])
    cursor.close()
    conn.close()
    return resultdb[0]

def search(request):
    if request.session['is_login']:
        error = []
        if 'q' in request.GET:
            q = request.GET['q']
            if not q:
                error.append("Please enter a order_code.")
            elif len(q) > 11 or len(q) < 11:
                error.append("Please enter right order_code")
            else:
                orders = queryDB(q)
                sendMQ(orders)
                print("orders:")
                print(orders)
                return render_to_response('search_results.html', {'orders': orders, 'query': q})
        return render_to_response('search_form.html', {'error': error})
    else:
        return HttpResponse('http://' + get_host_ip() + ':8088/index')

def refund(request):

    if request.session['is_login']:
        error = []
        if 'order_code' in request.GET:
            order_code = request.GET['order_code']
            if not order_code:
                error.append("Please enter a order_code.")
            elif len(order_code) > 11 or len(order_code) < 11:
                error.append("Please enter right order_code")
            else:
                #print(queryUUID(order_code))
                # return render_to_response('refund_list.html',{'refundMessages':json.dumps(queryUUID(order_code))})
                return render_to_response('refund_list.html', {'refundMessages': queryUUID(order_code)})
        if 'refundIds' in request.GET:
            if not request.GET['refundIds']:
                error.append("Please enter refundId.")
            else:
                refundIds = request.GET['refundIds'].split(",")
                orderId = request.GET['orderId']
                for refundId in refundIds:
                    rfundEntry = {}
                    for refundMessage in queryUUID(orderId):
                        if refundMessage.get('refundId') == refundId:
                            rfundEntry = refundMessage
                    sendMQ_refund(orderId, rfundEntry.get('refundPrice'), rfundEntry.get('uuid'),
                                  rfundEntry.get('refundId'))
                return render_to_response('refund_results.html', {'orders': orderId, 'refundIds': refundIds})
                print(request.GET['orderId'])
                print(refundIds + '***************')
        return render_to_response('refund_form.html', {'error': error})
    else:
        return HttpResponse('http://'+get_host_ip()+':8088/index')


def login():
    url = 'http://***.***.***.***/jmq-web/j_spring_security_check'
    header = {
        'Host': '***.***.***.***',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Origin': 'http://***.***.***.***',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'http://***.***.***.***/jmq-web/login.html'
    }
    data = {
        'j_username': '***',
        'j_password': '***'
    }
    r = s.request('post', url, headers=header, data=data)
    print(r.status_code, '\n')
    print(r.request._cookies, '\n')
    return r.request._cookies

def login_gw():
    url = 'http://***.***.***.***/sso/login?ReturnUrl=http://***.***.***.***'
    header = {
        'Host': 't***.***.***.***',
        'Connection': 'keep-alive',
        'Content - Length': '129',
        'Cache-Control': 'max-age=0',
        'Origin': 'http://***.***.***.***',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'http://***.***.***.***/sso/login?ReturnUrl=http://***.***.***.***/'
    }
    data = {
        'fp': 'FLHQPKIPZV2RVCQG66V4EYHD4RWGFY3OUIPV5IK2ZH25NG6P63O35C4NASGOMLIJEA4ZWCSXIF32WS4PU27O3JY25A',
        'username': '***',
        'password': '****'
    }
    try:
        r = s.request('post', url, headers=header, data=data)
    except Exception as e:
        print(e)
    print(r.status_code, '\n')
    print(r.request._cookies, '\n')
    return r.request._cookies

def queryUUID(orderId):
    loginCookie=login_gw()
    search_url = 'http://***.***.***.***/refund/refundList?orderId=++'+orderId+'&businessType=-1&pin=&refundStatus=-1&isHis=false'
    search_header = {
        'Host': 'gw.man.jd.com',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'http://***.***.***.***/refund/refundList',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    search_Response = s.request('get', search_url, headers=search_header, cookies=loginCookie)
    text=search_Response.text
    r=r'<td>\d{7}</td>'
    pattern = re.compile(r)
    #result=pattern.search(text)
    result=pattern.findall(text)
    refundMessages = []
    for refundId_str in result:
        refundId = re.search(r'\d{7}',refundId_str).group(0)
        refundDetail_url = 'http://***.***.***.***/refund/refundDetailList?refundId=' + refundId + '&refundStatus=0'
        refundDetail_header = {
            'Host': '***.***.***.***',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://***.***.***.***/refund/refundList?orderId='+orderId+'&businessType=-1&pin=&refundStatus=-1&isHis=false',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        refundDetail_Response = s.request('get', refundDetail_url, headers=refundDetail_header, cookies=loginCookie)
        UUID = re.search(r'jp_[0-9a-zA-Z\-]+', refundDetail_Response.text).group(0)
        refundPrice = re.search(r'\d*\.\d{2}',re.search(r'<td>￥\d*\.\d{2}</td>', refundDetail_Response.text).group(0)).group(0)
        refundMessages.append({'orderId':orderId,'uuid': UUID, 'refundPrice': refundPrice, 'refundId': refundId})
    return refundMessages




def sendMQ(orderMessage):
    logginCookie = login()
    sendMqUrl = 'http://***.***.***.***/jmq-web/subscribe/addConsumerRetry.do'
    sendMqheader = {
        'Host': '***.***.***.***',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Cache-Control': 'max-age=0',
        'Origin': 'http://***.***.***.***',
        'X-Requested-With': 'XMLHttpRequest',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'http://***.***.***.***/jmq-web/consumerMonitor.do'
    }
    #orderConfirmId='2212101001131793275a656756'
    orderConfirmId=''.join(random.sample(string.ascii_letters + string.digits, 30))
    orderConfirmTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    sendMqdata = {
        'topicId': '',
        'app': 'popjipiao',
        'topic':'PS_DZvirtual_Success',
        'businessId':'35',
        'message':'{ "orderId":"%s", "parentOrderId":"0", "payId":"", "orderConfirmPrice":%s, "confirmType":"createPay", "confirmResultType":"full", "pin":"%s", "orderConfirmTime":"%s", "orderConfirmId":"%s", "orderType":35, "ver":0, "realDuePrice":%s, "realPayPrice":%s, "paidIn":%s, "auditStatus":0, "dbIndex":"4", "lastOrderBankStatus":1, "refundType":0, "payMode":4, "psMode":0, "price":%s, "id":%s, "shouldMorePayRefund":0.0000 }'%(orderMessage[0],orderMessage[2],orderMessage[1],orderConfirmTime,orderConfirmId,orderMessage[2],orderMessage[2],orderMessage[3],orderMessage[3],orderMessage[0])
    }
    mqResponse=s.request('post',sendMqUrl,headers=sendMqheader,data=sendMqdata,cookies=logginCookie)
    print(orderConfirmId)
    print(orderConfirmTime)
    print(sendMqdata.get('message'))
    print(mqResponse.json(),'\n')

    def queryUUID(orderId):
        loginCookie = login_gw()
        search_url = 'http://***.***.***.***/refund/refundList?orderId=++' + orderId + '&businessType=-1&pin=&refundStatus=-1&isHis=false'
        search_header = {
            'Host': 'gw.man.jd.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://***.***.***.***/refund/refundList',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        search_Response = s.request('get', search_url, headers=search_header, cookies=loginCookie)
        text = search_Response.text
        r = r'<td>\d{7}</td>'
        pattern = re.compile(r)
        refundId = re.search(r'\d{7}', pattern.search(text).group(0)).group(0)
        print(refundId)

        refundDetail_url = 'http://***.***.***.***/refund/refundDetailList?refundId=' + refundId + '&refundStatus=0'
        refundDetail_header = {
            'Host': '***.***.***.***',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://***.***.***.***/refund/refundList?orderId=++56288525121&businessType=-1&pin=&refundStatus=-1&isHis=false',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        refundDetail_Response = s.request('get', refundDetail_url, headers=refundDetail_header, cookies=loginCookie)
        UUID = re.search(r'jp_\d{6}', refundDetail_Response.text).group(0)
        return UUID

def sendMQ_refund(orderId,refundMoney,uuid,refundId):
    logginCookie = login()
    sendMqUrl = 'http://1***.***.***.***/jmq-web/subscribe/addConsumerRetry.do'
    sendMqheader = {
        'Host': '***.***.***.***',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Cache-Control': 'max-age=0',
        'Origin': 'http://***.***.***.***',
        'X-Requested-With': 'XMLHttpRequest',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'http://***.***.***.***/jmq-web/consumerMonitor.do'
    }
    jdRefundId=refundId
    refundTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    transactionNumber=uuid
    sendMqdata = {
        'topicId': '',
        'app': 'airplane',
        'topic':'refundCallback',
        'businessId':orderId,
        'message':'{"bussinessType":"35","field1":"35","field2":"","jdRefundId": %s,"memo":"","orderId":%s,"refundMoney": %s,"refundTime":"%s","status":"0","transactionNumber":"%s"}' % (jdRefundId,orderId,refundMoney,refundTime,transactionNumber)
    }
    mqResponse=s.request('post',sendMqUrl,headers=sendMqheader,data=sendMqdata,cookies=logginCookie)
    print(mqResponse.content)
    print(sendMqdata)

def index(request):
    url = 'http://***.***.***.***.88:8080/sso?appid=6a325be8-8e11-3b67-a8e5-d9f113b23847&erpusername=****&param={"returnurl":"http://'+get_host_ip()+':8088/allInOne"}'
    r = requests.get(url)
    ajson = json.loads(r.text)
    print(ajson)
    print(ajson['result'])
    response = HttpResponseRedirect(ajson['result'])
    return response


def allInOne(request):
    rr = request.GET['sso_service_ticket']
    if rr == request.GET['sso_service_ticket']:
        request.session['is_login'] = True
        print(request.session['is_login'])
    else:
        return HttpResponse('http://'+get_host_ip()+':8088/index')

    if request.session['is_login']:
        return render(request, 'allInOne.html')
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip