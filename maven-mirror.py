#!/usr/bin/env python3

import sys
import os
import socket
import threading
import socketserver
import mimetypes
import shutil
from urllib import request, error
from io import BytesIO
from http.server import SimpleHTTPRequestHandler, BaseHTTPRequestHandler, HTTPServer

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)-5s %(module)s - %(message)s')
log = logging.getLogger(__name__)
# logging.getLogger("paramiko").setLevel(logging.ERROR)

class SimpleHTTPProxy(BaseHTTPRequestHandler):
    cache_path = None
    mirrors = []

    @classmethod
    def set_cache_path(cls, cache_path):
        log.info("Caching from %s" % cache_path)
        cls.cache_path = cache_path

    @classmethod
    def set_mirrors(cls, mirrors):
        log.debug("Setting %d mirrors: %s" % ( len(mirrors), " ".join( mirrors ) ) )
        cls.mirrors = mirrors

    def do_HEAD(self):
        path = self.path[1:]
        if not os.path.isfile( path ):
            for mirror in SimpleHTTPProxy.mirrors:
                url = "%s%s" % ( mirror, path )
                log.debug("Checking: %s" % ( url ) )
                file = self.save_mirror_file( url, path )
                if file is not False: 
                    break

        if not os.path.isfile( path ):
            mimetype = mimetypes.guess_type(path)
            self.send_response(200)
            self.send_header('Content-type', mimetype[0])
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
        return

    def do_GET(self):
        # path is already normalized by the underlying engine, so things like "../" are already resolved
        path = self.path[1:]

        try:
            found = self.serve_local_file( path )
            if found:
                log.debug("%s found in local cache. Done." % path)
                return

            log.info("%s not found locally. Searching %d remote repositories" % ( path, len(SimpleHTTPProxy.mirrors) ) )
            for mirror in SimpleHTTPProxy.mirrors:
                url = "%s%s" % ( mirror, path )
                log.debug("Checking: %s" % ( url ) )
                file = self.serve_mirror_file( url )
                if file: break

            if file:
                log.info("%s downloaded. Storing in local cache." % path)
                self.save_local_file( path, file )
                return

            if not found:
                self.send_response(404)
                self.end_headers()
        except Exception as ex:
            log.error("Unhandled exception serving %s. Returning 500: %s" % ( path, ex ) )
            self.send_response(500)
            self.end_headers()

    def send_file( self, path, fh ):
        mimetype = mimetypes.guess_type(path)
        self.send_response(200)
        self.send_header('Content-type',mimetype[0])
        self.end_headers()
        shutil.copyfileobj(fh, self.wfile)
        self.wfile.flush()

    def serve_local_file( self, path ):
        full_path = os.path.join( SimpleHTTPProxy.cache_path, path )
        try:        
            if not os.path.isfile( full_path ): return False

            with open( full_path, 'rb' ) as f:
                self.send_file(path, f)
                return True
        except Exception as ex:
            log.error("Local file %s exists, but unable to open: %s" % ( full_path, ex ) )
            return False

    def save_local_file( self, path, bytes ):
        if ".xml" not in path and ".pom" not in path and ".jar" not in path:
            return False
        full_path = os.path.join( SimpleHTTPProxy.cache_path, path )
        try:
            # makedirs will fail if the directory already exists (fine, ignore)
            # or if it can't be made (will fail in the open below, so ignore)
            try:
                dir = os.path.dirname( full_path )
                os.makedirs( dir )
            except: pass

            with open( full_path, 'wb' ) as of:
                of.write( bytes )
        except Exception as ex:
            log.error("Unable to save local file %s: %s" % ( full_path, ex ) )
            return False

    def save_mirror_file(self, url, path):
        try:
            response = request.urlopen(url)
        except error.HTTPError as e:
            log.error("Not found on %s" % url)
            return False
        
        if response.status == 200:
            log.debug("Found on %s" % url)
            with BytesIO() as f:
                shutil.copyfileobj(response, f)
                return self.save_local_file(path, f.read())
        else:
            return False

    def serve_mirror_file(self, url):
        try:
            response = request.urlopen(url)
        except error.HTTPError as e:
            log.error("Not found on %s" % url)
            return False
        
        if response.status == 200:
            log.debug("Found on %s" % url)
            with BytesIO() as f:
                shutil.copyfileobj(response, f)
                f.seek(0)
                self.send_file(url, f)
                f.seek(0)
                return f.read()
        else:
            return False

    def log_request(self, code='-', size='-'):
        log.info('%s - - [%s] "%s" %s %s' % (self.address_string(), self.log_date_time_string(), self.requestline, str(code), str(size)))

    def log_error(self, format, *args):
        log.error("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format%args))

    def log_message(self, format, *args):
        log.error("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format%args))


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    pass

mirrors = [
    "https://repo.maven.apache.org/maven2/",
]

if len(sys.argv) != 2:
    print("Usage: %s /path/to/cache" % sys.argv[0])
    sys.exit(1)

cache_path = sys.argv[1]

SimpleHTTPProxy.set_mirrors( mirrors )
SimpleHTTPProxy.set_cache_path( cache_path )

port = 5956
if 'PORT' in os.environ:
  port = int(os.environ['PORT'])

with ThreadedHTTPServer(('0.0.0.0', port), SimpleHTTPProxy) as httpd:
    host, port = httpd.socket.getsockname()
    log.info(f'Listening on http://{host}:{port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("\nKeyboard interrupt received, exiting.")
        sys.exit(0)