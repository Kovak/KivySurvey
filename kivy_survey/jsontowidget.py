from __future__ import unicode_literals, print_function
from kivy.factory import Factory


def widget_from_json(json_dict):
	#Conversion step as python2 kivy does not accept Property names in unicode
	args = json_dict['args']
	new_dict = {}
	for each in args:
		new_dict[str(each)] = args[each]
	return getattr(Factory, json_dict['type'])(**new_dict)
