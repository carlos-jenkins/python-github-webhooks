#!/usr/bin/env bash
: {PM_BRANCH:="develop"}
cd /app/puppet-master
git pull origin $PM_BRANCH
cp -R /app/puppet-master/puppet/code /etc/puppetlabs
