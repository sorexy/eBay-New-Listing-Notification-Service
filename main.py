import os
import requests
from bs4 import BeautifulSoup as bs
import smtplib
import ssl
import email.message
import email.utils
import hashlib
import time

URLS = ['https://www.ebay.co.uk/sch/i.html?_from=R40&_sacat=0&LH_BIN=1&_sop=10&_nkw=macbook+pro+2019+15&_ipg=200&rt=nc',
        'https://www.ebay.co.uk/sch/i.html?_from=R40&_sacat=0&LH_BIN=1&_sop=10&_nkw=macbook+pro+2018+15&_ipg=200&rt=nc']
PW = os.getenv('password')
PORT = 465
SENDER_EMAIL, RECEIVER_EMAIL = "sorex.notifications@gmail.com", "richardrother1994@gmail.com"


def stripPrice(s):
    return float(s[8:15])


def sendEmail(macs2019, macs2018):
    msg = email.message.Message()
    msg['Subject'] = "New Macbook Found!"
    msg.add_header('Content-Type', 'text')

    tmpMsg = "Hi Richard, I found new MacBook listing(s), please find them below: \n\n"

    tmpMsg += "=================================== 2019 MacBooks =================================== \n\n"
    for mac in macs2019:
        tmpMsg += "%s \n Price: %s \n\n" % (mac['title'], mac['price'][1:])
    tmpMsg += ("-"*150)
    tmpMsg += "\n\n =================================== 2018 MacBooks =================================== \n\n"
    for mac in macs2018:
        tmpMsg += "%s \n Price: %s \n\n" % (mac['title'], mac['price'][1:])

    msg.set_payload(tmpMsg)

    context = ssl.create_default_context()

    # setting up the tls encryption, login, and send email
    # if error, retry until fine
    sendingSuccess = False
    while sendingSuccess is False:
        with smtplib.SMTP_SSL("smtp.gmail.com", PORT, context=context) as server:
            try:
                server.login("sorex.notifications@gmail.com", PW)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
                print("Email has been sent")
                server.quit()
                sendingSuccess = True
            except:
                print("Error with sending email, trying again in 30 sec")
                time.sleep(30)
                pass


def getUrlRes(URL):
    while requests.get(URL).status_code != 200:
        print("Request FAILED, trying again in 10 secs. . .")
        time.sleep(10)
    else:
        print("Request OK")
        return requests.get(URL).text


def getNewListings(url, prev_seen):
    """
    Returns a list of new mac listings
    """
    soup = bs(url, 'html.parser')
    listings = soup.find_all('li', class_='sresult lvresult clearfix li')

    macs = []
    for item in listings:
        # in title, h3 is the element used for the title, so conveniently, we can just stirp all h3s for titles
        # in price, the ul element is the list which contains prices
        # i am filtering the list of items for the actual price
        title_text = item.h3.get_text().strip().encode('utf-8')
        title_hash = hashlib.md5(title_text).digest()

        price = item.ul.find('li', class_='lvprice prc').get_text().strip().encode('utf-8')[1:]

        tmp = {'title': title_text, 'price': price}

        if title_hash not in prev_seen:
            prev_seen[title_hash] = price
            macs.append(tmp)

    print("found some macs, returning listings")
    return macs


previously_seen_2019, previously_seen_2018 = {}, {}

# Main
while True:
    mac2019pg, mac2018pg = None, None
    # need to refresh URLs each time to make sure updated
    while mac2019pg is None:
        mac2019pg = getUrlRes(URLS[0])
    while mac2018pg is None:
        mac2018pg = getUrlRes(URLS[1])

    new2019macs = getNewListings(mac2019pg, previously_seen_2019)
    new2018macs = getNewListings(mac2018pg, previously_seen_2018)

    if new2019macs or new2018macs:
        print("============================ New Mac listings found! Preparing to send email. . . ============================")
        sendEmail(new2019macs, new2018macs)
    else:
        print("No new listings :(")

    print("Going to sleep for 15 seconds, goodnight!")
    time.sleep(15)
