#!/usr/bin/python

#RCD

import sys, re, md5,os

"""
this function returns the MD5 Digest (in string) of a file
you provide from its parameters
"""
def sumfileX(fname):
	try:
		f = open(fname, 'rb')
	except:
		return 'Failed to open file'
	m= md5.new()
	while True:
		d= f.read(8096)
		if not d:
			break
		m.update(d)
	f.close()	
	return m.hexdigest()
"""
this function returns the MD5 Digest for the first 1024 bytes of a file
you provide from its parameters
"""
def sumfile(fname):
	try:
		f = open(fname, 'rb')
	except:
		return 'Failed to open file'
	m= md5.new()
	d= f.read(1024)
	m.update(d)
	f.close()	
	return m.hexdigest()
	
"""
this function accepts a list then
returns the MD5 hash of all items in the list
"""
def sumlist(filelist):
	m = md5.new()
	for f in filelist:
		m.update(f)
	return m.hexdigest()
"""
Recursive directory walk  

Walk(<path of the folder you want to walk>,
     <0 for not recursive,1 for recursive>,
     <this is the filter or pattern to include>,
     <if 0 then it does not return folders,1 otherwise>)
 this function returns a list.
"""
def Walk( root, recurse=0, pattern='*', return_folders=0 ):
	import fnmatch, os, string

	result = []

	try:
		names = os.listdir(root)
	except os.error:
		return result

	pattern = pattern or '*'
	pat_list = string.splitfields( pattern , ';' )

	for name in names:
		fullname = os.path.normpath(os.path.join(root, name))

		for pat in pat_list:
			if fnmatch.fnmatch(name, pat):
				if os.path.isfile(fullname) or (return_folders and os.path.isdir(fullname)):
					result.append(fullname)
				continue
		if recurse:
			if os.path.isdir(fullname) and not os.path.islink(fullname):
				result = result + Walk( fullname, recurse, pattern, return_folders )
			
	return result
			
def checksumfiles(files):
	filedic = {}
	count = len(files)
	for fname in files:
		print "\n["+str(count)+"] Processing "+fname
		_hash_ = sumfile(fname)
		count=count-1	
		filedic[fname.split('\\')[-1]] = _hash_				
	return filedic
def createDatabase(cursor, dbName):
	query = """CREATE DATABASE IF NOT EXISTS %s""" % (dbName)
	cursor.execute(query)
	return
	
def useDatabase(cursor,dbName):
	query = """USE %s""" % (dbName)
	cursor.execute(query)
	return
	
def createBookTable(cursor,dbName,table):
	#useDatabase(cursor,dbName)
	query = """DROP TABLE IF EXISTS %s""" % (table)
	cursor.execute(query)
	ct="""
	   CREATE TABLE %s (
	  `bookId` int(10) unsigned NOT NULL auto_increment,
	  `Name` varchar(120) collate latin1_general_ci NOT NULL default '',
	  `md5` varchar(45) collate latin1_general_ci NOT NULL default '',
	  `pubId` int(10) unsigned NOT NULL default '0',
	  PRIMARY KEY  (`bookId`),
	  KEY `pubId` (`pubId`)
	  ) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_general_ci
	""" % (table)
	cursor.execute(ct)
	return
	
def createPublisherTable(cursor,dbName,table):
	#useDatabase(cursor,dbName)
	query = """DROP TABLE IF EXISTS %s""" % (table)
	cursor.execute(query)		
	query = """
			CREATE TABLE %s (
			`pubId` int(10) unsigned NOT NULL auto_increment,
			`name` varchar(20) collate latin1_general_ci NOT NULL default '',
			`md5` varchar(45) collate latin1_general_ci NOT NULL default '',
			PRIMARY KEY  (`pubId`)
			) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_general_ci
	""" % (table)
	cursor.execute(query)
	return
	

def insertIntoPublisher(cursor,db,table,name,md5):
	n = name.replace("'","\\'")		
	query = """insert into %s(name,md5) values ('%s','%s')""" % (table,n,md5)
	#useDatabase(cursor,db)
	cursor.execute(query)
	return
	
def insertIntoBooks(cursor,db,table,Name,md5,pubId):
	name=Name.replace("'","\\'")
	query = """insert into %s(Name,md5,pubId) values ('%s','%s','%d')""" % (table,name,md5,pubId)
	#useDatabase(cursor,db)
	cursor.execute(query)
	return
	
if len(sys.argv) not in [2,4]:
	print "\nUsage: ./bookz.py <dir> -ext [extension filename]"
	print "\nExample: ./bookz.py m:\\books\\computers -ext pdf"
	print "will produce all books/filetypes md5 hashcode from a given directory and all subdirectories"
	sys.exit(1)

from time import clock as now
start = now()
bookdictionary={}

#setup mysql, connection, cursor
try:
	import MySQLdb
except(ImportError):
	print '[-] please install MySQLdb'
	sys.exit(-1)

print '[+] connecting database..'	
db = MySQLdb.connect(host='localhost',	user='root',passwd='')
c = db.cursor()

dbname = 'Libros'
booktable = 'bookz'
pubtable = 'publisherz'

print '[+] creating database..'
createDatabase(c,dbname)
useDatabase(c,dbname)

print '[+] creating book table'
createBookTable(c,dbname,booktable)

print '[+] creating publishers table'
createPublisherTable(c,dbname,pubtable)
		
if len(sys.argv) == 2:
	dir = os.listdir(sys.argv[1])
	for file in dir:
		fn = os.path.normpath(os.path.join(sys.argv[1],file))
		if os.path.isdir(fn):
			print '[+] Trying to extract folder ' + fn
			files = Walk(fn, 1, '*', 0)	
			#query the id of fn
			if files:								
				dirChecksum = sumlist(files)		
				fol = fn.split("\\")[-1]
				insertIntoPublisher(c,dbname,pubtable,fol,dirChecksum)		
				bookdictionary=checksumfiles(files)				
				query="""SELECT pubId FROM %s p where name='%s'""" % (pubtable,fol.replace("'","\\'"))
				c.execute(query)
				gotPubId=c.fetchone()
				if gotPubId==None:
					print '[-] No results from the query!'
					continue
				for k,v in bookdictionary.items():
					print "[+] Inserting %s,%s into table %s" % (k,v,booktable)					
					insertIntoBooks(c,dbname,booktable,k,v,gotPubId[0])
			else:
				print "[-] No files inside %s" % (sys.argv[1])
				
else:
	dir = os.listdir(sys.argv[1])
	for file in dir:
		fn = os.path.normpath(os.path.join(sys.argv[1],file))
		if os.path.isdir(fn):
			print '[+] Trying to extract folder ' + fn
			files = Walk(sys.argv[1], 1, '*.'+sys.argv[3]+';')
			if files:								
				dirChecksum = sumlist(files)		
				fol = fn.split("\\")[-1]
				insertIntoPublisher(c,dbname,pubtable,fol,dirChecksum)		
				bookdictionary=checksumfiles(files)				
				query="""SELECT pubId FROM %s p where name='%s'""" % (pubtable,fol.replace("'","\\'"))
				c.execute(query)
				gotPubId=c.fetchone()
				if gotPubId==None:
					print '[-] No results from the query!'
					continue
					
				for k,v in bookdictionary.items():
					print "[+] Inserting %s,%s into table %s" % (k,v,booktable)					
					insertIntoBooks(c,dbname,booktable,k,v,gotPubId[0])
			else:
				print "[-] No files inside %s" % (sys.argv[1])

finish = now()
elapsed_time = finish - start	
print '[+] Elapsed time is '+str(elapsed_time)+' seconds'
