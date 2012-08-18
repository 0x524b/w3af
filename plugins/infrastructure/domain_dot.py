'''
domain_dot.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseInfrastructurePlugin import baseInfrastructurePlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.controllers.w3afException import w3afException
from core.controllers.misc.levenshtein import relative_distance_lt


class domain_dot(baseInfrastructurePlugin):
    '''
    Send a specially crafted request with a dot after the domain (http://host.tld./) and analyze response.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseInfrastructurePlugin.__init__(self)
        
        # Internal variables
        self._already_tested = []

    def discover(self, fuzzable_request ):
        '''
        Sends the special request.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                                    (among other things) the URL to test.
        '''
        domain = fuzzable_request.getURL().getDomain()
        extension = fuzzable_request.getURL().getExtension()
        
        if (domain, extension) not in self._already_tested:
            
            # Do it only one time
            self._already_tested.append( (domain, extension) )
            
            # Generate the new URL
            domain += '.'
            dot_url = fuzzable_request.getURL()
            dot_url = dot_url.copy()
            dot_url.setDomain(domain)
            try:
                # GET the original response
                original_response = self._uri_opener.GET( fuzzable_request.getURL(), cache=False )
                # GET the response with the modified domain (with the trailing dot)
                response = self._uri_opener.GET( dot_url, cache=False )
            except KeyboardInterrupt,e:
                raise e
            except w3afException,w3:
                om.out.error( str(w3) )
            else:
                self._analyze_response( original_response, response )

    def _analyze_response(self, original_resp, resp):
        '''
        @parameter original_resp: The httpResponse object that holds the ORIGINAL response.
        @parameter resp: The httpResponse object that holds the content of the response to analyze.
        '''
        if relative_distance_lt(original_resp.getBody(), resp.getBody(), 0.7):
            i = info.info(resp)
            i.setPluginName(self.getName())
            i.setId([original_resp.id, resp.id])
            i.setName('Responses differ')
            msg = '[Manual verification required] The response body for a ' \
            'request with a trailing dot in the domain, and the response ' \
            'body without a trailing dot in the domain differ. This could ' \
            'indicate a misconfiguration in the virtual host settings. In ' \
            'some cases, this misconfiguration permits the attacker to read ' \
            'the source code of the web application.'
            i.setDesc(msg)
            
            om.out.information(msg)
            
            kb.kb.append(self, 'domain_dot', i)
                
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def set_options( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds misconfigurations in the virtual host settings by sending a specially crafted
        request with a trailing dot in the domain name. For example, if the input for this plugin is
        http://host.tld/ , the plugin will perform a request to http://host.tld./ .
        
        In some misconfigurations, the attacker is able to read the web application source code by
        requesting any of the files in the "dotted" domain like this:
            - http://host.tld/login.php
        '''