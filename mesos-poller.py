#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/*
 * Copyright (C) 2017 DBC A/S (http://dbc.dk/)
 *
 * This is part of mesos-poller
 *
 * mesos-poller is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * mesos-poller is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

@author: mran-dbc-dk
"""
import re
import time
import json
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import gen

from argparse import ArgumentParser
from traceback import print_exc

http_client = AsyncHTTPClient()

class ServiceError(Exception):
    pass

class MesosHandler(tornado.web.RequestHandler):
    mesos = 'http://mesos-master-p01:8080/v2/apps/'

    def initialize(self, user, pswd):
        self.user = user
        self.pswd = pswd

    @gen.coroutine
    def get(self, url):
        params = {k: self.get_argument(k) for k in self.request.arguments}

        if 'app' not in params:
            raise ServiceError('Need app param')

        app = params['app']
        print("Requesting status for app:%s"%params['app'])

        part = None
        if 'part' in params:
            part = params['part']

        endpoints = yield self.get_endpoints_from_mesos(app, part)
        numOk = yield self.check_endpoint_status(endpoints)
        numEndpoints = len(endpoints)

        print("Client health request finished for app:%s"%params['app'])
        result = json.dumps({'status':'ERROR' if numOk<numEndpoints else 'OK', 'app': app, 'num-endpoints':numEndpoints, 'num-ok':numOk})
        self.write(result)
        self.finish()


    @gen.coroutine
    def check_endpoint_status(self, endpoints):
        numOk = 0
        for endpoint in endpoints:
            print("Calling status endpoint: %s"%endpoint)
            req = HTTPRequest(url=endpoint)
            response = yield http_client.fetch(req, raise_error=False)
            if response.error:
                print("Error: Got %d/%s from %s"%(response.code, response.reason, endpoint))
            else:
                numOk = numOk + 1
            res = response.body
            print("Response from %s : %s"%(endpoint,res))

        return numOk



    @gen.coroutine
    def get_endpoints_from_mesos(self, app, part):
        url = self.mesos + app
        print("Calling Mesos URL=%s"%url)

        req = HTTPRequest(url=url, auth_username=self.user, auth_password=self.pswd)
        mesos_resp = yield http_client.fetch(req)

        res = json.loads(mesos_resp.body.decode('utf-8'))
        endpoints = []

        if part is None:
            part = res['app']['healthChecks'][0]['path']

        if part[0:1] != "/":
            part = "/" + part

        portindex = res['app']['healthChecks'][0]['portIndex']
        tasks = res['app']['tasks']

        for task in tasks:
            host = task['host']
            port = task['ports'][portindex]
            endpoints.append( "http://%s:%d%s"%(host,port,part) )

        return endpoints

    def write_error(self, status_code, **kwargs):
        if 'message' in kwargs.keys():
            self.finish("<html><title>%(code)d: %(message)s</title>"
                        "<body>%(msg)s</body></html>" % {
                            "code": status_code,
                            "message": self._reason,
                            "msg": kwargs.get('message')
                        })
        else:
            self.finish("<html><title>%(code)d: %(message)s</title>"
                        "<body>%(code)d: %(message)s</body></html>" % {
                            "code": status_code,
                            "message": self._reason,
                        })


if __name__ == "__main__":
    p = ArgumentParser(description="Mesos poller")
    p.add_argument("-P", "--port", metavar="PORT", default=8888, dest="port", type=int,
                   help="Which port to listen to")
    p.add_argument("-d", "--doc-root", metavar="DIR", default="/tmp", dest="doc_root", type=str,
                   help="Where to serve index.html from")
    p.add_argument("-u", "--user", metavar="USER", required=True, dest="user", type=str,
                   help="Mesos user")
    p.add_argument("-p", "--password", metavar="PASSWORD", required=True, dest="password", type=str,
                   help="Password for Mesos user")
    a = p.parse_args()
    s = tornado.httpserver.HTTPServer(
            tornado.web.Application([
                    (r"/()", tornado.web.StaticFileHandler, {
                            "path": a.doc_root,
                            "default_filename": "index.html"
                            }),
                    (r"/(status)", MesosHandler, {'user': a.user, 'pswd': a.password} ),
                    ]))
    s.bind(a.port)
    s.start()
    line = "# Starting on port: %d #"%(a.port)
    bar = re.sub('.', '#', line)
    print(bar)
    print(line)
    print(bar)
    tornado.ioloop.IOLoop.current().start()
