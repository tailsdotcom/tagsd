# Sample Test passing with nose and pytest
import mock

from tagsd.client import StatsDNoiseless


def _send_catcher(data):
    pass

class DummySender(object):
    _args = ()
    _kwargs = {}

    def __call__(self, *args, **kwargs):
        self._args = args,
        self._kwargs = kwargs


def argtest(return_val):
    """ Mocks functions with a return value provided + stores args and kwargs that was used to call the function"""
    class TestArgs(object):
        def __call__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            return return_val
    return TestArgs()


@mock.patch('tagsd.client.StatsDNoiseless._send', argtest(None))
def test_default_tags_are_included():
    client = StatsDNoiseless(host='dev.null', default_tags={'stage': 'prod'})

    client.incr('dummy.namespace')

    assert 'stage=prod' in client._send.args[0]


@mock.patch('tagsd.client.StatsDNoiseless._send', argtest(None))
def test_event_level_tags():
    client = StatsDNoiseless(host='dev.null')

    client.incr('dummy.namespace', tags={'scope': 'user'})

    assert 'scope=user' in client._send.args[0]