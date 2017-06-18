# -*- coding: utf-8 -*-
import requests
import datetime
from bs4 import BeautifulSoup
import time
import telepot
import telepot.namedtuple
import Levenshtein
import  sys
from telepot.loop import MessageLoop

token='338854615:AAEVxndSfzDtsvqp9ZU951Go2z8ey4v2WRk'

#with open('test.html', 'w') as output_file:
#   output_file.write(text)
def get_busstop(route, days, waypoint, direction):
    url = 'http://www.mosgortrans.org/pass3/shedule.printable.php?type=avto&way=%s&date=%s&direction=%s&waypoint=%d' % \
    (route, days, direction, waypoint)
    # r = requests.get(url, proxies = proxyDict)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    page = soup.find('div', {'class': 'cutthis'})
    return page.find('p').find('b').text

def get_timetable(route, days, waypoint, direction):
    url = 'http://www.mosgortrans.org/pass3/shedule.printable.php?type=avto&way=%s&date=%s&direction=%s&waypoint=%d' % \
    (route, days, direction, waypoint)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    page = soup.find('div', {'class':'cutthis'})
    stop_title = page.find('p').find('b').text
    print(stop_title)

    ttable= page.find('table',{'class':'bordered'})

    timetable=[]

    ttable_rows = ttable.find_all('tr')

    for ttable_row in ttable_rows:
        td_hours = ttable_row.find_all('td',{'align':'right'})
        td_minutes = ttable_row.find_all('td',{'align':'left'})
        hours=[]

        for td_hour in td_hours:
            hours.append(int(td_hour.find('span',{'class':'hour'}).text))
        i=0
        for td_minute in td_minutes:
            min_spans = td_minute.find_all('span',{'class':'minute'})
            for min_span in min_spans:
                mins = min_span.text
                if mins:
                    ts = datetime.time(hours[i],int(mins))
                    timetable.append(ts)
            i=i+1

    return timetable

def get_stations_list(route):
    url='http://www.mosgortrans.org/pass3/request.ajax.php?list=waypoints&type=avto&way=%s&date=0000011&direction=AB' % \
        (route)
    print(url)
    r = requests.get(url)
    stlist = r.text.splitlines()
    return stlist
#for dt in get_timetable(882,'0000011',0,'BA'):
#    print(dt)

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    m = telepot.namedtuple.Message(**msg)

    if chat_id < 0:
        # group message
        print 'Received a %s from %s, by %s' % (content_type, m.chat, m.from_)
    else:
        # private message
        print 'Received a %s from %s' % (content_type, m.chat)  # m.chat == m.from_

    if content_type == 'text':
        reply = ''
    weekd='1111100'
    if (datetime.datetime.now()+datetime.timedelta(hours=7)).weekday()>4:
        weekd='0000011'
        # Length-checking and substring-extraction may work differently
        # depending on Python versions and platforms. See above.
        comandlist = msg['text'].partition(' ')
        print (comandlist)

        busnumber=comandlist[0]
        try:
            int_busnumber1 = int(busnumber[0])#bus number should start with digit

            if len(comandlist)==1:
                print ('size==1')
                reply = get_busstop(busnumber, weekd, 0, 'AB')
        print(reply)
        j=0
                for dt in get_timetable(busnumber, weekd, 0, 'AB'):
                    if dt > (datetime.datetime.now()+datetime.timedelta(hours=7,minutes=-20)).time():
                        reply = reply + '\n%s' % (dt)
                        j = j + 1
                    if j > 10:
                        break
            else:
                stations = get_stations_list(busnumber)
                for s in stations:
                    print(s)
                matchings=[]
                k=0
                res=0
                for row in stations:
                    mratio = Levenshtein.ratio(row, comandlist[2])
                    #print (row, mratio)
                    matchings.append(mratio)

                    if mratio>0.6:
                        if mratio>matchings[res]:
                            res=k
                    k=k+1
                print (matchings)
                if len(matchings)==0:
                    print ('station not found')
                    reply = 'Остановка не найдена:'
                    for row in stations:
                        print(row)
                        reply = reply + '\n%s' % (row)
                else:
                    print ('%d %s %s %s' % (res, matchings[res], stations[res], stations[len(stations)-1]))
                    reply = 'Остановка: %s Направление: %s' % (stations[res].encode('utf-8'), stations[len(stations)-1].encode('utf-8'))

                    print (reply)
            print(datetime.datetime.now().time())
            print((datetime.datetime.now()+datetime.timedelta(hours=7)).time())
                    j=0
                    for dt in get_timetable(busnumber, weekd, res, 'AB'):
                        if dt>(datetime.datetime.now()+datetime.timedelta(hours=7,minutes=-20)).time():
                            reply = reply + '\n%s' % (dt)
                            j = j + 1
                        if j > 10:
                            break
                    reply = reply + '\nОбратно, в сторону %s' % (stations[0].encode('utf-8'))

                    j = 0
                    for dt in get_timetable(busnumber, weekd, len(stations)-1-res, 'BA'):
                        if dt > (datetime.datetime.now() + datetime.timedelta(hours=7,minutes=-20)).time():
                            reply = reply + '\n%s' % (dt)
                            j = j + 1
                        if j > 10:
                            break

            bot.sendMessage(chat_id, reply)
        except:
            # print sys.exc_info()[0]
            import traceback;     traceback.print_exc()
            reply = 'Введите через пробел номер автобуса и название остановки'
            bot.sendMessage(chat_id, reply)

bot = telepot.Bot(token)
MessageLoop(bot, handle).run_as_thread()
print 'Listening ...'

# Keep the program running.
while 1:
    time.sleep(10)
