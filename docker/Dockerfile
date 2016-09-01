FROM orca.quixey.com/python27

MAINTAINER "Chris Hoffman" <chris@quixey.com>

RUN groupadd -g 999 puppet && \
    useradd -u 999 -g 999 -m -d /home/puppet -s /bin/bash puppet

RUN apt-get install -qy --no-install-recommends git ssh

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt && \
    mkdir /app/puppet-master && \
    chown -R puppet:puppet /app

RUN mkdir -p /etc/puppetlabs/code && \
    chown puppet:puppet /etc/puppetlabs/code

COPY docker/.ssh /home/puppet/.ssh
RUN  echo "    IdentityFile ~/.ssh/id_rsa_github" >> /etc/ssh/ssh_config && \
     ssh-keyscan github.com >> /home/puppet/.ssh/known_hosts && \
     chown -R puppet:puppet /home/puppet/.ssh &&\
     chmod 0600 /home/puppet/.ssh/*


USER puppet

RUN git clone git@github.com:quixey/puppet-master.git puppet-master && \
    cp -R /app/puppet-master/puppet/code /etc/puppetlabs


VOLUME /etc/puppetlabs/code

EXPOSE 5000
CMD ["python", "/app/webhooks.py", "hooks/push"]
