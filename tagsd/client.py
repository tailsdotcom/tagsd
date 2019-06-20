# -*- coding: utf-8 -*-
import abc
import random
import socket

import six
import structlog
from statsd.client.timer import Timer
from statsd.client.udp import Pipeline

logger = structlog.get_logger(__name__)


class DummyStatsDClient(object):
    def pipeline(self):
        pass

    def timer(self, stat, rate=1):
        pass

    def timing(self, stat, delta, rate=1, tags=None):
        pass

    def incr(self, stat, count=1, rate=1, tags=None):
        pass

    def decr(self, stat, count=1, rate=1, tags=None):
        pass

    def gauge(self, stat, value, rate=1, delta=False, tags=None):
        pass

    def set(self, stat, value, rate=1, tags=None):
        pass


class StatsDTelegrafClientBase(object):
    """
    Telegraf compatible statsd client base.
    This base client supports telegraf /influxdb / datadog style tags
    over statsd protocol

    This class is a superset of StatsClientBase from pystatsd written by jsocol.
    Support for tags was added by Dinesh Vitharanage.

    Original copyright notice:
    Copyright (c) 2012, James Socol

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, default_tags=None, prefix=None):
        self._prefix = prefix
        self._default_tags = default_tags or {}

    @abc.abstractmethod
    def _send(self):
        pass

    @abc.abstractmethod
    def pipeline(self):
        pass

    def timer(self, stat, rate=1):
        return Timer(self, stat, rate)

    def timing(self, stat, delta, rate=1, tags=None):
        """Send new timing information. `delta` is in milliseconds."""
        self._send_stat(stat, '%0.6f|ms' % delta, rate, tags=tags)

    def incr(self, stat, count=1, rate=1, tags=None):
        """Increment a stat by `count`."""
        self._send_stat(stat, '%s|c' % count, rate, tags=tags)

    def decr(self, stat, count=1, rate=1, tags=None):
        """Decrement a stat by `count`."""
        self.incr(stat, -count, rate, tags=tags)

    def gauge(self, stat, value, rate=1, delta=False, tags=None):
        """Set a gauge value."""
        if value < 0 and not delta:
            if rate < 1:
                if random.random() > rate:
                    return
            with self.pipeline() as pipe:
                pipe._send_stat(stat, '0|g', 1, tags=tags)
                pipe._send_stat(stat, '%s|g' % value, 1, tags=tags)
        else:
            prefix = '+' if delta and value >= 0 else ''
            self._send_stat(stat, '%s%s|g' % (prefix, value), rate, tags=tags)

    def set(self, stat, value, rate=1, tags=None):
        """Set a set value."""
        self._send_stat(stat, '%s|s' % value, rate, tags)

    def _send_stat(self, stat, value, rate, tags=None):
        self._after(self._prepare(stat, value, rate, tags=tags))

    def _prepare(self, stat, value, rate, tags=None):
        if rate < 1:
            if random.random() > rate:
                return
            value = '{}|@{}'.format(value, rate)

        if self._prefix:
            stat = '{}.{}'.format(self._prefix, stat)

        all_tags = {k: v for k, v in six.iteritems(self._default_tags)
                    if isinstance(v, six.string_types)}

        try:
            for tag, val in six.iteritems(tags):
                all_tags[tag] = val
        except AttributeError:
            pass

        if all_tags:
            tag_string = ','.join(
                self._build_tag(k, v) for k, v in six.iteritems(all_tags))
            return '{},{}:{}'.format(stat, tag_string, value)

        return '{}:{}'.format(stat, value)

    def _build_tag(self, tag, value):
        if value:
            return '{}={}'.format(str(tag), str(value))
        else:
            return tag

    def _after(self, data):
        if data:
            self._send(data)


class StatsDNoiseless(StatsDTelegrafClientBase):
    """
    This is a noiseless implementation of statsd.client.udp.StatsClient.

    The package provided StatsClient raises exceptions at instantiation time
    if it is unable to open a socket connection to the host provided. This
    implementation simply ignores errors caused when trying to open the socket
    connection, while still returning an API that does nothing.
    """

    def __init__(self, host, port=8125, prefix=None,
                 maxudpsize=512, ipv6=False, default_tags=None):
        self._addr = None
        self._sock = None
        self._host = host
        self._port = port
        self._ipv6 = ipv6
        self._prefix = prefix
        self._maxudpsize = maxudpsize
        self._default_tags = default_tags or {}

    def _create_socket(self):
        """
        Create a new client.
        :raises socket.error:
        """
        fam = socket.AF_INET6 if self._ipv6 else socket.AF_INET
        family, _, _, _, addr = socket.getaddrinfo(
            self._host, self._port, fam, socket.SOCK_DGRAM)[0]
        self._addr = addr
        self._sock = socket.socket(family, socket.SOCK_DGRAM)

    def _send(self, data):
        """Send data to statsd."""
        try:
            if not self._sock:
                self._create_socket()

            self._sock.sendto(data.encode('ascii'), self._addr)
        except (socket.error, RuntimeError) as e:
            logger.exception(e)

    def pipeline(self):
        return Pipeline(self)
