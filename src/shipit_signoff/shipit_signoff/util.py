# -*- coding: utf-8 -*-
def is_key_present_in_list_of_dicts(key, list_of_dicts):
    return any(key in dict_ for dict_ in list_of_dicts)
