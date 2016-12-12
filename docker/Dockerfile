FROM orca.quixey.com/python27

MAINTAINER "Chris Hoffman" <chris@quixey.com>

RUN groupadd -g 999 puppet && \
    useradd -u 999 -g 999 -m -d /home/puppet -s /bin/bash puppet

RUN apt-get install -qy --no-install-recommends git ssh

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt && \
    mkdir /app/cenconf && \
    mkdir /app/puppet-master && \
    chown -R puppet:puppet /app

RUN mkdir -p /etc/puppetlabs/code /etc/puppetlabs/r10k && \
    chown puppet:puppet /etc/puppetlabs/code /etc/puppetlabs/r10k

RUN mkdir -p /var/log/python-github-webhooks && \
    chown puppet:puppet /var/log/python-github-webhooks

COPY docker/.ssh /home/puppet/.ssh
RUN  echo "    IdentityFile ~/.ssh/id_rsa_github" >> /etc/ssh/ssh_config && \
     ssh-keyscan github.com >> /home/puppet/.ssh/known_hosts && \
     chown -R puppet:puppet /home/puppet/.ssh &&\
     chmod 0600 /home/puppet/.ssh/*

RUN echo "*/1 * * * *    	puppet  /app/hooks/push" >> /etc/crontab

USER puppet

RUN git clone git@github.com:quixey/puppet-master.git puppet-master && \
    cp -R /app/puppet-master/puppet/code /etc/puppetlabs && \
    cp -R /app/puppet-master/puppet/r10k /etc/puppetlabs && \
    git clone git@github.com:quixey/cenconf.git cenconf && \
    cp -R /app/cenconf /etc/puppetlabs/code/modules

# Install hiera data
RUN git clone git@github.com:quixey/puppet-hieradata.git /etc/puppetlabs/code/hieradata

# Run r10k once to get latest updates
RUN /opt/puppetlabs/puppet/bin/r10k deploy --puppetfile --detail

VOLUME /etc/puppetlabs/code

EXPOSE 5000
CMD ["python", "/app/webhooks.py"]
