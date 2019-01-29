# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for Apache configuration management.'''


import os
import os.path
import re
import string
from cStringIO import StringIO

# import glob
# import sys
# import shutil
# import utils

DEBUG = False

HTTPD_CONF_DIR = '/etc/httpd/'
# HTTPD_CONF_DIR = '/Users/douzhenjiang/Projects/intranet-panel/lib/intranet/'
HTTPD_CONF = '/etc/httpd/conf/httpd.conf'
SERVERCONF = '/etc/httpd/conf.d/'
COMMENTFLAG = '#v#'
GENBY = 'Generated by Intranet'
ABC = '/etc/httpd/conf.d/abc.com.conf'


CONFIGS = {
    'ServerTokens': 'OS',
    'ServerRoot': '/etc/httpd',
    'Timeout': 60,
    'DefaultType': 'text/plain',
    'DocumentRoot': '/var/www/html',
    'DirectoryIndex': 'index.html index.html.var',
    'AddDefaultCharset': 'UTF-8',
    'Listen': 80,
    'ServerAdmin': 'root@localhost',
    'ServerName': 'www@localhost',
    'NameVirtualHost': '*:80',
    'KeepAlive': 'Off',
    'MaxKeepAliveRequests': 100,
    'KeepAliveTimeout': 15,
    'UseCanonicalName': 'Off',
    'AccessFileName': '.htaccess',
    'TypesConfig': '/etc/mime.types',
    'HostnameLookups': 'Off',
    'ErrorLog': 'logs/error_log',
    'LogLevel': 'debug, info, notice, warn, error, crit, alert, emerg',
    'ServerSignature': 'On',
    'IndexOptions': 'FancyIndexing VersionSort NameWidth=* HTMLTable Charset=UTF-8',
    'Alias': '',
}

DIRECTIVES = {
    'Directory': '',
    'Files': '',
    'Limit': '',
    'Location': '',
    'VirtualHost': ''
}

OPTIONS = {
    'ServerAdmin': 'admin@localhost',
    'ServerName': 'www',
    'DocumentRoot': '/var/www',
    'Indexs': '',
    'Options': '',
    'ServerAlias': '',
    'Location': '',
    'SuexecUserGroup': '',
}

DIRECTORY = {
    'Options': 'Indexes FollowSymLinks MultiViews',
    'AllowOverride': 'None',
    'Order': 'allow,deny',
    'Allow': 'from all',
}


vHostTemplate = '''<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www
    <Directory />
        Options FollowSymLinks
        AllowOverride None
    </Directory>
    <Directory /var/www/>
        Options Indexes FollowSymLinks MultiViews
        AllowOverride None
        Order allow,deny
        allow from all
    </Directory>
</VirtualHost>
'''


def getservers(config=None):
    '''Get servers from apache configuration files.
    '''

    servers = []
    # SERVERCONF = '/Users/douzhenjiang/Projects/intranet-panel/test'
    # aaa = '/etc/httpd/conf.d/aaa.com.conf'
    # bbb = '/etc/httpd/conf.d/bbb.com.conf'

    clist = os.listdir(SERVERCONF)  # 列出文件夹下所有的目录与文件
    for i in range(0, len(clist)):
        path = os.path.join(SERVERCONF, clist[i])
        if os.path.isfile(path) and os.path.splitext(path)[1] == '.conf':
            v = _load_virtualhost(path)
            if v is not False:
                servers.extend(v)

    # servers = _load_virtualhost(aaa) + _load_virtualhost(bbb)
    return servers


