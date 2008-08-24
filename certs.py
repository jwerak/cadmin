#!/usr/bin/python

import re
import os
import sys
import gettext
import locale
import readline
import datetime

#
# configuration variables
#
prj_name = 'myca'
myca_version = '1'
cadirs = {'CA':'ca', 'SRV':'server', 'CRL':'crl', 'CLN':'user' }
cafiles = {'CRL':'ca-crl.crl', 'IDX':'index.txt', 'CRT':'ca-crt.pem'}
openssl = 'openssl'
days = {'10y':'3652', '1y':'366' }
cfgfile = 'CA.cnf'
rdns = {'SRV':'/C=CZ/ST=Czech Republic/O=Medoro s.r.o./OU=Servers/emailAddress=barton@medoro.org/CN=%s',
	'CLN':'/C=CZ/ST=Czech Republic/O=Medoro s.r.o/OU=Employee/emailAddress=%s/CN=%s'}
revoke = '--revoke'
host_spec = ['host=', 'Domain name:']
mail_spec = ['email=', 'E-mail address:']
name_spec = ['name=', 'First and last name:']
login_spec = ['login=', 'Logon name:']

cfgfile_part = {'SRV':'server_ca', 'CLN':'client_ca'}
modes = ['SRV', 'CLN']
basename = ''

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
def get_user_input(fmt):
	for arg in sys.argv:
		if (arg.startswith(fmt[0])):
			return(arg[fmt[0].__len__() : ])
	print _(fmt[1]) ,
	return(raw_input())


#
# check if certificate for hostname exists and if is valid
#
def check_certificate_validity(fname, common_name):
	print common_name
	if (not os.path.exists(os.path.join(cadirs[basename], fname) + '.crt')):
		return(True)
	# V|R valid x revoked valid_to revoked_whe serial ??? RDN
	RDN = re.compile('(R|V)\t(\d{12}Z)\t(\d{12}Z|)\t([0-9A-Fa-f]{2})\t(\w+)\t(.*)')
	CN = re.compile('.*CN=(.*)/.*')
	# read index file and test for common name 
	index = open(cafiles['IDX'])
	index.readline()
	for line in index.readlines():
		# parse line
		rdn = RDN.match(line)
		# get CN
		cn = CN.match(rdn.group(6)).group(1)
		if (cn == common_name and rdn.group(1) == 'V'):
			# parse validity timestamp
			tmp = rdn.group(2)
			validity = datetime.date(2000 + int(tmp[0:2]), int(tmp[2:4]), int(tmp[4:6]))
			# certificate regeneration period
			period = datetime.date.today() + datetime.timedelta(31)
			if (period <= validity):
				days = validity - datetime.date.today()
				print '  ', _('Certificate valid to %s, valid for next %s days') % (validity, days.days)
				return(False)
			else:
				print _('Revoking old certificate for %s') % common_name 
				revoke_certificate(common_name)
				return(True)
	return(True)

#
# generate server certificate
#
def generate_certificate(fname, common_name, RDN):
	filename = os.path.join(cadirs[basename], fname)

	# check validity, if certificate exists and is still valid
	if (not check_certificate_validity(fname, common_name)):
		print _('Previous certificate for %s is still valid...') % fname
		print _('Revoke and create new certificate [%s/%s]') % (_('y'), _('N')) ,
		if (raw_input().lower() == _('y')):
			revoke_certificate(fname)
		else:
			return

	# create certificate request
	command = '%s req -config %s -verbose -new -nodes -subj "%s" -keyout %s.key -out %s.csr' % (openssl, cfgfile, RDN, filename, filename)
	print command
	os.system(command)
	# create and sign certificate
	command = '%s ca -config %s -name %s -in %s.csr -out %s.crt' % (openssl, cfgfile, cfgfile_part[basename], filename, filename)
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
def revoke_certificate(name):
	filename = os.path.join(cadirs[basename], name) + '.crt';
	if (os.path.isfile(filename)):
		command = '%s ca -config %s -revoke %s' % (openssl, cfgfile, filename);
		print command
		os.system(command)
		command = '%s ca -config %s -gencrl -out %s' % (openssl, cfgfile, os.path.join(cadirs['CA'], cafiles['CRL']))
		print command
		os.system(command)
	else:
		print _("Certificate %s was not found...") % filename

#
# get base program name
#
def get_base_name():
	prog_name = sys.argv[0]
	prog_name = prog_name[prog_name.rfind(os.sep) + 1 : prog_name.rfind('.')]
	return prog_name.upper()

#
# server mode
#
def srv():
	name = get_user_input(host_spec)
	if (revoke in sys.argv):
		revoke_certificate(name)
	else:
		RDN = rdns[basename] % (name)
		generate_certificate(name, name, RDN)
	print _('Done...')

#
# export user certificate
#
def export_cert(name):
	filename = os.path.join(cadirs[basename], name)
	command = '%s pkcs12 -export -inkey %s.key -in %s.crt -out %s.pfx -certfile %s' % (openssl, filename, filename, filename, os.path.join(cadirs['CA'], cafiles['CRT']))
	print command
	os.system(command)	

#
# client mode
#
def cln():
	login = get_user_input(login_spec)
	if (revoke in sys.argv):
		revoke_certificate(login)
	else:
		name = get_user_input(name_spec)
		mail = get_user_input(mail_spec)
		RDN = rdns[basename] % (mail, name)
		generate_certificate(login, name, RDN)
		export_cert(login)
	print _('Done...')

"""
Print application name and version
"""
print _("MyCA version"), myca_version;
basename = get_base_name()
if (basename in modes):
	print _('Running program in %s mode') % _(basename)
	locals()[basename.lower()]()
else:
	print _('Unknown program mode: %s') % basename
