======================
Python GitHub Webhooks
======================

Simple Python WSGI application to handle GitHub webhooks.


Install
=======

::
    git clone git@github.com:carlos-jenkins/python-github-webhooks.git
    cd python-github-webhooks


Dependencies
============

::

   sudo pip install -r requirements.txt


Setup
=====

You can configure what the application does by changing ``config.json``:

::

    {
        "github_ips_only": false,
        "enforce_secret": "",
        "return_scripts_info": true
    }

:github_ips_only: Restrict application to be called only by GitHub IPs. IPs
 whitelist is obtained from
 `GitHub Meta <https://developer.github.com/v3/meta/>`_
 (`endpoint <https://api.github.com/meta>`_).
:enforce_secret: Enforce body signature with HTTP header ``X-Hub-Signature``.
 See ``secret`` at
 `GitHub WebHooks Documentation <https://developer.github.com/v3/repos/hooks/>`_.
:return_scripts_info: Return a JSON with the ``stdout``, ``stderr`` and exit
 code for each executed hook using the hook name as key.


Adding Hooks
============

This application will execute scripts in the hooks directory using the
following order:

::

    hooks/{event}-{name}-{branch}
    hooks/{event}-{name}
    hooks/{event}
    hooks/all

The application will pass to the hooks the JSON received as first argument.
Hooks can be written in any scripting language as long as the file is executable
and has a shebang. A simple example in Python could be:

::

    #!/usr/bin/env python
    # Python Example for Python GitHub Webhooks

    import os
    import sys
    import json
    from tempfile import mkstemp

    payload = json.loads(sys.argv[1])
    _, tmpfile = mkstemp()

    ### Do something with the payload
    if payload['repository']['name'] == 'my-repo-name':
        f = open(tmpfile, 'w')
        f.write(json.dumps(payload))
        f.close()


Test
====

The following will launch the Flask web server in debug mode at port ``5000``.

::

    python webhooks.py


Deploy
======

To deploy in Apache, just add a ``WSGIScriptAlias`` directive to your
VirtualHost file:

::

    <VirtualHost *:80>
        ServerAdmin you@my.site.com
        ServerName  my.site.com
        DocumentRoot /var/www/site.com/my/htdocs/

        # Handle Github webhook
        <Directory "/var/www/site.com/my/python-github-webhooks">
            Order deny,allow
            Allow from all
        </Directory>
        WSGIScriptAlias /webhooks /var/www/site.com/my/python-github-webhooks/webhooks.py

    </VirtualHost>


License
=======

::

   Copyright (C) 2014 Carlos Jenkins <carlos@jenkins.co.cr>

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing,
   software distributed under the License is distributed on an
   "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
   KIND, either express or implied.  See the License for the
   specific language governing permissions and limitations
   under the License.


Credits
=======

This project is just the reinterpretation and merge of two approaches:

- `github-webhook-wrapper <https://github.com/datafolklabs/github-webhook-wrapper>`_.
- `flask-github-webhook <https://github.com/razius/flask-github-webhook>`_.

Thanks.