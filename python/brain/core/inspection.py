# !usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2016-09-28 22:39:08
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-06 11:58:58

from __future__ import print_function, division, absolute_import


class Inspection:
    '''
    A temp alternate local class of Inspection

    Designed for Trac user authentication in the Flask web
    '''

    cols = keys = ['membername', 'modified']
    trac_url = None

    def __init__(self, session=None, username=None, auth=None):
        self.session = session
        self.message = ''
        self.status = -1
        self.set_ready()
        if self.ready:
            self.set_member(id=self.session['member_id'], update_session=False)
        if not self.ready:
            self.set_member(username=username, auth=auth)

    def set_ready(self):
        ''' sets the Flask session to ready post login '''
        if self.session is not None:
            if 'member_id' in self.session:
                try:
                    self.ready = int(self.session['member_id']) > 0
                except:
                    self.ready = False
            else:
                self.ready = False
        else:
            self.ready = False

    def set_member(self, id=None, username=None, auth=None, add=False, update_session=True):
        ''' sets the trac user member '''
        if id is None:
            id = 1 if (username, auth) == ('test', 'b3a32904f4d5977f0d41e97713b3c4c1') else 0
        elif id == 1:
            username, auth = ('test', 'b3a32904f4d5977f0d41e97713b3c4c1')
        if username and auth:
            self.member = {'id': int(id), 'username': username, 'auth': auth}
            fullname = "SDSS User" if id == 1 else "Unknown user"
            if self.member['id']:
                self.status = 1
                self.message = "Logged in as {0}. ".format(self.member['username'])
            else:
                self.status = 0
                self.message = "Failed login for {0}. ".format(username)
                self.message += "Please retry." if username == 'sdss' else "Username unrecognized."
        else:
            self.member = None
        if self.member and update_session:
            self.set_session_member(id=self.member['id'],
                                    username=self.member['username'],
                                    fullname=fullname, auth=self.member['auth'])

    def set_session_member(self, id=None, username=None, fullname=None, auth=None):
        ''' sets the trac user member into the Flask session '''
        if self.session is not None:
            if 'member_id' not in self.session or self.session['member_id'] != id:
                try:
                    self.session['member_id'] = int(id)
                    self.session['member_username'] = username if username else 'None'
                    self.session['member_fullname'] = fullname if fullname else 'None'
                    self.session['member_auth'] = auth if auth else 'None'
                    self.set_ready()
                except:
                    self.session['member_id'] = None
                    self.session['member_username'] = None
                    self.session['member_fullname'] = None
                    self.session['member_auth'] = None

    def set_member_from_session(self):
        ''' sets the trac user member from a Flask session '''
        if self.session is not None:
            member_id = self.session['member_id'] if 'member_id' in self.session else None
            member_username = self.session['member_username'] if 'member_username' in self.session else None
            member_auth = self.session['member_auth'] if 'member_auth' in self.session else None
            self.set_member(id=member_id, username=member_username, auth=member_auth, update_session=False)
        else:
            self.member = None

    def result(self):
        result = {'ready': self.ready, 'message': self.message, 'status': self.status}
        if self.session and 'member_fullname' in self.session:
            result.update({'membername': self.session['member_fullname']})
        return result
