import re

from xml.sax import saxutils


def http_date(value):
    return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def escape_xml(value):
    return saxutils.quoteattr("'" + value)[2:-1]

def string_to_sign_bytes(value):
    return ' '.join(['%02x' % ord(b) for b in value.encode('utf-8')])

def parse_url_path(url_path, query_string=None):
    """ returns bucket, key, query string """

    
    m = re.match('^/([^/]+)/?$',url_path)
    if m:
        return (m.group(1),None,query_string)
    
    
    
    m = re.match('^/([^/]+)/(.+)$',url_path)
    if m:
        return (m.group(1),m.group(2),query_string)
    
    return (None,None,None)
           
    
    