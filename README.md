#csva

Chupeta
=======

Odbc to Csv/txt/html extractor

Install (Ubuntu)
----------------

You will need:
* wxpython
* pyodbc 
* pyaml

File association
----------------

```
sudo cp chupeta.desktop /usr/share/applications/

sudo cp cyx_mime.xml /usr/share/mime/packages/

sudo update-mime-database /usr/share/mime

```


(See https://coderwall.com/p/qjda2q/create-new-mime-type-and-assign-an-icon-to-it-in-ubuntu
 and https://askubuntu.com/questions/525953/use-custom-command-to-open-files
)



Install the Odbc driver
-----------------------

Postgresql: 
```
   apt-get install odbc-postgresql
```


Mysql:

   * Download from: https://dev.mysql.com/downloads/connector/odbc/
   * Follow the instructions in: https://dev.mysql.com/doc/connector-odbc/en/connector-odbc-installation-binary-unix-tarball.html
   
   
Configure the Driver
--------------------


Edit the file /etc/odbc.ini

```
[DevDb]
Description	= Postgresql connecton to Development database
Driver		= PostgreSQL Unicode
Database	= devdb
Servername	= 192.168.0.300
Username	= postgres
Password	= blablublapombo
Port		= 5432
```

