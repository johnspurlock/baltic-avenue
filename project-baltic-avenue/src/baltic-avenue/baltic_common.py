from datetime import tzinfo, timedelta, datetime
from baltic_model import *

import base64
import urllib
import hmac
import sha
import logging
import re


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




class S3Operation():

    
    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.requestor = None


        
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

    

    def check_auth(self, bucket='', key='', query_args = {}):
        
        # check auth header present
        client_auth = self.request.headers.get('Authorization')
        if not client_auth:
            self.error2(400,'NoAuthHeader','Expecting an Authorization header')
            return False
        
        m = re.match('^AWS ([^:]+):([^:]+)$',client_auth)
        if not m:
            self.error2(400,'InvalidHeader','Authorization header is not in the correct format')
            return False
        
        
        client_aws_key = m.group(1)
        client_aws_secrethash = m.group(2)
        
        
        self.requestor = UserPrincipal.gql('WHERE aws_key = :1', client_aws_key).get()
        if not self.requestor:
            self.response.set_status(403)
            self.response.headers['Content-Type'] = 'application/xml'
            self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?><Error>')
            self.response.out.write( u'<Code>InvalidAccessKeyId</Code>')
            self.response.out.write( u'<Message>The AWS Access Key Id you provided does not exist in our records.</Message>')
            self.response.out.write( u'<RequestId>AC5AA2E4B863E975</RequestId>')
            self.response.out.write( u'<AWSAccessKeyId>%s</AWSAccessKeyId>' % client_aws_key)
            self.response.out.write( u'<HostId>1Yajca0Zb4GRxLTO0Ezhmh0S0H40qil2fpySjRvc86iWug++zn7g+5/jJJFJTmw0</HostId>')
            self.response.out.write( u'</Error>')
            return False
            
     
    

     
        method = self.request.method
        headers = self.request.headers
        
        server_canonical_string = self.canonical_string(method=method, headers=headers, bucket=bucket, key=key, query_args = query_args)
        
        server_auth = "AWS %s:%s" % (self.requestor.aws_key, self.encode(self.requestor.aws_secret, server_canonical_string))
        
        
        logging.debug('server canonical: ' + server_canonical_string)
        logging.debug('server computed: ' + server_auth)
        logging.debug('client computed: ' + client_auth)
        
        if server_auth != client_auth:
            self.response.set_status(403)
            self.response.headers['Content-Type'] = 'application/xml'
            self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>\n<Error>')
            self.response.out.write( u'<Code>SignatureDoesNotMatch</Code>')
            self.response.out.write( u'<Message>The request signature we calculated does not match the signature you provided. Check your key and signing method.</Message>')
            self.response.out.write( u'<RequestId>7112FE9E72C69D9D</RequestId>')
            self.response.out.write( u'<SignatureProvided>%s</SignatureProvided>' % client_aws_secrethash)
            self.response.out.write( u'<StringToSignBytes>44 45 4c 45 54 45 0a 0a 0a 0a 78 2d 61 6d 7a 2d 64 61 74 65 3a 53 75 6e 2c 20 33 31 20 41 75 67 20 3230 30 38 20 31 38 3a 34 33 3a 30 32 20 47 4d 54 0a 2f 78 78 78 78 61 73 66 61 73 6c 64 6b 66 6a 6c 6b 61 73 66 6a 6c 6b 61 73 6a 64 66 6b 6c 78 2f</StringToSignBytes>')
            self.response.out.write( u'<AWSAccessKeyId>%s</AWSAccessKeyId>' % self.requestor.aws_key)
            self.response.out.write( u'<HostId>dEEfIoqdj0kkSkoc81NuK4Q4BoYCZqunIL5y1bJ81zhx3dd0asGvCDZ0NrFMqoMU</HostId>')
            self.response.out.write( u'<StringToSign>%s</StringToSign>' % server_canonical_string)
            self.response.out.write( u'</Error>')
            return False
        
    
        
        return True




    def error_no_such_bucket(self, bucket):
        self.response.set_status(404)
        self.response.headers['Content-Type'] = 'application/xml'
        self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>\n<Error>')
        self.response.out.write( u'<Code>NoSuchBucket</Code>')
        self.response.out.write( u'<Message>The specified bucket does not exist</Message>')
        self.response.out.write( u'<RequestId>11CF4D91A1DD2B0F</RequestId>')
        self.response.out.write( u'<BucketName>%s</BucketName>' % bucket)
        self.response.out.write( u'<HostId>7s0XcbPPISRUBJpdfRIjmXoZNW/YSCtHBhlo6PJrbDndaK3iWMAermCtqcnBBgix</HostId>')
        self.response.out.write( u'</Error>')

    def error_access_denied(self):
        self.response.set_status(403)
        self.response.headers['Content-Type'] = 'application/xml'
        self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>\n<Error>')
        self.response.out.write( u'<Code>AccessDenied</Code>')
        self.response.out.write( u'<Message>Access Denied</Message>')
        self.response.out.write( u'<RequestId>FCCB5AC5BA2E4FCC</RequestId>')
        self.response.out.write( u'<HostId>FJNtoWJ33FRU1GNSAOhuiyGDTvnFDFrY4NKrz0yJna/gTCgksX+8ubCf1afmrdYN</HostId>')
        self.response.out.write( u'</Error>')
        

