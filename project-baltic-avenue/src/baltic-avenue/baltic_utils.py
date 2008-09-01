import re

from xml.sax import saxutils


def date_format_1(value):
    return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def date_format_2(value):
    return value.strftime('%a, %d %b %Y %H:%M:%S GMT')

def escape_xml(value):
    return saxutils.quoteattr("'" + value)[2:-1]

def string_to_sign_bytes(value):
    return ' '.join(['%02x' % ord(b) for b in value.encode('utf-8')])

def parse_url_path(url_path):
    """ returns bucket, key parsed from the path """

    m = re.match('^/([^/]+)/?$',url_path)
    if m:
        return (m.group(1),None)
    
    m = re.match('^/([^/]+)/(.+)$',url_path)
    if m:
        return (m.group(1),m.group(2))
    
    return (None,None)
           
    
    