def _load_virtualhost(conf=''):
    '''parser VirtualHost config to python object (array)
    '''
    try:
        if not conf or not os.path.isfile(conf):
            return False
    except OSError:
        return False

    with open(conf, 'r') as f:
        lines = f.readlines()
        data = filter(lambda i: re.search('^((?!#).)*$', i), lines)

    id_v = 0
    enable = False
    virtualHosts = []
    vhost = []
    result = {}
    id_d = 0
    enable_d = False
    v_dirs = {}
    result_d = {}
    directorys = {}  # 附加信息
    line_disabled = False
    gen_by_intranet = False
    match_start = re.compile(r'<VirtualHost(\s+)(\S+)>')
    match_end = re.compile(r'</VirtualHost>')
    match_start_d = re.compile(r'<Directory(\s+)(\S+)>')
    match_end_d = re.compile(r'</Directory>')
    while len(data) > 0:
        out = data.pop(0)

        # deal with our speical comment string
        if out.startswith(COMMENTFLAG):
            while out.startswith(COMMENTFLAG):
                out = out[3:]
            out = out.strip()
            line_disabled = True

        if not out or out.startswith('#'):
            continue

        # deal with comment and detect intranet flag in comment
        fields = out.split('#', 1)
        out = fields[0].strip()
        if len(fields) > 1 and fields[1].strip() == GENBY:
            gen_by_intranet = True

        # start of VirtualHost
        match = match_start.search(out)
        if match:  # if '<VirtualHost' in out:
            id_d = 0
            v_dirs = {}
            result_d[id_v] = []
            directorys[id_v] = []
            name_port = match.groups()[1].strip(' ').strip('"').strip('\'')
            ip, port = name_port.split(':')
            vhost.append(ip)
            vhost.append(port)
            enable = True
            enable_d = False
            continue

        # start of Directory in VirtualHost
        match_d = match_start_d.search(out)
        if enable is True and match_d:
            v_dirs = {}
            path = match_d.groups()[1].strip()
            v_dirs[id_d] = []
            v_dirs[id_d].append(path)
            enable_d = True
            continue

        # end of Directory in VirtualHost
        # if '</Directory>' in out:
        if enable_d is True and match_end_d.search(out):
            result_d[id_v].append(v_dirs[id_d])
            id_d += 1
            enable_d = False
            v_dirs = {}
            continue

        # merge of Directory in VirtualHost
        if enable_d:
            v_dirs[id_d].append(out)
            continue

        # end of VirtualHost
        if match_end.search(out):
            enable_d = False

            result[id_v] = vhost
            if id_v in result_d:
                d = _append_directory(result_d[id_v])
                directorys[id_v] = d
            else:
                directorys[id_v] = []
            id_v += 1
            enable = False
            vhost = []
            continue

        # merge of VirtualHost
        if enable:
            vhost.append(out)
            continue

    # print('directorys', directorys)
    for i in result:
        server = {
            'IP': result[i][0],  # IP
            'Port': result[i][1],  # Port
            'Directory': directorys[i]
        }
        for line in result[i]:
            for i in OPTIONS:
                if i in line:
                    if i in ['ServerAlias', 'DirectoryIndex']:
                        server[i] = ' '.join(str(n) for n in line.split()[1:])
                    else:
                        server[i] = line.split()[1].strip(string.punctuation)
                    continue
        virtualHosts.append(server)

    return virtualHosts


def _append_directory(res):
    if not res:
        return []

    directorys = []
    for r in res:
        directory = {'Path': r[0]}
        for line in r:
            for i in DIRECTORY:
                if i in line:
                    if i in ['Order']:
                        directory[i] = ','.join(
                            str(n) for n in line.split()[1:])
                    elif i in ['Options', 'Allow']:
                        directory[i] = ' '.join(
                            str(n) for n in line.split()[1:])
                    else:
                        directory[i] = line.split()[1].strip(
                            string.punctuation)
                    continue
        directorys.append(directory)

    return directorys


def virtual_host_config(site, key, val, port=80):
    '''
    site: abc.com
    key: VirtualHost or DocumentRoot or ServerAdmin or Directory
    val: /var/www
    '''
    keys = ['VirtualHost', 'DocumentRoot', 'ServerAdmin', 'Directory']
    if key not in keys or not site or not val:
        return False

    conf = SERVERCONF + site + '.conf'
    try:
        os.stat(conf)
    except OSError:
        print('site config file not exist')
        return False

    old_conf = open(conf).read()

    with open(conf + '.bak', 'w') as f:
        # backup
        f.write(old_conf)

    if key == 'VirtualHost':
        conf = SERVERCONF + val + '.conf'
        val = str(val) + ':' + str(port)
        # os.renames(SERVERCONF + site + '.conf', conf + '.bak')

    # make new config
    new_conf = re.sub(key + ' "(.*?)"',
                      key + ' "' + val + '"',
                      old_conf)

    # save new config file
    with open(conf, 'w') as f:
        f.write(new_conf)
        # delete old site config file
        if key == 'VirtualHost' and os.stat(conf) and os.stat(SERVERCONF + site + '.conf.bak'):
            os.remove(SERVERCONF + site + '.conf')
        return True


