---
layout: post
title: Have Fun with Logging
tags: 
- python
---

In python, the imported module is self-contained.  The logger called in the imported module will only be available in that module. 

Self-defined logger:

{% highlight python %}

import logging

logger= logging.getLogger('a')
logger.propagate = False
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s.%(lineno)d %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

{% endhighlight %}

Cautious! Running this snip more than once, it will add handlers to the logger.  As a result, calling the logger will print multiple logging messages.  

Loggers are different from print.  It need the string type.  In that sense, loggers are more like sprintf.  This would not run without that %s. 

{% highlight python %}
logger.debug('- Fitting for pixel: %s', pix)
{% endhighlight %}


