#!/usr/bin/env python
#
# Copyright (c) 2015 Aruba Networks, Inc.
# Copyright (c) 2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""ClearPass API client tool.  Calls a single API specified by METHOD and URL
and prints the result.

Usage:
  cpapi.php (-? | --help)
  cpapi.php [options] METHOD URL [PARAMS...]

Options:
  -? --help               Show this screen.
  -h --host HOSTNAME      Set the ClearPass server hostname.
  -k --insecure           Allow insecure SSL certificate checks.
  --access-token TOKEN    Use TOKEN as the OAuth2 Bearer access_token.
  --client-id CLIENT      OAuth2 client identifier.
  --client-secret SECRET  OAuth2 client secret.
  --username USERNAME     OAuth2 username, for grant_type password.
  --password PASSWORD     OAuth2 password, for grant_type password.
  -z --unauthorized       Skip OAuth2 authorization.  Only useful for /oauth.
  -v --verbose            Print HTTP request and response traffic.
  --debug                 Print connection traces.

PARAMS may be expressed as:
  * name=value     for JSON body parameters (POST, PATCH, PUT)
  * name==value    for query string parameters (GET)

Authorization requires ONE of the following:
  * --access-token (if you already performed OAuth2 authentication)
  * --client-id, --client-secret (for grant_type=client_credentials)
  * --client-id, --username, --password (for grant_type=password, public client)
  * --client-id, --client-secret, --username, --password (for grant_type=password)

Most options can be stored in environment variables; use _ in place of -.

Examples:
  # Get an access_token
  cpapi.py --host clearpass.example.com -z POST /oauth grant_type=client_credentials client_id=Client1 client_secret=ClientSecret

  # Create a guest account; show full request/response
  export host=clearpass.example.com
  export access_token=...
  cpapi.py -v POST /guest username=demo@example.com password=123456 role_id=2 visitor_name='Demo User'

  # Lookup a guest account by ID
  cpapi.py get /guest/3001

  # Modify a guest account
  cpapi.py patch /guest/3001 password=654321

"""
from clearpass import api
from docopt import docopt
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
import os
import re
import sys
import warnings

VERSION = 'cpapi.py 1.1'

class CommandLineInterface:
	def main(self):
		# Don't generate a warning message about --insecure
		warnings.simplefilter('ignore', InsecureRequestWarning)
		self.args = docopt(__doc__, version=VERSION)
		exit_status = 0
		try:
			client = api.Client(host=self.argStr('host'),
				insecure=self.argBool('insecure'),
				verbose=self.argBool('verbose'),
				debug=self.argBool('debug'),
				access_token=self.argStr('access_token'),
				client_id=self.argStr('client_id'),
				client_secret=self.argStr('client_secret'),
				username=self.argStr('username'),
				password=self.argStr('password'))
			query, body = self.parseParams(self.args['PARAMS'])
			result = client.invoke(self.validateMethod(self.args['METHOD']),
				self.args['URL'], query, body, not self.args['--unauthorized'])
			json.dump(result, sys.stdout, indent=4, sort_keys=True)
			print("\n")
		except api.ConfigurationException as e:
			sys.stderr.write("ERROR: Configuration error: %s\n" % str(e))
			exit_status = 3
		return exit_status

	def validateMethod(self, method):
		if method.upper() not in ('GET', 'POST', 'PATCH', 'PUT', 'DELETE'):
			raise api.ConfigurationException('Invalid HTTP method: ' + method)
		return method.upper()

	_matchParams = re.compile(r'^(?P<name>\w+)(?P<op>==|=)(?P<value>.*)$', re.DOTALL)

	def parseParams(self, params):
		query = {}
		body = {}
		bad_params = []
		for param in params:
			match = self._matchParams.match(param)
			if match is None:
				bad_params.append(param)
			elif match.group('op') == '==':
				query[match.group('name')] = match.group('value')
			else:
				body[match.group('name')] = match.group('value')
		if bad_params:
			raise api.ConfigurationException('Invalid parameter(s): ' + ', '.join(bad_params))
		return (query, body)

	def argBool(self, name):
		value = self.args.get('--' + name.replace('_', '-'), False)
		if not value:
			value = os.getenv(name) in ('1', 'true', 'on', 'yes')
		return value

	def argStr(self, name, default=''):
		value = self.args.get('--' + name.replace('_', '-'))
		if value is None:
			value = os.getenv(name, default)
		return value

if __name__ == '__main__':
	sys.exit(CommandLineInterface().main())
