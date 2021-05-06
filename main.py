#!/usr/bin/env python3
# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import yaml

from wazo_auth_client import Client as Auth
from wazo_websocketd_client import Client as Wws

from hue_api import HueApi


with open('config.yml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

username = config['username']
password = config['password']
wazo_host = config['wazo_host']
hue_host = config['hue_host']
lights_ids = config['lights']


class Wazo(object):

    def __init__(self, host, username, password):
        self.client_id = 'wazo-hue'
        self.token = None
        self.cb = None
        self.driver_name = None

        self.auth = Auth(host, username=username, password=password, verify_certificate=False)
        self.refresh_token = self._create_refresh_token()
        self.ws = Wws(host, token=self.token, verify_certificate=False)
        self.ws.on('auth_session_expire_soon', self._session_expired)

    def _create_token(self):
        self.token = self.auth.token.new('wazo_user', expiration=3600, refresh_token=self.refresh_token, client_id=self.client_id)['token']

    def _session_expired(self, data):
        self._create_token()
        self.ws.update_token(self.token)

    def _create_refresh_token(self):
        token_data = self.auth.token.new('wazo_user', access_type='offline', client_id=self.client_id)
        self.refresh_token = token_data['refresh_token']
        self._create_token()
        return self.refresh_token

    def set_driver(self, cb, driver_name):
        self.cb = cb
        self.driver_name = driver_name

    def _callback(self, data):
        dnd = data['data']['do_not_disturb']
        state = data['data']['state']
        status = data['data']['status']
        if dnd:
            state = 'dnd'
        self.cb.update_presence(state, status)


class Hue(object):

    def __init__(self, hue_ip, lights):
        self.cache_file = ".pickle"
        self.lights = lights
        self.hue = HueApi()
        self._init(hue_ip)
        self.hue.fetch_lights()

    def _init(self, hue_host):
        try:
            self.hue.load_existing(cache_file=self.cache_file)
        except:
            print('Error to load HUE config')
            self._first_time(hue_host)

    def _first_time(self, ip):
        input("Please press the link button on the bridge before to continue! Then Press enter...")
        self.hue.create_new_user(ip)
        self.hue.save_api_key(cache_file=self.cache_file)

    def list_lights(self):
        return self.hue.list_lights()

    def set_color(self, color, ids):
        self.hue.set_color(color, indices=ids)

    def update_presence(self, state, status):
        if state == 'available':
            self.set_color('green', self.lights)
        if state == 'dnd':
            self.set_color('red', self.lights)
        if state == 'away':
            self.set_color('yellow', self.lights)


wazo = Wazo(wazo_host, username, password)
hue = Hue(hue_host, lights_ids)
print(hue.list_lights())
wazo.set_driver(hue, "Hue Philips")
wazo.ws.on('chatd_presence_updated', wazo._callback)
wazo.ws.run()
