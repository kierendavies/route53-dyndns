#!/usr/bin/python

import boto.route53
import configargparse
import logging
import os
import re
import urllib.request

arg_parser = configargparse.ArgumentParser(default_config_files=["/etc/route53-dyndns.conf"])
arg_parser.add("-c", "--config", is_config_file=True, help="config file path")
arg_parser.add("-f", "--ip-file", default="/var/opt/route53-dyndns/ip")
arg_parser.add("--aws-secret-access-key", required=True)
arg_parser.add("--aws-access-key-id", required=True)
arg_parser.add("--aws-region", required=True)
arg_parser.add("--zone-name", required=True)
arg_parser.add("--record-name", required=True)
config = arg_parser.parse_args()

logger = logging.getLogger("route53-dyndns")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

ip_address = urllib.request.urlopen("http://icanhazip.com/").read().decode("utf-8").strip()

if not re.fullmatch("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip_address):
    logger.error("Invalid IP address: %s", ip_address)
    exit(1)

cached_ip_address = ""
try:
    with open(config.ip_file, "r") as f:
        cached_ip_address = f.read().strip()
except FileNotFoundError:
    logger.info("IP file does not exist: %s", config.ip_file)
    os.makedirs(os.path.dirname(config.ip_file))

if ip_address == cached_ip_address:
    logger.info("IP address unchanged")
else:
    logger.info("Setting IP address: %s", ip_address)

    connection = boto.route53.connect_to_region(
        config.aws_region,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key
    )
    zone = connection.get_zone(config.zone_name)
    zone.update_a("{}.{}".format(config.record_name, config.zone_name), ip_address)

    with open(config.ip_file, "w") as f:
        f.write(ip_address)
