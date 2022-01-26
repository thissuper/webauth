# -*- coding: utf-8 -*-
# @Time    : 2021/8/22 22:50
# @Author  : thissuper
# @File    : webauth.py
# @Software: PyCharm
import requests
import sys
import getopt
import urllib3
import logging
import base64
from urllib.parse import urlparse, parse_qs

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

logger = logging.getLogger('run log')
logger.setLevel(logging.INFO)

sh = logging.StreamHandler()
fh = logging.FileHandler(filename='run.log')

logger.addHandler(sh)
logger.addHandler(fh)

fmt = logging.Formatter(fmt="%(asctime)s %(filename)s %(funcName)s：line %(lineno)d %(levelname)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

fh.setFormatter(fmt)
sh.setFormatter(fmt)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def redirect(userName, password):
    try:
        r = requests.get("http://192.168.168.1:80/", verify=False,
                         allow_redirects=False, headers=header)
        logger.debug('status code:{0}'.format(r.status_code))
        if r.status_code == 303:
            redirect_url = r.headers['Location']
            logger.debug('redirect_url:{0}'.format(redirect_url))
            r = requests.get(redirect_url, verify=False,
                             allow_redirects=False, headers=header)
            logger.debug('web html:\n{0}'.format(r.text))
            pr = urlparse(redirect_url)
            qs = parse_qs(pr.query)
            result = False
            if 'jquery.min.js' in r.text:
                url = '{0}://{1}'.format(pr.scheme, pr.netloc)
                token = qs['token'][0]
                # oldurl = qs['old-url'][0]
                result = login_v2(url, userName, password, token)
            else:
                url = '{0}://{1}{2}'.format(pr.scheme, pr.netloc, pr.path)
                authServ = qs['authServ'][0]
                oldURL = qs['oldURL'][0]
                result = login_v1(url, userName, password, authServ, oldURL)
            if result:
                check()
            else:
                logger.error('认证失败')
        else:
            check()
    except requests.exceptions.ConnectionError:
        logger.error('连接被重置，未能触发 Web 认证')
    except Exception as err:
        logger.error(err)


def login_v1(url, userName, password, authServ, oldURL):
    payload = {'txtUserName': userName, 'txtPasswd': password, 'oldURL': oldURL, 'authServ': authServ,
               'authFailed': '0', 'userName': '', 'allowpwdChange': '0', 'forcepwdChange': '0'}
    r = requests.post(url, verify=False, data=payload, headers=header)
    if r.status_code != 200:
        logger.error(r.status_code)
        logger.error(r.text)
        return False
    if '错误' in r.text:
        logger.error(r.status_code)
        logger.error(r.text)
        return False
    return True


def login_v2(baseurl, userName, password, token):
    token_obj = token_v2(baseurl, token)
    payload = {'user-name': userName, 'password': str(base64.b64encode(password.encode('utf-8')), 'utf-8'),
               'user-type': 'user', 'chbx_mode': 'password',
               'client-id': token_obj['properties']['client-id']}
    url = '{0}/v1/users?token={1}'.format(baseurl, token)
    r = requests.post(url, verify=False, data=payload, headers=header)

    if r.status_code != 200:
        logger.error(r.status_code)
        logger.error(r.text)
        return False
    if '错误' in r.text:
        logger.error(r.status_code)
        logger.error(r.text)
        return False
    return True


def token_v2(baseurl, token):
    url = '{0}/v1/?token={1}'.format(baseurl, token)
    r = requests.get(url, verify=False, headers=header)
    return r.json()


def check():
    r = requests.get('https://www.taobao.com:443/', headers=header)
    if r.status_code == 200:
        logger.info('连接互联网成功')
    else:
        logger.error('无法连接互联网，请检查 DNS')


def errorExit():
    print('{0} -u <username> -p <password>'.format(sys.argv[0]))
    sys.exit()


def main():
    userName, password = None, None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:p:")
    except IndexError:
        errorExit()
    except getopt.GetoptError:
        errorExit()
    for opt, arg in opts:
        if opt == '-h':
            errorExit()
        elif opt == '-u':
            userName = arg
        elif opt == '-p':
            password = arg
    if userName is None or password is None:
        errorExit()
    redirect(userName, password)
    sys.exit()


if __name__ == "__main__":
    main()

