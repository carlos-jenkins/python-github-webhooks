#!/usr/bin/env python
import argparse
import requests

from get_neighbors import get_names


def alert_neighbors(neighbors):
   for n in neighbors:
       requests.get("http://{}/")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--asg-name', type=str, default='puppet-master-stage')
    parser.add_argument('-h', '--host-list', nargs='+', type=list, default=[])

    args = parser.parse_args()

    if not args.host_list:
        args.host_list = get_names(args.asg_name)

    for n in get_names(args.asg_name):
        print n
