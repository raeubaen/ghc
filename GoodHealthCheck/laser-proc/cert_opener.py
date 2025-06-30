import os, sys, urllib.request, urllib.error, urllib.parse, http.client, json
import array

HTTPS = http.client.HTTPSConnection


class X509CertAuth(HTTPS):
    ssl_key_file = None
    ssl_cert_file = None

    def __init__(self, host, *args, **kwargs):
        HTTPS.__init__(self, host, key_file = X509CertAuth.ssl_key_file,
                       cert_file = X509CertAuth.ssl_cert_file, **kwargs)

        
class X509CertOpen(urllib.request.AbstractHTTPHandler):
    def default_open(self, req):
        return self.do_open(X509CertAuth, req)
