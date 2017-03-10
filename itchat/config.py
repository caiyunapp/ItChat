import os, platform

VERSION = '1.2.29'
BASE_URL = 'https://login.weixin.qq.com'
OS = platform.system() #Windows, Linux, Darwin
DIR = os.getcwd()
DEFAULT_QR = 'QR.png'

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
BOT_NAME = os.getenv('ITCHAT_BOT_NAME') or 'bot'
QR_URL = os.getenv('ITCHAT_QR_URL') or ''
BEARY_URL = os.getenv('ITCHAT_BEARY_URL') or ''
REDIS_URL = os.getenv('ITCHAT_REDIS_URL') or ''
