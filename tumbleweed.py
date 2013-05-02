# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2013, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
"""\
A consumer of status message. This will persist a status message
in the acmeio database.

"""
import logging
import argparse
import json
import urllib2
from logging.config import fileConfig as load_logging_configuration
from ConfigParser import RawConfigParser

import pika
import psycopg2


QUEUE = 'acme-status'
logger = logging.getLogger('tumbleweed')
# Global configuration object
config = None


class Config(object):
    """\
    A configuration agend that holds and acts on information about the
    consumer connection, message queue(s) to follow, and what code &
    additional information should be run & handed to the code when
    a message is recieved (runner settings).

    """

    def __init__(self, settings, amqp):
        self.settings = settings
        self.amqp = amqp

    @classmethod
    def from_file(cls, ini_file):
        """Used to initialize the configuration object from an INI file."""
        config = RawConfigParser()
        if hasattr(ini_file, 'read'):
            config.readfp(ini_file)
        else:
            with open(ini_file, 'r') as f:
                config.readfp(f)

        def config_to_dict(c):
            result = {}
            for section in c.sections():
                result[section] = dict(c.items(section))
            return result

        all_settings = config_to_dict(config)
        settings = all_settings['tumbleweed']
        amqp = all_settings['amqp']
        return cls(settings, amqp)


def handle_delivery(channel, method, headers, body):
    global config
    db_connection = psycopg2.connect(config.settings['database'])
    cursor = db_connection.cursor()

    data = json.loads(body)
    job_id = data['job']
    status = data['status']
    cursor.execute("SELECT id FROM status WHERE name = %s", (status,))
    status_id = cursor.fetchone()[0]
    # XXX Message is currently dropped because PyBit doesn't have a
    #     field for it.'
    msg = data.get('message', '')

    # Insert the status
    cursor.execute("INSERT INTO jobstatus (job_id, status_id) VALUES (%s, %s)",
                   (job_id, status_id,))

    # Check completion for callback invocation
    if status == 'Done':
        cursor.execute("SELECT url FROM callbacks WHERE job_id = %s", (job_id,))
        callback = cursor.fetchone()
        if callback is not None:
            url = callback[0]
            urllib2.urlopen(url)

    db_connection.commit()
    cursor.close()
    db_connection.close()
    channel.basic_ack(method.delivery_tag)

def on_connected(connection):
    """Called after an amqp connection has been established."""
    # Open a new channel.
    connection.channel(on_open_channel)

def on_open_channel(channel):
    """Called when a new channel has been established."""
    global config
    def on_queue_declared(frame):
        channel.basic_consume(handle_delivery, queue=QUEUE)
    channel.queue_declare(queue=QUEUE, durable=True, exclusive=False,
                          auto_delete=False, callback=on_queue_declared)

def main(argv=None):
    """Command line utility"""
    parser = argparse.ArgumentParser(description="PyBit builder for rhaptos")
    parser.add_argument('config', type=argparse.FileType('r'),
                        help="INI configuration file")
    args = parser.parse_args(argv)

    load_logging_configuration(args.config)
    # Re-spool the file for a future read.
    args.config.seek(0)
    # Load the configuration
    global config
    config = Config.from_file(args.config)

    host = config.amqp.get('host', 'localhost')
    port = int(config.amqp.get('port', 5672))
    user = config.amqp.get('user')
    password = config.amqp.get('password')
    virtual_host = config.amqp.get('virtual_host')

    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(host, port, virtual_host,
                                           credentials)
    connection = pika.SelectConnection(parameters, on_connected)

    try:
        # Loop so we can communicate with RabbitMQ
        connection.ioloop.start()
    except KeyboardInterrupt:
        # Gracefully close the connection
        connection.close()
        # Loop until we're fully closed, will stop on its own
        connection.ioloop.start()

if __name__ == '__main__':
    main()
