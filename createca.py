#!/usr/bin/python

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
cadirs = {'CA':'ca', '_CAN':'ca/newcerts', 'SRV':'server', '_SRVN':'server/newcerts', 'WRK':'workstation', 'USR':'user', '_USRN':'user/newcerts', 'CRL':'crl'}
cafiles = { 'KEY':'ca-key.pem', 'REQ':'ca-req.pem', 'CRT':'ca-crt.pem', 'IDX':'index.txt', 'IDXA':'index.txt.attr', 'IDXAO':'index.txt.attr.old', 'IDXO':'index.txt.old', 'SRL':'serial', 'SRLO':'serial.old'}
openssl = 'openssl'
days = {'10y':'3652', '1y':'366'}
cfgfile = 'CA.cnf'

#
# command line parameters
#
remove = '--clean'
help = ['-h', '--help']

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
# create directory structure for CA
#
def create_dir_structure():
	for dir in cadirs.values():
		if ('/' not in dir):
			print _("Creating directory %s...") % dir
			try:
				os.mkdir(dir);
			except OSError:
				pass
	for dir in cadirs.values():
		if ('/' in dir):
			print _("Creating directory %s...") % dir
			try:
				os.mkdir(dir);
			except OSError:
				pass
	
	open(cafiles['IDX'], 'w').close()
	serial = open(cafiles['SRL'], 'w')
	serial.write('01\n')
	serial.close()

#
# remove content of directory
#
def remove_dir_content(dir):
	print _("Removing directory %s...") % dir
	content = []
	try:
		content = os.listdir(dir)
		for fod in content:
			path = os.path.join(dir, fod);
			if (os.path.isdir(path)):
				remove_dir_content(path);
			else:
				print "  ", _("Removing file %s...") % path
				try:
					os.remove(path);
				except OSError:
					print "  ", _("Error removing file %s...") % path;
		os.rmdir(dir);
	except OSError:
		pass

#
# remove previous version of CA
#
def remove_previous_ca(retval):
	if (_("N") == retval.upper()):
		print _("Leaving previous version of CA untouched...");
		sys.exit(1);
	if (_("y") == retval.lower()):
		print _("Removing previous version of CA...");
		for dir in cadirs.values():
			if ('/' not in dir):
				remove_dir_content(dir);
	content = []
	try:
		content = os.listdir('.');
		for fod in content:
			if (os.path.isfile(fod)):
				if (fod in cafiles.values()):
					print _("Removing file %s...") % fod
					os.remove(fod)
	except OSError:
		print "OSError"

#
# check for existing files (previous CA)
#
def check_prev_ca():
	error = 0;
	for dir in cadirs.values():
		if (os.path.isdir(dir)): error = 1
	if (error == 1):
		print _("FAIL: Previous version of CA exists...")
		print _("Overvrite previous version of CA [%s/%s]") % (_("y"), _("N")) ,
		remove_previous_ca(raw_input());
	else:
		print _("OK: No previous version of CA exists...") ;

#
# create new CA
#
def create_new_ca():
	create_dir_structure();
	print _("Creating CA certificate...");
	request = os.path.join(cadirs['CA'], cafiles['REQ'])
	key = os.path.join(cadirs['CA'], cafiles['KEY'])
	crt = os.path.join(cadirs['CA'], cafiles['CRT'])
	command = "%s req -config %s -new -keyout %s -out %s" % (openssl, cfgfile, key, request)
	print command
	os.system(command)
	command = "%s ca -config %s -create_serial -out %s -days %s -batch -keyfile %s -selfsign -extensions v3_ca -infiles %s" % (openssl, cfgfile, crt, days['10y'], key, request)
	print command
	os.system(command)


"""
Print application name and version
"""
print _("MyCA version"), myca_version;

if (remove in sys.argv):
	print _("Remove actual version of CA [%s/%s]") % (_("y"), _("N")) ,
	remove_previous_ca(raw_input());
else:
	check_prev_ca();
	create_new_ca();

