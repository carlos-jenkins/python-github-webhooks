#!/usr/bin/env python
import argparse
import socket

import boto3


def get_names(asg_name):
    asg = boto3.client('autoscaling')
    ec2 = boto3.client('ec2')

    instances = []
    me = socket.gethostname()
    neighbors = []

    for i in asg.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])['AutoScalingGroups'][0]['Instances']:
        instances.append(i['InstanceId'])

    for p in ec2.describe_instances(InstanceIds=instances)['Reservations']:
        for q in p['Instances'][0]['Tags']:
            if q['Key'] == 'Name' and q['Value'] not in me:
                neighbors.append(q['Value'])

    return neighbors

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--asg-name', type=str, default='puppet-master-stage')

    args = parser.parse_args()

    for n in get_names(args.asg_name):
        print n
