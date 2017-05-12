#!/usr/bin/env bash
: {PM_BRANCH:="master"}
cd /app/cenconf
git pull origin $PM_BRANCH
cp -R /app/cenconf /etc/puppetlabs/code/modules
