#!/usr/bin/python

import os
import readline
import gettext
import locale
from utils import *

try:
	locale.setlocale(locale.LC_ALL, '')
	gettext.bindtextdomain(prj_name, "po")
	gettext.textdomain(prj_name)
	gettext.install(prj_name, "po", unicode=1)
except (IOError, locale.Error), e:
	print "(%s): WARNING **: %s" % (prj_name, e)
	__builtins__.__dict__["_"] = lambda x : x
__builtins__.__dict__["ngettext"] = gettext.ngettext

def getResponse(prompt, defaultValue):
	print "%s [%s]:" % (prompt, defaultValue) , ;
	value = raw_input();
	if (value == ""):
		return defaultValue;
	return value;
	


if (not os.path.isfile("settings.py")):
	state = getResponse(_("State"), "");
	province = getResponse(_("Province"), "");
	city = getResponse(_("City"), "");
	company = getResponse(_("Company name"), "");
	admin_email = getResponse(_("Admin email"), "");
	org_unit = getResponse(_("Organization Unit"), "%s CA" % (company));
	client_nscomment = getResponse(_("Client nsComment"), "%s Client Certificate" % (company));
	client_crl_url = getResponse(_("Client CRL URL"), "");
	server_nscomment = getResponse(_("Server nsComment"), "%s Server Certificate" % (company));
	server_crl_url = getResponse(_("Server CRL URL"), client_crl_url);
	ws_nscomment = getResponse(_("Workstation nsComment"), "%s Workstation Certificate" % (company));
	ws_crl_url = getResponse(_("Workstation CRL URL"), server_crl_url);
	ca_nscomment = getResponse(_("CA nsComment"), "%s CA Certificate" % (company));
	ca_crl_url = getResponse(_("CA CRL URL"), server_crl_url);
	
	command = 'cp %s %s' % ("CA.cnf.inst", "CA.cnf.def");
	os.system(command);

	replaceAll("CA.cnf.def", "__DEFAULT_COUNTRY__", state);
	replaceAll("CA.cnf.def", "__DEFAULT_PROVINCE__", province);
	replaceAll("CA.cnf.def", "__DEFAULT_CITY__", city);
	replaceAll("CA.cnf.def", "__DEFAULT_ORGANIZATION_NAME__", company);
	replaceAll("CA.cnf.def", "__DEFAULT_ORGANIZATION_UNIT__", org_unit);
	replaceAll("CA.cnf.def", "__DEFAULT_CLIENT_NSCOMMENT__", client_nscomment);
	replaceAll("CA.cnf.def", "__DEFAULT_CLIENT_CLR_URL__", client_crl_url);
	replaceAll("CA.cnf.def", "__DEFAULT_SERVER_NSCOMMENT__", server_nscomment);
	replaceAll("CA.cnf.def", "__DEFAULT_SERVER_CRL_URL__", server_crl_url);
	replaceAll("CA.cnf.def", "__DEFAULT_WORKSTATION_NSCOMMENT__", ws_nscomment);
	replaceAll("CA.cnf.def", "__DEFAULT_WORKSTATION_CRL_URL__", ws_crl_url);
	replaceAll("CA.cnf.def", "__DEFAULT_CA_NSCOMMENT__", ca_nscomment);
	replaceAll("CA.cnf.def", "__DEFAULT_CA_CRL_URL__", ca_crl_url);
	
	settings = open("settings.py", "w");
	settings.write("#!/usr/bin/python\n");
	settings.write("STATE=\"%s\"\n" % (state));
	settings.write("ORGANIZATION=\"%s\"\n" % (company));
	settings.write("ADMIN_EMAIL=\"%s\"\n" % (admin_email));
	settings.close();
