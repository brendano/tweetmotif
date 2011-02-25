#!/usr/bin/python

# Copyright 2008 Yongjian Xu (i3dmaster@gmail.com)
# License MIT

"""Protocol based timeout facility for urllib2.

Currently only support HTTP and HTTPS.

Achived by inheriting httplib.HTTPConnection and httplib.HTTPSConnection
classes and provide a timeout version of both. Timeout has been carefully
implemented per connection base. A HTTPConnectionTimeoutError or
HTTPSConnectionTimeoutError would be raised instead of the general socket.error
so that urlib2 wouldn't throw out URLError exception when timeout is hit.

This module also provides two overrided urllib2 HTTPHandler and HTTPSHandler
class for convenience. You should only need to call sethttpstimeout or
sethttpstimeout to setup the timeout enabled connections. The reset function
will restore the default. (disable timeout)

  Classes:
    HTTPConnectionTimeoutError: raised when timeout is hit
    HTTPSConnectionTimeoutError: raised when timeout is hit. HTTPS version.
    FTPConnectionTimeoutError: raised when timeout is hit. FTP version.
    TimeoutHTTPConnection: inherit class to override connect method of its
                           original to provide timeout functionality.
    TimeoutHTTPSConnection: the HTTPS version.
    TimeoutFTP: the FTP version.
    TimeoutFTPWrapper: Timeout FTP wrapper class.
    TimeoutHTTPHandler: The overrided HTTPHandler.
    TimeoutHTTPSHandler: The overrided HTTPSHandler.
    TimeoutFTPHandler: The overrided FTPHandler.

  Functions:
    sethttptimeout: set the timeout for all HTTP connections.
    sethttpstimeout: set the timeout for all HTTPS connections.
    setftptimeout: set the timeout for all ftp connections.
    reset: restore the default behavior.

Note:
1. This module is only needed for python version <= 2.5. If you are using
python 2.6 or higher, this feature is already builtin.
2. This module is not thread-safe. It is the client responsibility to make sure
urllib2 opener object does not get altered during the connection period.
e.g.
>>> import threading
>>> lck = threading.Lock()
>>> loc.aquaire()
>>> try:
...   timeout_http.sethttptimeout(10.0)
...   do_http_works()...
...   Done...
... finally:
...   timeout_http.reset()
...   loc.release()
Call to sethttptimeout will be blocked until the lock is released. But one can
still use establish http connections, just that all the connections will be
sharing the same timeout value.
3. HTTPConnection and HTTPSConnection have their own timeout attribute.
Although HTTPSConnection is inherited from HTTPConnection, the timeout
parameter does not get passed through. This enables client to deploy different
timeout strategy without affecting each other. For example, You can set HTTP
timeout to 5 seconds while setting HTTPS timeout to 20 seconds.
4. If you are not using urllib2, then timeout can be per connection base. Pass
a timeout parameter to your connection object and it only affects that socket
connection.
"""

import ftplib
from httplib import FakeSocket
from httplib import HTTPConnection as _HC
from httplib import HTTPSConnection as _HSC
from httplib import HTTPS_PORT
import socket
import urllib
import urllib2
from urllib2 import HTTPHandler as _H
from urllib2 import HTTPSHandler as _HS


def sethttptimeout(timeout):
  """Use TimeoutHTTPHandler and set the timeout value.
  
  Args:
    timeout: the socket connection timeout value.
  """
  if _under_26():
    opener = urllib2.build_opener(TimeoutHTTPHandler(timeout))
    urllib2.install_opener(opener)
  else:
    raise Error("This python version has timeout builtin")


def sethttpstimeout(timeout):
  """Use TimeoutHTTPSHandler and set the timeout value.

  Args:
    timeout: the socket connection timeout value.
  """
  if _under_26():
    opener = urllib2.build_opener(TimeoutHTTPSHandler(timeout))
    urllib2.install_opener(opener)
  else:
    raise Error("This python version has timeout builtin")


def setftptimeout(timeout):
  """
  """
  if _under_26():
    opener = urllib2.build_opener(TimeoutFTPHandler(timeout))
    urllib2.install_opener(opener)
  else:
    raise Error("This python version has timeout builtin")


def reset():
  """Restore to use default urllib2 openers."""
  urllib2.install_opener(urllib2.build_opener())


def _clear(sock):
  sock.close()
  return None


def _under_26():
  import sys
  if sys.version_info[0] < 2: return True
  if sys.version_info[0] == 2:
    return sys.version_info[1] < 6
  return False


class Error(Exception): pass

