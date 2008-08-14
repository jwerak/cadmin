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
cadirs = {'CA':'ca', 'SRV':'server', '_SRVN':'server/newcerts', 'WRK':'workstation', '_WRKN':'workstation/newcerts', 'USR':'user', 'CRL':'crl', 'PRV':'private'}
cafiles = { 'KEY':'cakey.pem', 'REQ':'careq.pem', 'CRT':'cacrt.pem', 'IDX':'index.txt', 'SRL':'serial' }
openssl = 'openssl'
remove = '--remove'
days = {'10y':'3652'}
cfgfile = 'CA.cnf'

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
	for dir in cadirs:
		if (dir[0] != '_'):
			print _("Creating directory %s...") % cadirs[dir];
			os.mkdir(cadirs[dir]);
	for dir in cadirs:
		if (dir[0] == '_'):
			print _("Creating directory %s...") % cadirs[dir];
			os.mkdir(cadirs[dir]);
	open(cafiles['IDX'], 'w').close();

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
		for dir in cadirs:
			if (dir[0] != '_'):
				remove_dir_content(cadirs[dir]);
	content = []
	try:
		content = os.listdir('.');
		for fod in content:
			if (os.path.isfile(fod)):
				for file in cafiles:
					if (fod.startswith(cafiles[file])):
						print _("Removing file %s...") % fod
						os.remove(fod)
	except OSError:
		print "OSError"

#
# check for existing files (previous CA)
#
def check_prev_ca():
	error = 0;
	for dir in cadirs:
		if (os.path.isdir(cadirs[dir])): error = 1;
	if (error == 1):
		print _("FAIL: Previous version of CA exists...");
		print _("Overvrite previous version of CA [%s/%s]") % (_("y"), _("N")) ,;
		remove_previous_ca(raw_input());
	else:
		print _("OK: No previous version of CA exists...") ;

#
# create new CA
#
def create_new_ca():
	create_dir_structure();
	print _("Creating CA certificate...");
	command = "%s req -config %s -new -keyout %s -out %s" % (openssl, cfgfile, os.path.join(cadirs['PRV'], cafiles['KEY']), cafiles['REQ'])
	print command
	os.system(command)
	command = "%s ca -config %s -create_serial -out %s -days %s -batch -keyfile %s -selfsign -extensions v3_ca -infiles %s" % (openssl, cfgfile, cafiles['CRT'], days['10y'], os.path.join(cadirs['PRV'], cafiles['KEY']), cafiles['REQ'])
	print command
	os.system(command)


"""
Print application name and version
"""
print _("MyCA version"), myca_version;

if (remove in sys.argv):
	remove_previous_ca(_("y"));
else:
	check_prev_ca();
	create_new_ca();

