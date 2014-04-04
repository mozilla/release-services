Deployment Environment
======================

RelengAPI is designed for flexible deployment.
It is a simple WSGI application that can run on a developer's laptop or in a production environment.

In practice, it runs on a cluster of VMs at Mozilla, using Apache Httpd and ``mod_wsgi``.
However, in principle nothing in the design of the system precludes hosting on services like [Elastic Beanstalk](http://aws.amazon.com/elasticbeanstalk/), [Heroku](https://www.heroku.com/) or [Mozilla's PaaS](https://wiki.mozilla.org/Paas_Apps).