class HTTPConnectionTimeoutError(Error): pass

class HTTPSConnectionTimeoutError(Exception): pass

class FTPConnectionTimeoutError(Exception): pass


class TimeoutHTTPConnection(_HC):
  """A timeout control enabled HTTPConnection.
  
  Inherit httplib.HTTPConnection class and provide the socket timeout
  control.
  """
  _timeout = None

  def __init__(self, host, port=None, strict=None, timeout=None):
    """Initialize the object.

    Args:
      host: the connection host.
      port: optional port.
      strict: strict connection.
      timeout: socket connection timeout value.
    """
    _HC.__init__(self, host, port, strict)
    self._timeout = timeout or TimeoutHTTPConnection._timeout
    if self._timeout: self._timeout = float(self._timeout)

  def connect(self):
    """Perform the socket level connection.

    A new socket object will get built everytime. If the connection
    object has _timeout attribute, it will be set as the socket
    timeout value.

    Raises:
      HTTPConnectionTimeoutError: when timeout is hit
      socket.error: when other general socket errors encountered.
    """
    msg = "getaddrinfo returns an empty list"
    err = socket.error
    for res in socket.getaddrinfo(self.host, self.port, 0,
                                  socket.SOCK_STREAM):
      af, socktype, proto, canonname, sa = res
      try:
        try:
          self.sock = socket.socket(af, socktype, proto)
          if self._timeout: self.sock.settimeout(self._timeout)
          if self.debuglevel > 0:
            print "connect: (%s, %s)" % (self.host, self.port)
          self.sock.connect(sa)
        except socket.timeout, msg:
          err = socket.timeout
          if self.debuglevel > 0:
            print 'connect timeout:', (self.host, self.port)
          self.sock = _clear(self.sock)
          continue
        break
      except socket.error, msg:
        if self.debuglevel > 0:
          print 'general connect fail:', (self.host, self.port)
        self.sock = _clear(self.sock)
        continue
      break
    if not self.sock:
      if err == socket.timeout:
        raise HTTPConnectionTimeoutError, msg
      raise err, msg

