

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
from baltic_model import *


class MainPage(webapp.RequestHandler):

   
   
    def find_principals(self, module_name):
        
        try:
            module = __import__(module_name)
            logging.info('module [%s] found, loading principals...' % module_name)
        except ImportError:
            logging.info('module [%s] not found, no principals loaded' % module_name)
            return []
        except:
            logging.info('error occurred while loading module [%s], no principals loaded' % module_name)
            return []
        return [module.__dict__[x] 
                for x in module.__dict__ 
                if module.__dict__[x].__class__ in (GroupPrincipal,UserPrincipal)]
        
   
    def update_principals(self):
        
        for p in self.find_principals('principals_public') + self.find_principals('principals_private'):
            q = db.GqlQuery("SELECT * FROM %s WHERE id = :1 LIMIT 1" %  p.__class__.__name__,p.id).get()
            if q:
                logging.info('update %s' % p.id)
                
                q.display_name = p.display_name
                if q.__class__ == UserPrincipal:
                    q.aws_key = p.aws_key
                    q.aws_secret = p.aws_secret
                    q.email = p.email
                if q.__class__ == GroupPrincipal:
                    q.uri = p.uri
                q.put()
            else:
                logging.info('creating %s' % p.id)
                p.put()
        
        
        

    def get(self):
        

            
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
    
        # TEMP
        if self.request.path == '/test':
            self.update_principals()
            
            return
        
        # GET service
        if self.request.path == '/':
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