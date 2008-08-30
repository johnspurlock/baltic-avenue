

import wsgiref.handlers
import logging
import os

import re

from google.appengine.ext import webapp

from baltic_service_get import *

from baltic_bucket_get import *
from baltic_bucket_head import *
from baltic_bucket_put import *
from baltic_bucket_delete import *

from baltic_utils import *

class MainPage(webapp.RequestHandler):

    

    def get(self):
        
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
    
    
        # GET service
        if (self.request.path == '/'):
            GetServiceOperation(self.request,self.response).go() 
            return
        
        
        # GET bucket
        m = parse_url_path(self.request.path,self.request.query_string)
        if m[0] and not m[1]:
            GetBucketOperation(self.request,self.response).go(m[0],m[2]) 
            return




        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)


    
    def put(self):
        
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
        
        # PUT bucket
        m = parse_url_path(self.request.path,self.request.query_string)
        if m[0] and not m[1]:
            PutBucketOperation(self.request,self.response).go(m[0]) 
            return
            
        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)
      
    def delete(self):
        
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
        
        # DELETE bucket
        m = parse_url_path(self.request.path,self.request.query_string)
        if m[0] and not m[1]:
            DeleteBucketOperation(self.request,self.response).go(m[0]) 
            return
            
        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)
        
    def head(self):
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
        
        # HEAD bucket
        m = parse_url_path(self.request.path,self.request.query_string)
        if m[0] and not m[1]:
            HeadBucketOperation(self.request,self.response).go(m[0]) 
            return
        
def main():
    
    application = webapp.WSGIApplication(
                                       [('.*', MainPage)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()