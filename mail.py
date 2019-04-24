#/usr/bin/env python
# -*- coding: utf-8 -*-
import smtplib
from string import Template
from email.mime.text import MIMEText
mail_host=""  #设置服务器
mail_user=""    #用户名
mail_pass=""   #口令
mail_postfix=""  #发件箱的后缀
booking_c = """
<html>
<head>
<meta http-equiv=Content-Type content="text/html; charset=utf8">
<div>
<p align=right><span>订单号：$oid</span></p>
<hr class=msocomoff align=left size=1 width="100%">
</div>
<title>订房确认单</title>
</head>
<body lang=ZH-CN style='font-family:"微软雅黑","sans-serif"'>
<div>
<p style='text-indent:132.0pt;font-size:22.0pt'><span>订房确认单</span></p>
<p><span>致：$hotel</span></p>
<p><span>请确认以下订房信息，予以客人入住办理协助。</span></p>
<table border=1 cellspacing=0 cellpadding=0 width=720>
<tr align=center>
<td width=168 colspan=3>
<p><b><span>酒店</span></b></p>
</td>
<td width=120 colspan=2>
<p><b><span>到店时间</span></b></p>
</td>
<td width=135 colspan=2>
<p><b><span>离店时间</span></b></p>
</td>
<td width=99 colspan=2>
<p><b><span>房型</span></b></p>
</td>
<td width=82>
<p><b><span>数量</span></b></p>
</td>
<td width=116>
<p><b><span>价格</span></b></p>
</td>
</tr>
<tr align=center>
<td width=168 colspan=3 rowspan=2>$hotel</td>
<td width=64><p><span>日期</span></p></td>
<td width=56><p><span>时间</span></p></td>
<td width=135 colspan=2 rowspan=2>$leave</td>
<td width=99 colspan=2 rowspan=2>$roomtype</td>
<td width=82 rowspan=2>1</td>
<td width=116 rowspan=2>$price</td>
</tr>
<tr align=center>
<td width=64><span>$date</span></td>
<td width=56><p><span>$time</span></p></td>
</tr>
<tr align=center>
<td width=84 valign=top><p><b><span>备注</span></b></p></td>
<td width=636 colspan=10>
<p><span>&nbsp;</span></p>
<p><span>&nbsp;</span></p>
<p><span>&nbsp;</span></p>
</td>
</tr>
<tr align=center>
<td width=720 colspan=11>
<p><b><span style='font-size:15.0pt;'>入住方信息</span></b></p>
</td>
</tr>
<tr align=center>
<td width=89 colspan=2><p><b><span>姓名</span></b></p></td>
<td width=334 colspan=5><p><span>$cname</span></p></td>
<td width=81><p><b><span>电话</span></b></p></td>
<td width=216 colspan=3>
<p style='line-height:20.0pt'><span>$cphone</span></p>
</td>
</tr>
<tr align=center>
<td width=89 colspan=2>
<p><b><span>网站付费</span></b></p>
</td>
<td width=334 colspan=4>
<p><span>是</span></p>
</td>
<td width=81 colspan=2>
<p><b><span>发票抬头</span></b></p>
</td>
<td width=216 colspan=3>
<p><span>&nbsp;</span></p>
</td>
</tr>
</table>
<p><span>须知：</span></p>
<p><span>1、客人已通过呼呼睡平台预付房费，该笔预付房费根据订房协议将在$tdate日之间转账账户（）</span></p>
<p><span>
2、客人其他客房消费不涵盖在此笔预付房费中。</span></p>
<p><span>3、客人离店时间默认为离店日期12点以前，如客人提出延住，请根据酒店实际运营状况为客人提供方便。</span></p>
<p><span>4、请保留此预订确认邮件以便双方核对，若此订单无法确认，请在$rtime时前书面回复该邮件至：iask@huhushui.club邮箱。</span></p>
<p><span>
5、根据订房协议须免费为客人提供客房升级服务或在客人同意的前提下安排在区域内同等条件的酒店，由此产生的费用由酒店承担，并因此将产生$compen元中介补偿。</span></p>
</div>
<div>
<hr class=msocomoff align=left size=1 width="33%">
</div>
</body>
</html>
"""

daily_begin = """
<html>
<head>
<meta http-equiv=Content-Type content="text/html; charset=utf8">
</head>
<body lang=ZH-CN style='font-family:"微软雅黑","sans-serif"'>
<div>
<p align=center><span style='font-size:26.0pt;'>日审单</span></p>
<table border=1 cellspacing=0 cellpadding=0 width=699>
<tr>
<td width=47 align=center><p><b><span>序号</span></b></p></td>
<td width=66 align=center><p><b><span>订单号</span></b></p></td>
<td width=76 align=center><p><b><span>客人姓名</span></b></p></td>
<td width=76 align=center><p><b><span>入住房型</span></b></p></td>
<td width=47 align=center><p><b><span>房费</span></b></p></td>
<td width=76 align=center><p><b><span>中介补偿</span></b></p></td>
<td width=47 align=center><p><b><span>其他</span></b></p></td>
<td width=142 align=center><p><b><span>呼呼睡在线确认</span></b></p></td>
<td width=122 align=center><p><b><span>酒店确认</span></b></p></td>
</tr>
"""
daily_c = """
<tr>
<td width=47 align=center><p><span>$num</span></p></td>
<td width=66 align=center><p><span>$oid</span></p></td>
<td width=76 align=center><p><span>$cname</span></p></td>
<td width=76 align=center><p><span>$roomtype</span></p></td>
<td width=47 align=center><p><span>$hotelprice</span></p></td>
<td width=76 align=center><p><span>0</span></p></td>
<td width=47 align=center><p><span>&nbsp;</span></p></td>
<td width=142 align=center><p><span>&nbsp;</span></p></td>
<td width=122 align=center><p><span>&nbsp;</span></p></td>
</tr>
"""
daily_end = """
</table>
</div>
</body>
</html>
"""

def send_mail(to_list, sub, rc):
    me="呼呼睡预订"+"<"+mail_user+">"
    msg = MIMEText(rc, _subtype='html', _charset='utf8')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        server = smtplib.SMTP()
        server.connect(mail_host)
        server.login(mail_user,mail_pass)
        server.sendmail(me, to_list, msg.as_string())
        server.close()
        return True
    except Exception, e:
        print str(e)
        return False

def send_booking_mail(to_list, sub, data):
    t = Template(booking_c)
    rc = t.substitute(data)
    return send_mail(to_list, sub, rc)

def send_daily_mail(to_list, sub, items):
    rc = daily_begin
    for item in items:
        t = Template(daily_c)
        rc += t.substitute(item)
    rc += daily_end
    return send_mail(to_list, sub, rc)

if __name__ == '__main__':
    mailto_list=[""]
    sub = "测试122324314"
    data = {
            "oid":"0000000000000",
            "hotel":"花样",
            "date":"1",#art.strftime('%x'),
            "time":"2",#art.strftime('%X'),
            "roomtype":"大床房",
            "price":"100",
            "cname":"qy",
            "cphone":"135555",
            "leave":"正常离店时间",
            "tdate":"日期",
            "rtime":"时间",
            "compen":"100",
            }
    items = [{
        "num":"1",
        "oid":"23",
        "cname":"qqq",
        "roomtype":"123", 
        "hotelprice":"556",
        },{
        "num":"2",
        "oid":"2243",
        "cname":"q42qq",
        "roomtype":"24123", 
        "hotelprice":"245556",
            }]
    #if send_booking_mail(mailto_list, sub, data):
    if send_daily_mail(mailto_list, sub, items):
        print "发送成功"
    else:
        print "发送失败"
