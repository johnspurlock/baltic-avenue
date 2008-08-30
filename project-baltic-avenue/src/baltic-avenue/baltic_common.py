from datetime import tzinfo, timedelta, datetime
import logging

from google.appengine.ext import db

import base64
import urllib
import hmac
import sha


import privateinfo

ZERO = timedelta(0)
HOUR = timedelta(hours=1)




# A UTC class.

class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = UTC()

class Bucket(db.Model):
    name = db.StringProperty(required=True)
    creation_date = db.DateTimeProperty(required=True)

class Principal(db.Model):
    id = db.StringProperty(required=True)
    display_name = db.StringProperty(required=True)





class S3Operation():

    
    def __init__(self, request, response):
        self.request = request
        self.response = response


    def error2(self, status_int, code, message):
    
    
        self.response.set_status(status_int)
       
       
        self.response.headers['Content-Type'] = 'application/xml'
        
        
        self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>')
        self.response.out.write( u'<Error>')
        self.response.out.write( u'  <Code>%s</Code>' % code)
        self.response.out.write( u'  <Message>%s</Message>' % message)
        #self.response.out.write( u'  <Resource>/mybucket/myfoto.jpg</Resource>' % message)
        self.response.out.write( u'  <RequestId>4442587FB7D0A2F9</RequestId>')
        self.response.out.write( u'</Error>')
    

        
    # generates the aws canonical string for the given parameters
    def canonical_string(self, method, bucket="", key="", query_args={}, headers={}, expires=None):
        
        
        AMAZON_HEADER_PREFIX = 'x-amz-'
        
        interesting_headers = {}
        for header_key in headers:
            lk = header_key.lower()
            if lk in ['content-md5', 'content-type', 'date'] or lk.startswith(AMAZON_HEADER_PREFIX):
                interesting_headers[lk] = headers[header_key].strip()
    
        # workaround for dev_appserver defaulting content-type to application/x-www-form-urlencoded
        # assume that form-urlencoded means none provided
        if interesting_headers.has_key('content-type') and interesting_headers['content-type'] == 'application/x-www-form-urlencoded':
            del interesting_headers['content-type']
            
        
    
        # these keys get empty strings if they don't exist
        if not interesting_headers.has_key('content-type'):
            interesting_headers['content-type'] = ''
        if not interesting_headers.has_key('content-md5'):
            interesting_headers['content-md5'] = ''
    
        # just in case someone used this.  it's not necessary in this lib.
        if interesting_headers.has_key('x-amz-date'):
            interesting_headers['date'] = ''
    
        # if you're using expires for query string auth, then it trumps date
        # (and x-amz-date)
        if expires:
            interesting_headers['date'] = str(expires)
    
        sorted_header_keys = interesting_headers.keys()
        sorted_header_keys.sort()
    
        buf = "%s\n" % method
        for header_key in sorted_header_keys:
            if header_key.startswith(AMAZON_HEADER_PREFIX):
                buf += "%s:%s\n" % (header_key, interesting_headers[header_key])
            else:
                buf += "%s\n" % interesting_headers[header_key]
    
    
        # always append /
        buf += '/'
    
        # append the bucket if it exists
        if bucket != '':
            buf += "%s" % bucket


        # add the key.  even if it doesn't exist, add the slash
        #buf += "/%s" % urllib.quote_plus(key)
    
        # handle special query string arguments
    
        if query_args.has_key("acl"):
            buf += '/'  # only add a trailing slash for acl???
            buf += "?acl"
        elif query_args.has_key("torrent"):
            buf += "?torrent"
        elif query_args.has_key("logging"):
            buf += "?logging"
        elif query_args.has_key("location"):
            buf += "?location"
    
        return buf

    
    


    # computes the base64'ed hmac-sha hash of the canonical string and the secret
    # access key, optionally urlencoding the result
    def encode(self, aws_secret_access_key, str, urlencode=False):
        b64_hmac = base64.encodestring(hmac.new(aws_secret_access_key, str, sha).digest()).strip()
        if urlencode:
            return urllib.quote_plus(b64_hmac)
        else:
            return b64_hmac



    def get_private_info(self):
        private_yaml_file = open("private.yaml", "rb")
        
        return privateinfo.LoadSinglePrivateInfo(private_yaml_file)


    def check_auth(self, bucket='', key='', query_args = {}):
        
        # check auth header present
        auth = self.request.headers.get('Authorization')
        if not auth:
            self.error2(400,'NoAuthHeader','Expecting an Authorization header')
            return False
        
        
        
        # check auth header valid
        private_info = self.get_private_info()
        
        aws_key = private_info.aws_key
        aws_secret = private_info.aws_secret
        
     
     
     
        method = self.request.method
        
 
        headers = self.request.headers
        
        server_canonical_string = self.canonical_string(method=method, headers=headers, bucket=bucket, key=key, query_args = query_args)
        
        server_auth = "AWS %s:%s" % (aws_key, self.encode(aws_secret, server_canonical_string))
        
        client_auth = self.request.headers['Authorization']
        
        logging.debug('server canonical: ' + server_canonical_string)
        logging.debug('server computed: ' + server_auth)
        logging.debug('client computed: ' + client_auth)
        
        if server_auth != client_auth:
            self.error2(400, 'InvalidAuthHeader', 'Authorization header does not match')
            return False
        
        return True




