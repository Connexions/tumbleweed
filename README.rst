Tumbleweed
==========

A consumer of status message. This will persist a status message
in the ``acmeio`` database.

This process serves another purpose, in that if a callback URL was
given on job creation, it invokes the callback URL when a job has been
completed. 

Getting Started
---------------

Install the python package::

    $ python setup.py install

Run the process using the generated script::

    $ tumbleweed development.ini

You may need to change the values in ``development.ini`` to reflect
your installation.