class TimeoutHTTPSConnection(TimeoutHTTPConnection):
  """A timeout control enabled HTTPSConnection."""
  default_port = HTTPS_PORT
  _timeout = None

  def __init__(self, host, port=None, key_file=None, cert_file=None,
               strict=None, timeout=None):
    """Initialize the object.

    Args:
      host: the connection host.
      port: optional port.
      key_file: the ssl key file.
      cert_file: the ssl cert file.
      strict: strict connection.
      timeout: socket connection timeout value.

    TimeoutHTTPSConnection maintains its own _timeout attribute and
    does not override the its super class's value.
    """
    TimeoutHTTPConnection.__init__(self, host, port, strict)
    self._timeout = timeout or TimeoutHTTPSConnection._timeout
    if self._timeout: self._timeout = float(self._timeout)
    self.key_file = key_file
    self.cert_file = cert_file

  def connect(self):
    """Perform the secure http connection.
    
    Raises:
      HTTPSConnectionTimeoutError: when timeout is hit.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if self._timeout: sock.settimeout(self._timeout)
    try:
      sock.connect((self.host, self.port))
    except socket.timeout, msg:
      raise HTTPSConnectionTimeoutError, msg
    ssl = socket.ssl(sock, self.key_file, self.cert_file)
    self.sock = FakeSocket(sock, ssl)


class TimeoutFTP(ftplib.FTP):

  _timeout = None

  def __init__(self, host='', user='', passwd='', acct='', timeout=None):
    ftplib.FTP.__init__(self, host, user, passwd, acct)
    self._timeout = timeout or TimeoutFTP._timeout
    if self._timeout: self._timeout = float(self._timeout)
  
  def connect(self, host='', port=0):
    if host: self.host = host
    if port: self.port = port
    msg = "getaddrinfo returns an empty list"
    err = socket.error
    for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
      af, socktype, proto, canonname, sa = res
      try:
        try:
          self.sock = socket.socket(af, socktype, proto)
          if self._timeout: self.sock.settimeout(self._timeout)
          self.sock.connect(sa)
        except socket.timeout, msg:
          err = socket.timeout
          self.sock = _clear(self.sock)
          continue
        break
      except socket.error, msg:
        self.sock = _clear(self.sock)
        continue
      break
    if not self.sock:
      if err == socket.timeout:
        raise FTPConnectionTimeoutError, msg
      raise err, msg
    self.af = af
    self.file = self.sock.makefile('rb')
    self.welcome = self.getresp()
    return self.welcome

  def makeport(self):
    msg = "getaddrinfo returns an empty list"
    sock = None
    err = socket.error
    for res in socket.getaddrinfo(None, 0, self.af, socket.SOCK_STREAM, 0,
        socket.AI_PASSIVE):
      af, socktype, proto, canonname, sa = res
      try:
        try:
          sock = socket.socket(af, socktype, proto)
          if self._timeout: sock.settimeout(self._timeout)
          sock.bind(sa)
        except socket.timeout, msg:
          sock = _clear(sock)
          continue
        break
      except socket.error, msg:
        sock = _clear(sock)
        continue
      break
    if not sock:
      if err == socket.timeout:
        raise FTPConnectionTimeoutError, msg
      raise err, msg
    sock.listen(1)
    port = sock.getsockname()[1]
    host = self.sock.getsockname()[0]
    if self.af == socket.AF_INET:
      resp = self.sendport(host, port)
    else:
      resp = self.sendeprt(host, port)
    return sock

  def ntransfercmd(self, cmd, rest=None):
    size = None
    err = socket.error
    if self.passiveserver:
      host, port = self.makepasv()
      af, socktype, proto, canon, sa = socket.getaddrinfo(host, port, 0,
                                                          socket.SOCK_STREAM)[0]
      try:
        try:
          conn = socket.socket(af, socktype, proto)
          if self._timeout: conn.settimeout(self._timeout)
          conn.connect(sa)
        except socket.timeout, msg:
          err = socket.timeout
          conn = _clear(conn)
      except socket.error, msg:
        conn = _clear(conn)
      if not conn:
        if err == socket.timeout:
          raise FTPConnectionTimeoutError, msg
        raise err, msg
      if rest is not None:
        self.sendcmd("REST %s" % rest)
      resp = self.sendcmd(cmd)
      if resp[0] == '2':
        resp = self.getresp()
      if resp[0] != '1':
        raise ftplib.error_reply, resp
    else:
      sock = self.makeport()
      if rest is not None:
        self.sendcmd("REST %s" % rest)
      resp = self.sendcmd(cmd)
      if resp[0] == '2':
        resp = self.getresp()
      if resp[0] != '1':
        raise ftplib.error_reply, resp
      conn, sockaddr = sock.accept()
    if resp[:3] == '150':
      size = ftplib.parse150(resp)
    return conn, size
          


class TimeoutHTTPHandler(_H):
  """A timeout enabled HTTPHandler for urllib2."""
  def __init__(self, timeout=None, debuglevel=0):
    """Initialize the object.

    Args:
      timeout: the socket connect timeout value.
      debuglevel: the debuglevel level.
    """
    _H.__init__(self, debuglevel)
    TimeoutHTTPConnection._timeout = timeout

  def http_open(self, req):
    """Use TimeoutHTTPConnection to perform the http_open"""
    return self.do_open(TimeoutHTTPConnection, req)

class TimeoutHTTPSHandler(_HS):
  """A timeout enabled HTTPSHandler for urllib2."""
  def __init__(self, timeout=None, debuglevel=0):
    """Initialize the object.

    Args:
      timeout: the socket connect timeout value.
      debuglevel: the debuglevel level.
    """
    _HS.__init__(self, debuglevel)
    TimeoutHTTPSConnection._timeout = timeout

  def https_open(self, req):
    """Use TimeoutHTTPSConnection to perform the https_open"""
    return self.do_open(TimeoutHTTPSConnection, req)

class TimeoutFTPWrapper(urllib.ftpwrapper):

  def __init__(self, user, passwd, host, port, dirs, timeout=None):
    self._timeout = timeout
    urllib.ftpwrapper.__init__(self, user, passwd, host, port, dirs)

  def init(self):
    self.busy = 0
    self.ftp = TimeoutFTP(timeout=self._timeout)
    self.ftp.connect(self.host, self.port)
    self.ftp.login(self,user, self.passwd)
    for dir in self.dirs:
      self.ftp.cwd(dir)

class TimeoutFTPHandler(urllib2.FTPHandler):

  def __init__(self, timeout=None, debuglevel=0):
    self._timeout = timeout
    self._debuglevel = debuglevel

  def connect_ftp(self, user, passwd, host, port, dirs, timeout=None):
    if timeout: self._timeout = timeout
    fw = TimeoutFTPWrapper(user, passwd, host, port, dirs, self._timeout)
    fw.ftp.set_debuglevel(self._debuglevel)
    return fw
