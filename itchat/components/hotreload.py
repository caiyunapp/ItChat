import pickle, os
import logging, traceback

import requests
import redis

from .. import config
from ..config import VERSION
from ..returnvalues import ReturnValue
from .contact import update_local_chatrooms, update_local_friends
from .messages import produce_msg

logger = logging.getLogger('itchat')

def load_hotreload(core):
    core.dump_login_status = dump_login_status_redis
    core.load_login_status = load_login_status_redis

def dump_login_status(self, fileDir=None):
    fileDir = fileDir or self.hotReloadDir
    try:
        with open(fileDir, 'w') as f:
            f.write('itchat - DELETE THIS')
        os.remove(fileDir)
    except:
        raise Exception('Incorrect fileDir')
    status = {
        'version'   : VERSION,
        'loginInfo' : self.loginInfo,
        'cookies'   : self.s.cookies.get_dict(),
        'storage'   : self.storageClass.dumps()}
    with open(fileDir, 'wb') as f:
        pickle.dump(status, f)
    logger.info('Dump login status for hot reload successfully.')

def load_login_status(self, fileDir,
        loginCallback=None, exitCallback=None):
    try:
        with open(fileDir, 'rb') as f:
            j = pickle.load(f)
    except Exception as e:
        logger.debug('No such file, loading login status failed.')
        return ReturnValue({'BaseResponse': {
            'ErrMsg': 'No such file, loading login status failed.',
            'Ret': -1002, }})

    if j.get('version', '') != VERSION:
        logger.debug(('you have updated itchat from %s to %s, ' +
            'so cached status is ignored') % (
            j.get('version', 'old version'), VERSION))
        return ReturnValue({'BaseResponse': {
            'ErrMsg': 'cached status ignored because of version',
            'Ret': -1005, }})
    self.loginInfo = j['loginInfo']
    self.s.cookies = requests.utils.cookiejar_from_dict(j['cookies'])
    self.storageClass.loads(j['storage'])
    msgList, contactList = self.get_msg()
    if (msgList or contactList) is None:
        self.logout()
        load_last_login_status(self.s, j['cookies'])
        logger.warning('server refused, loading login status failed.')
        return ReturnValue({'BaseResponse': {
            'ErrMsg': 'server refused, loading login status failed.',
            'Ret': -1003, }})
    else:
        if contactList:
            for contact in contactList:
                if '@@' in contact['UserName']:
                    update_local_chatrooms(self, [contact])
                else:
                    update_local_friends(self, [contact])
        if msgList:
            msgList = produce_msg(self, msgList)
            for msg in msgList: self.msgList.put(msg)
        self.start_receiving(exitCallback)
        logger.debug('loading login status succeeded.')
        if hasattr(loginCallback, '__call__'):
            loginCallback()
        return ReturnValue({'BaseResponse': {
            'ErrMsg': 'loading login status succeeded.',
            'Ret': 0, }})

def load_last_login_status(session, cookiesDict):
    try:
        session.cookies = requests.utils.cookiejar_from_dict({
            'webwxuvid': cookiesDict['webwxuvid'],
            'webwx_auth_ticket': cookiesDict['webwx_auth_ticket'],
            'login_frequency': '2',
            'last_wxuin': cookiesDict['wxuin'],
            'wxloadtime': cookiesDict['wxloadtime'] + '_expired',
            'wxpluginkey': cookiesDict['wxloadtime'],
            'wxuin': cookiesDict['wxuin'],
            'mm_lang': 'zh_CN',
            'MM_WX_NOTIFY_STATE': '1',
            'MM_WX_SOUND_STATE': '1', })
    except:
        logger.info('Load status for push login failed, we may have experienced a cookies change.')
        logger.info('If you are using the newest version of itchat, you may report a bug.')


def dump_login_status_redis(self, fileDir=None):
    fileDir = fileDir or self.hotReloadDir
    status = {
        'version'   : VERSION,
        'loginInfo' : self.loginInfo,
        'cookies'   : self.s.cookies.get_dict(),
        'storage'   : self.storageClass.dumps()}
    pkls = pickle.dumps(status)
    redis_client = redis.StrictRedis.from_url(config.REDIS_URL)
    redis_client.set(fileDir, pkls)
    logger.info('Dump login status for hot reload successfully.')


def load_login_status_redis(self, fileDir,
        loginCallback=None, exitCallback=None):
    try:
        redis_client = redis.StrictRedis.from_url(config.REDIS_URL)
        pkls = redis_client.get(fileDir)
        j = pickle.loads(pkls)
    except Exception as e:
        logger.warning('No such file, loading login status failed.')
        return ReturnValue({'BaseResponse': {
            'ErrMsg': 'No such file, loading login status failed.',
            'Ret': -1002, }})

    if j.get('version', '') != VERSION:
        logger.debug(('you have updated itchat from %s to %s, ' +
            'so cached status is ignored') % (
            j.get('version', 'old version'), VERSION))
        return ReturnValue({'BaseResponse': {
            'ErrMsg': 'cached status ignored because of version',
            'Ret': -1005, }})
    self.loginInfo = j['loginInfo']
    self.s.cookies = requests.utils.cookiejar_from_dict(j['cookies'])
    self.storageClass.loads(j['storage'])
    msgList, contactList = self.get_msg()
    if (msgList or contactList) is None:
        self.logout()
        load_last_login_status(self.s, j['cookies'])
        logger.warning('server refused, loading login status failed.')
        return ReturnValue({'BaseResponse': {
            'ErrMsg': 'server refused, loading login status failed.',
            'Ret': -1003, }})
    else:
        if contactList:
            for contact in contactList:
                if '@@' in contact['UserName']:
                    update_local_chatrooms(self, [contact])
                else:
                    update_local_friends(self, [contact])
        if msgList:
            msgList = produce_msg(self, msgList)
            for msg in msgList: self.msgList.put(msg)
        self.start_receiving(exitCallback)
        logger.info('loading login status succeeded.')
        if hasattr(loginCallback, '__call__'):
            loginCallback()
        return ReturnValue({'BaseResponse': {
            'ErrMsg': 'loading login status succeeded.',
            'Ret': 0, }})
