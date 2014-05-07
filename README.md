Hashbooks
=========

 - Gets the md5 of ebook files (recursively) and saves it to MySQL database
 - it only hashes the first 8096 bytes of the book, to increase speed.
 - it assumes your ebooks are inside its publishers folder
 - it does not save any other book properties other than the filename,publisher & md5

Requirements
------------
 - Python 2.7
 - Python MySQL interface (MySQLdb)
 
