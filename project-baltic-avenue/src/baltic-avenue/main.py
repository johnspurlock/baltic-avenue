

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

from baltic_object_put import *
from baltic_object_delete import *
from baltic_object_head import *
from baltic_object_get import *

from baltic_utils import *
from baltic_model import *

from admin_page import *




class MainPage(webapp.RequestHandler):

    __ran_once = False
    
    def common(self):
        
        # run update-principals task once on the first request after a reload
        if not MainPage.__ran_once and not is_development_server_request(self.request):
            MainPage.__ran_once = True
            logging.info('RUN ONCE')
            AdminPage(self.request,self.response).update_principals()
            
        # common to all responses
        self.response.charset = 'utf8'
        del self.response.headers['Cache-Control']
        del self.response.headers['Content-Type']
        
   
    def get(self):
                        
        self.common()
    
        # ADMIN
        admin_page = 'admin'
        if self.request.path == '/%s' % admin_page or self.request.path.startswith('/%s/'% admin_page):
            AdminPage(self.request,self.response).go()
            return
        
        # GET service
        if self.request.path == '/':
            GetServiceOperation(self.request,self.response).go_common() 
            return
        
        
        # GET bucket
        m = parse_url_path(self.request.path)
        if m[0] and not m[1]:
            GetBucketOperation(self.request,self.response).go_common(m[0]) 
            return

        # GET object
        m = parse_url_path(self.request.path)
        if m[0] and m[1]:
            GetObjectOperation(self.request,self.response).go_common(m[0],m[1]) 
            return


        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)


    
    def put(self):
        
        self.common()
        
        # PUT bucket
        m = parse_url_path(self.request.path)
        if m[0] and not m[1]:
            PutBucketOperation(self.request,self.response).go_common(m[0]) 
            return
            
        # PUT object
        m = parse_url_path(self.request.path)
        if m[0] and m[1]:
            PutObjectOperation(self.request,self.response).go_common(m[0],m[1]) 
            return
 
            
        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)
      
    def delete(self):
        
        self.common()
        
        # DELETE bucket
        m = parse_url_path(self.request.path)
        if m[0] and not m[1]:
            DeleteBucketOperation(self.request,self.response).go_common(m[0]) 
            return
        
        # DELETE object
        m = parse_url_path(self.request.path)
        if m[0] and m[1]:
            DeleteObjectOperation(self.request,self.response).go_common(m[0],m[1]) 
            return
            
        # unsupported
        self.response.set_status(500)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request.path)
        
    def head(self):
        
        self.common()
        
        # HEAD bucket
        m = parse_url_path(self.request.path)
        if m[0] and not m[1]:
            HeadBucketOperation(self.request,self.response).go_common(m[0]) 
            return
        
        # HEAD object
        m = parse_url_path(self.request.path)
        if m[0] and m[1]:
            HeadObjectOperation(self.request,self.response).go_common(m[0],m[1]) 
            return
    

        
def main():
    
    application = webapp.WSGIApplication(
                                       [('.*', MainPage)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()