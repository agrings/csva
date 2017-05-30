#!/usr/bin/python
# -*- coding: utf-8 -*-

from xml.dom import minidom
import sys
import re
from sys import stdin
import getopt
import pyodbc

def usage():
  print __doc__

def str2bool(v):
  return v.lower() in ("yes","true","t","1")

class Xqkt():
  resumo = ""
  exportar = ""
  pos_exec = "" 
  exportar_nomes_campos = False
  caracter_separacao = ";"
  descricao = ""
  sql_query = ""
  string_conexao_windows = ""
  string_conexao_pyodbc = 'DRIVER={MySQL};SERVER=192.168.0.100;DATABASE=wjp;UID=wjpadm;PWD=2u0qej'

  parametros = []  
  columns = [] #nomes das colunas

  def extrai_parametros(self,sql_string):
    #regex = re.compile(r"(\[\w+\])",re.IGNORECASE)
    regex = re.compile(r'\[([^]]*)\]',re.IGNORECASE)
    m=regex.findall(sql_string)
    return list(set(m)) #remove parametros duplicados

  def substitui_parametros(self, sql_string, param_list):
    
    for param in param_list:
       print "Entre com %s:" %(param) 
       valor=stdin.readline().rstrip("\n")
       sql_string = sql_string.replace(param, valor)
    return sql_string

  def config(self, attributes, key, default_value):
      return attributes[key].value if (key in attributes.keys()) else default_value

  def __init__(self,filename):
    xmldoc = minidom.parse(filename)
    itemlist = xmldoc.getElementsByTagName('xmlqkt') 
    attribs = itemlist[0].attributes
    self.resumo = self.config(attribs,'Resumo','')
    self.exportar = self.config(attribs,'Exportar','')
    self.pos_exec = self.config(attribs,'PosExec','')
    self.exportar_nomes_campos = self.config(attribs,'ExportarNomesCampos','')
    self.cadacter_separacao = self.config(attribs,'CaracterSeparacao','')
    self.descricao = self.config(attribs,'Descricao','')
    self.sql_query = (self.config(attribs,'SQL','')).encode('utf-8')
    self.parametros = self.extrai_parametros(self.sql_query)
    self.string_conexao_windows = self.config(attribs,'StringConexao','')
    self.string_conexao_pyodbc=self.config(attribs,'StringConexaoPyOdbc',self.string_conexao_pyodbc)

  def printline(self, list):
    size = len(list) 
    i = 0
    for item in list:
      if not item:
        item=""
      sys.stdout.write("%s"%(item))
      i+=1
      if i < size:
        sys.stdout.write(self.caracter_separacao)
    print ""
  
  def connect_db(self):
     self.connection = pyodbc.connect(self.string_conexao_pyodbc)
     self.cursor = self.connection.cursor()

  def remove_comentarios_2(self, sql):
    state=0
    index_ini=sql.find('/*')  
    if index<0:
       index_fim=sql.find('*/')
       return sql[index_fim+2:]
    else:
       return sql[0:index_ini] + self.remove_comentarios(sql[index_ini+2:])

  def remove_comentarios_multilinhas(self,sql):
    sql_no_comments=''
    abertos=0
    for i in range(len(sql)):
      if i < len(sql):
          if sql[i:i+2]=='/*':
             abertos+=1
          if abertos and (sql[i-2:i]=='*/'):
             abertos-=1

      if abertos==0:
        sql_no_comments+=sql[i]
    return sql_no_comments

  def remove_comentarios_inline(self,sql):
    linhas=sql.split('\n')
    no_comments=''
    for linha in linhas:
      no_comments+=(linha.split('#')[0]+'\n')
    return no_comments

  def remove_todo_comentario(self,sql):
    return self.remove_comentarios_inline(self.remove_comentarios_multilinhas(sql))
    
  def execute_query(self):

    sql = self.substitui_parametros(self.sql_query, self.parametros)
    #print sql
    sql = self.remove_todo_comentario(sql)
    self.cursor.execute(sql)
    self.columns = [column[0] for column in self.cursor.description]

    rows=[]
    while 1:
      row = self.cursor.fetchone()
      if not row:
        break
      rows.append(row) 
    return rows
    
def do_it(filename):

  xqkt = Xqkt(filename)
  xqkt.connect_db()
  rows=xqkt.execute_query()

  if xqkt.exportar_nomes_campos:
     xqkt.printline(xqkt.columns)
  
  for row in rows:
    xqkt.printline(row) 

def main(argv):
  try:                                
    format = ""
    mode = ""
    opts, args = getopt.getopt(argv, "h", ["help"])
    if len(args) != 1:
      raise getopt.GetoptError("Numero errado de argumentos")

    for opt, arg in opts:                
      if opt in ("-h", "--help"):      
        usage()                     
        sys.exit()                  

    do_it(args[0])
 
  except getopt.GetoptError,err:          
    imprime_erro('',err)
    usage()                         
    sys.exit(2)                     


if __name__=="__main__":
  main(sys.argv[1:]) 


