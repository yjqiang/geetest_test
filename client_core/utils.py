import time

import toml

from .user import User


def curr_time() -> int:
    return int(time.time())


def get_1st_user(path):
    with open(path, encoding='utf-8') as f:
        user = toml.load(f)['users'][0]
    return user
 
               
def get_dict_bili(path):
    with open(path, encoding='utf-8') as f:
        dict_bili = toml.load(f)
    return dict_bili
    

def new_user(dict_user, dict_bili):
    return User(dict_user, dict_bili)
