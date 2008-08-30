import re


def parse_url_path(url_path, query_string=None):
    """ returns bucket, key, query string """

    
    m = re.match('^/([^/]+)/?$',url_path)
    if m:
        return (m.group(1),None,query_string)
    
    
    
    m = re.match('^/([^/]+)/(.+)$',url_path)
    if m:
        return (m.group(1),m.group(2),query_string)
    
    return (None,None,None)
           
    
    