# https://blog.csdn.net/brucemj/article/details/37933519
# https://oomake.com/question/266681


def replace_docroot(vhost, new_docroot):
    '''yield new lines of an httpd.conf file where docroot lines matching
        the specified vhost are replaced with the new_docroot
    '''
    vhost_start = re.compile(r'<VirtualHost\s+(.*?)>')
    vhost_end = re.compile(r'</VirtualHost>')
    docroot_re = re.compile(r'(DocumentRoot\s+)(\S+)')
    file = open(HTTPD_CONF_DIR + vhost + '.conf').read()
    conf_file = StringIO(file)
    in_vhost = False
    curr_vhost = None
    for line in conf_file:
        # 起始行查找host
        vhost_start_match = vhost_start.search(line)
        if vhost_start_match:
            curr_vhost = vhost_start_match.groups()[0]
            in_vhost = True
            print(curr_vhost, vhost)
        if in_vhost and (curr_vhost == vhost):
            docroot_match = docroot_re.search(line)
            if docroot_match:
                sub_line = docroot_re.sub(r'\1%s' % new_docroot, line)
                line = sub_line
            vhost_end_match = vhost_end.search(line)
            if vhost_end_match:
                in_vhost = False
            yield line


def loadconfig(conf=None, getlineinfo=False):
    """Load apache config and return a dict.
    """
    if not conf:
        conf = HTTPD_CONF
    if not os.path.exists(conf):
        return False
    return _loadconfig(conf, getlineinfo)


def _loadconfig(conf, getlineinfo):
    '''load Apache httpd.conf'''

    # if key not in CONFIGS or not val:
    #     return False
    conf = HTTPD_CONF
    # conf = HTTPD_CONF_DIR + '/httpd.conf'
    try:
        os.stat(conf)
    except OSError:
        print('site config file not exist')
        return False

    configs = {}
    with open(conf) as f:
        for line_index, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            for i in CONFIGS:
                if line.startswith(i):
                    if i in ['IndexOptions', 'DirectoryIndex']:
                        configs[i] = ' '.join(str(n) for n in line.split()[1:])
                    else:
                        configs[i] = line.split()[1].strip(string.punctuation)
                    print(line_index, i, line)
        return configs


def _context_getservers(disabled=None, config=None, getlineinfo=True):
    """Get server context configs.
    """
    if not config or config['_isdirty']:
        config = loadconfig(HTTPD_CONF, getlineinfo)
    http = config['_'][0]['http'][0]
    if not http.has_key('server'):
        return []
    servers = http['server']
    if disabled == None or not getlineinfo:
        return servers
    else:
        return [server for server in servers
                if server['_param']['disabled'] == disabled]


# if __name__ == '__main__':
    # virtual_host_config('aaa.com', 'DocumentRoot', '/v/asfs34535')
    # virtual_host_config('aaa.com', 'ServerAdmin', '4567896543')
    # virtual_host_config('aaa.com', 'VirtualHost', 'bbb.com', 567)

    # for line in replace_docroot('aaa.com', 'docroot'):
    #     print(line)

    # aaa = '/Users/douzhenjiang/Projects/intranet-panel/aaa.com.conf'
    # bbb = '/Users/douzhenjiang/Projects/intranet-panel/httpd.conf'
    # print _load_virtualhost(aaa)

    # # print _load_virtualhost('/etc/httpd/conf.d/bbb.com.conf')
    # print getservers()

    # path = os.path.join(SERVERCONF, clist[i])
    # print os.path.splitext('/Users/douzhenjiang/Projects/intranet-panel/lib/intranet/test/aaa.com')
