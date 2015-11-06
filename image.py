import os
import re
import requests
from pyquery import PyQuery as pq
from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class GetMeiziPic(object):
    """docstring for ClassName"""
    def __init__(self):
        super(GetMeiziPic, self).__init__()
        self.max = None
        self.cookies = {}
        self._isUrlFormat = re.compile(r'http://([\w-]+\.)+[\w-]+(/[\w\- ./?%&=]*)?');
        self._path = self.DealDir("Images")
        print("===============   start   ===============");

        last = 'last'
        i = 900
        if os.path.exists(last):
            i = int(open(last, 'r').read(1000))
            print 'last', i
        while True:
            print("===============   loading page {0}   ===============".format(i))
            with open('last', 'w') as f:
                f.write(str(i))
            if not self.DoFetch(i):
                print 'Fail DoFetch'
                break
            i += 1
            if i > self.max:
                break

        print("===============   end   ===============")
    def DealDir(self, path):
            if not os.path.exists(path):
                os.mkdir(path);
            return path;

    def DoFetch(self, pageNum):
        url = "http://jandan.net/ooxx/page-{0}#comments".format(pageNum)
        print "GET", url
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}
        print "GET", url, headers, self.cookies
        response = requests.get(url, headers=headers, cookies=self.cookies)
        if response.status_code == 403:
            print "403, need check"
            #print response.text
            if 'set-cookie' in response.headers:
                sc = response.headers['set-cookie']
                k,v = sc.split('=')
                self.cookies[k] = v
                print 'set-cookie',k,'=',v
            d = pq(response.text)
            payload = dict([(x.name, x.value) for x in d('form input')])
            url = 'http://jandan.net/block.php'+d('form')[0].action
            print response.url
            headers['Referer'] = response.url
            print url,payload,headers,self.cookies
            r = requests.post(url, data=payload, headers=headers, cookies=self.cookies)
            print r.status_code
            print r.headers
            #print r.text

            return False

        if response.status_code != 200:
            print "Fail", response.status_code
            #print response.text
            return False
        # stream = response.GetResponseStream();
        if len(response.text) == 0:
            return False
        if self.max is None:
            self.max = self.get_max(response.text)

        return self.FetchLinksFromSource(response.text)
    

    # @return int
    def get_max(self, html_code):
        d = pq(html_code)
        for a in d('#comments')[0].find_class('comments')[0].find_class('cp-pagenavi')[0].getchildren():
            if unicode(a.text).isnumeric():
                return int(a.text)
        raise Exception("no int")
    def FetchLinksFromSource(self, htmlSource):
        d = pq(htmlSource)
        for img in d('#comments ol li .text img'):
            attrib = img.attrib
            if 'org_src' in attrib:
                print 'fonund a gif'
                href = attrib['org_src']
            elif 'src' in attrib:
                href = attrib['src']
            else:
                print attrib, 'fuck, no src'
                continue

            # only for sina image
            if ".sinaimg." in href and self.CheckIsUrlFormat(href):
                print href
            else:
                continue;

            self.download_file(href)
        return True

    def CheckIsUrlFormat(self, value):
        return self._isUrlFormat.match(value) is not None
    def download_file(self, url):
        local_filename = "Images/"+ url.split('/')[-1]
        if os.path.exists(local_filename):
            print '\t skip',local_filename
            return
        else:
            print '\t=>',local_filename
        try:
            pass
            # NOTE the stream=True parameter
            r = requests.get(url, stream=True)
        except Exception, e:
            print e
            return False
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        return local_filename

if __name__ == '__main__':
    g = GetMeiziPic()
