#!/usr/bin/python

import re
import os
import sys
import gettext
import locale
import readline
import datetime

from default_settings import *
from utils import *

try:
	from settings import *
except ImportError:
	pass


#
# configuration variables
#
prj_name = 'myca'
myca_version = '1'
cadirs = {'CA':'ca', 'SRV':'server', 'CRL':'crl', 'CLN':'user', 'WRK':'workstation'}
cafiles = {'CRL':'ca-crl.crl', 'CRLT':'ca-crl.pem', 'IDX':'index.txt', 'CRT':'ca-crt.pem'}
openssl = 'openssl'
days = {'10y':'3652', '1y':'366' }
cfgfile_def = 'CA.cnf.def'
cfgfile = 'CA.cnf'
rdns = {'SRV':'/C=CZ/ST=%s/O=%s/OU=Servers/emailAddress=%s/CN=%%s' % (STATE, ORGANIZATION, ADMIN_EMAIL),
	'CLN':'/C=CZ/ST=%s/O=%s/OU=Employee/emailAddress=%%s/CN=%%s' % (STATE, ORGANIZATION),
	'WRK':'/C=CZ/ST=%s/O=%s/OU=Workstations/emailAddress=%s/CN=%%s' % (STATE, ORGANIZATION, ADMIN_EMAIL)}
revoke = '--revoke'
host_spec = ['host=', 'Domain name:']
dns_spec = ['dns=', 'Aliases (space separated):'];
mail_spec = ['email=', 'E-mail address:']
name_spec = ['name=', 'First and last name:']
login_spec = ['login=', 'Logon name:']

cfgfile_part = {'SRV':'server_ca', 'CLN':'client_ca', 'WRK':'workstation_ca'}
modes = ['SRV', 'CLN', 'WRK']
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
	if (not os.path.exists(os.path.join(cadirs[basename], fname + '.crt'))):
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
				revoke_certificate(fname)
				return(True)
	return(True)

#
# generate server certificate
#
def generate_certificate(fname, common_name, alt_names, RDN):
	filename = os.path.join(cadirs[basename], re.escape(fname))

	# check validity, if certificate exists and is still valid
	if (not check_certificate_validity(fname, common_name)):
		print _('Previous certificate for %s is still valid...') % fname
		print _('Revoke and create new certificate [%s/%s]') % (_('y'), _('N')) ,
		if (raw_input().lower() == _('y')):
			revoke_certificate(fname)
		else:
			return

	command = 'cp %s %s' % (cfgfile_def, cfgfile)
	os.system(command)

	if (alt_names is not None):
		replaceAll(cfgfile, "__REPLACE__", alt_names);

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
		command = '%s ca -config %s -revoke %s' % (openssl, cfgfile, re.escape(filename));
		print command
		os.system(command)
		command = '%s ca -config %s -gencrl -out %s' % (openssl, cfgfile, os.path.join(cadirs['CA'], cafiles['CRLT']))
		print command
		os.system(command)
		command = '%s crl -in %s -outform DER -out %s' % (openssl, os.path.join(cadirs['CA'], cafiles['CRLT']), os.path.join(cadirs['CA'], cafiles['CRL']))
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
		readedAliases = get_user_input(dns_spec)
		RDN = rdns[basename] % (name)
		aliases = readedAliases.split(' ')
		first = None
		dnss = ""
		for alias in aliases:
			ip = re.compile('\d{1,3}(\.\d{1,3}){3}')
			m = ip.match(alias)
			if first:
				dnss += ","
			else:
				first = 1
			if m:
				dnss += "IP:%s" % alias
			else:
				dnss += "DNS:%s" %alias
		if dnss.endswith('DNS:'):
			dnss = "email:copy"
		generate_certificate(name, name, dnss, RDN)
	print _('Done...')

def wrk():
	name = get_user_input(host_spec)
	if (revoke in sys.argv):
		revoke_certificate(name)
	else:
		RDN = rdns[basename] % (name)
		generate_certificate(name, name, None, RDN)
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
		generate_certificate(login, name, None, RDN)
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
