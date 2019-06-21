tagsd
=====

[![Build Status](https://travis-ci.org/tailsdotcom/tagsd.svg?branch=master)](https://travis-ci.org/tailsdotcom/tagsd)
[![codecov](https://codecov.io/gh/tailsdotcom/tagsd/branch/master/graph/badge.svg)](https://codecov.io/gh/tailsdotcom/tagsd)

Telegraf compatible statsd client with rich support for tags

Usage
-----
```python
from tagsd import StatsDNoiseless

client = StatsDNoiseless(host='remote.server', default_tags={'some': 'value'})

client.incr('test.namespace')

# emits test.namespace:1|c,some=value
```

Installation
------------
```bash
pip install git+https://github.com/tailsdotcom/tagsd.git
```

Compatibility
-------------
This package supports following python versions:
- Python 2.7 (Support will be dropped end of 2019)
- Python 3.6 
- Python 3.7 

Authors
-------

`tagsd` was written by `Dinesh Vitharanage <d@dnsh.io>`.
