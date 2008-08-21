#!/usr/bin/python

import re
import os
import sys
import gettext
import locale
import readline

#
# configuration variables
#
prj_name = 'myca'
myca_version = '1'
cadirs = {'CA':'ca', 'SRV':'server', 'CRL':'crl' }
cafiles = {'CRL':'ca-crl.crl'}
openssl = 'openssl'
days = {'10y':'3652', '1y':'366' }
cfgfile = 'CA.cnf'
RDN = '/C=CZ/ST=Czech Republic/O=Medoro s.r.o/OU=Servers/emailAddress=barton@medoro.org/CN'
revoke = '--revoke'

#
# i18n support
#
try:
	locale.setlocale(locale.LC_ALL, '')
	gettext.bindtextdomain(prj_name, "po")
	gettext.textdomain(prj_name)
	gettext.install(prj_name, "po", unicode=1)
except (IOError, locale.Error), e:
	print "(%s): WARNING **: %s" % (prj_name, e)
	__builtins__.__dict__["_"] = lambda x : x
__builtins__.__dict__["ngettext"] = gettext.ngettext


#
# get hostname
#
def get_hostname():
	hostname_re = re.compile('(\w*\.){2}\w*')
	for hostname in sys.argv:
		if (hostname_re.match(hostname)):
			print _("Found hostname %s...") % hostname
			return(hostname)
	print _("Server hostname:") ,
	return(raw_input())

#
# generate server certificate
#
def generate_server_certificate():
	hostname = get_hostname();
	filename = os.path.join(cadirs['SRV'], hostname)

	if (os.path.isfile(filename + '.crt')):
		print _('Previous certificate for %s found...') % hostname
		print _('Revoke and create new certificate [%s/%s]') % (_('y'), _('N')) ,
		return

	# create certificate request
	command = '%s req -config %s -new -nodes -subj "%s=%s" -keyout %s.key -out %s.csr -days %s -verbose' % (openssl, cfgfile, RDN, hostname, filename, filename, days['1y'])
	print command
	os.system(command)
	# create and sign certificate
	command = '%s ca -config %s -name server_ca -in %s.csr -out %s.crt' % (openssl, cfgfile, filename, filename)
	print command
	os.system(command)
	# remove certificate request
	try:
		os.remove(filename + '.csr')
	except (OSError):
		pass


#
# revoke server certificate
#
def revoke_server_certificate():
	hostname = get_hostname()
	filename = os.path.join(cadirs['SRV'], hostname) + '.crt';
	if (os.path.isfile(filename)):
		command = '%s ca -config %s -revoke %s' % (openssl, cfgfile, filename);
		print command
		os.system(command)
		command = '%s ca -config %s -gencrl -out %s' % (openssl, cfgfile, os.path.join(cadirs['CA'], cafiles['CRL']))
		print command
		os.system(command)
	else:
		print _("Server certificate %s was not found...") % filename

"""
Print application name and version
"""
print _("MyCA version"), myca_version;
if (revoke in sys.argv):
	revoke_server_certificate()
else:
	generate_server_certificate()
