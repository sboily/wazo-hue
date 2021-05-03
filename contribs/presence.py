#!/usr/bin/env python3

import pprint

from wazo_auth_client import Client as Auth
from wazo_chatd_client import Client as Chatd


username = ""
password = ""
host = "localhost"


def get_token():
    auth = Auth(host, username=username, password=password, verify_certificate=False)
    token_data = auth.token.new('wazo_user', expiration=3600)
    return token_data['token'], token_data['metadata']['uuid']

token, user_uuid = get_token()
c = Chatd(host, token=token, verify_certificate=False)

# List presence
presences = c.user_presences.list()

# Set presence to away
c.user_presences.update({"uuid": user_uuid, "state": "away"})

pprint.pprint(presences)
