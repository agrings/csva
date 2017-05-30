#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
"""
  csvanywere.py
  Author: Alexandre Grings
  
  Usage: csvanywere.py [r|c|e|h] file.cyx

  Where: file.cyx: query in cyx format (yaml data)
 Options:
   -r or -run: run query
   -e or -edit: edit query
   -c or -convert: convert from xqkt to cyx format 
   -n or --new: create empty cyx  file
   -p or --print: run query and print results to the screen

"""
###############################################################################


from xml.dom import minidom
import sys
import re
import os
import io
from sys import stdin
import getopt
import pyodbc
from xqkt import *
import yaml #config
from collections import OrderedDict
import argparse
import tempfile
import datetime

def usage():
  print __doc__

def str2bool(v):
  return v.lower() in ("yes","true","t","1")

def isnumber(s):
  try:
    int(s)
    return True
  except ValueError:
    try:
      float(s)
      return True
    except ValueError:
      return False


def isfloat(s):
  try:
    int(s)
    return False
  except ValueError:
    try: 
      float(s)
      return True
    except ValueError:
      return False

class CsvAnyware():
  #class variables
  resumo = ""
  exportar = ""
  pos_exec = "" 
  exportar_nomes_campos = False
  caracter_separacao = ";"
  descricao = ""
  sql_query = ""
  string_conexao_windows = ""
  string_conexao_pyodbc = ''

  param_names = []  
  param_values = []
  columns = [] #nomes das colunas

  def extrai_parametros(self,sql_string):
    regex = re.compile(r'\[([^]]*)\]',re.IGNORECASE)
    params=regex.findall(sql_string)
    params2=list(OrderedDict.fromkeys(params))
    return params2

  def substitui_parametros(self):
    sqlstr=self.sql_query
    if not self.param_values:
      self.param_values=[]
      for param in self.param_names:
         print "Entre com %s:" %(param) 
         self.param_values+=[stdin.readline().rstrip("\n")]
      
    for param,valor in zip(self.param_names,self.param_values):
       print param+"="+valor
       sqlstr = sqlstr.replace('['+param+']', valor)

    return sqlstr

  def config(self, attributes, key, default_value):
      return attributes[key] if (key in attributes.keys()) else default_value
  
  def read_config(self,filename):

    # Read YAML file
    with open(filename, 'r') as stream:
      data_loaded = yaml.load(stream)
    return data_loaded

  def write_config(self,filename):
    # Write YAML file
    properties=vars(self)
    with io.open(filename, 'w', encoding='utf8') as outfile:
      yaml.dump(properties, outfile, default_flow_style=False, allow_unicode=True)


  
  def __init__(self,filename):

    just_filename, file_extension = os.path.splitext(filename)
    self.filename=just_filename+".cyx"
    if file_extension=='.xqkt':
      older_xqkt = Xqkt(filename)
      self.resumo = older_xqkt.resumo
      self.exportar = older_xqkt.exportar
      self.pos_exec = older_xqkt.pos_exec
      self.exportar_nomes_campos = older_xqkt.exportar_nomes_campos
      self.caracter_separacao = older_xqkt.caracter_separacao
      self.descricao = older_xqkt.descricao
      self.sql_query = older_xqkt.sql_query
      self.param_names = older_xqkt.parametros
      self.string_conexao_windows = older_xqkt.string_conexao_windows 
      self.string_conexao_pyodbc = older_xqkt.string_conexao_pyodbc
      self.write_config(self.filename) #converte para novo formato
    else:
      configuration = self.read_config(filename)
      self.resumo = self.config(configuration,'resumo','')
      self.exportar = self.config(configuration,'exportar','')
      self.pos_exec = self.config(configuration,'pos_exec','')
      self.exportar_nomes_campos = self.config(configuration,'exportar_nomes_campos','')
      self.caracter_separacao = self.config(configuration,'caracter_separacao','')
      self.descricao = self.config(configuration,'descricao','')
      self.sql_query = (self.config(configuration,'sql_query','')).encode('utf-8')
      self.param_names = self.extrai_parametros(self.sql_query)
      self.string_conexao_windows = self.config(configuration,'string_conexao_windows','')
      self.string_conexao_pyodbc=self.config(configuration,'string_conexao_pyodbc',self.string_conexao_pyodbc)
      self.separador_decimal=self.config(configuration,'separador_decimal',',')



  def reformat_type(self,stuff):
    if not stuff:
      stuff=""
    str_stuff=("%s" %stuff).encode('utf-8')
    if isfloat(str_stuff):
      return str_stuff.replace('.',self.separador_decimal) 
    else:
      return(str_stuff)  


  def format_row_as_a_list(self, row_as_a_list):
    list_out=[]
    sizes=[]
    for item in row_as_a_list:
      item_str="%s"%(self.reformat_type(item))
      list_out+=[item_str]
      sizes+=[len(item_str)]
    return (list_out,sizes)
    

  def formatline(self, list):
    size = len(list) 
    i = 0
    linha=''
    for item in list:
      linha+="%s"%(self.reformat_type(item))
      i+=1
 
      if i < size:
        linha+=self.caracter_separacao
 
    return linha+"\n"
 
  def connect_db(self):
     self.connection = pyodbc.connect(self.string_conexao_pyodbc)
     self.cursor = self.connection.cursor()

  def remove_multiline_comments(self,sql):
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

  def remove_inline_comments(self,sql):
    linhas=sql.split('\n')
    no_comments=''
    for linha in linhas:
      no_comments+=(linha.split('#')[0]+'\n')
    return no_comments

  def remove_all_comments(self,sql):
    return self.remove_inline_comments(self.remove_multiline_comments(sql))
    
  def execute_query(self):
    sql = self.substitui_parametros()
    sql = self.remove_all_comments(sql)
    self.cursor.execute(sql)
    self.columns = [column[0] for column in self.cursor.description]

    rows=[]
    while 1:
      row = self.cursor.fetchone()
      if not row:
        break
      rows.append(row) 
    return rows
    
def edit_it(cyx):
  try:
    editor=os.environ['CYX_EDITOR']
  except KeyError:
    print "A variavel de ambiente 'CYX_EDITOR' não existe"
    print "Configure 'CYX_EDITOR' para apontar para o editor sql de sua preferência"
    return

  temp_filename=cyx.filename+'.tmp'
  f_edit=open(temp_filename,'w')
  f_edit.write(cyx.sql_query)
  f_edit.close()

  os.system(editor+' '+temp_filename)

  f_edit=open(temp_filename,'r')
  cyx.sql_query=f_edit.read() 
  cyx.write_config(cyx.filename)
  f_edit.close()


def run_it(cyx, param_values, tabularize, temp_export):

  cyx.param_values=param_values

  cyx.connect_db()
  rows=cyx.execute_query()
  
  if not rows:
    print "A consulta nao retornou valores"
    return

  if tabularize:
    tabularize_it(cyx,rows)
    return

  if temp_export:
    cyx.exportar=temp_export[0]

  if cyx.exportar or temp_export:
    print "Exportando dados para arquivo "+ cyx.exportar
    output_f=open(cyx.exportar,'w')
    if cyx.exportar_nomes_campos:
      output_f.write(cyx.formatline(cyx.columns))
  
    for row in rows:
      output_f.write(cyx.formatline(row)) 
    output_f.close()

  if temp_export:
    open(cyx.exportar+".OK","a").close()
  else:
    print "Executando :{}".format(cyx.pos_exec)
    os.system(cyx.pos_exec)


def tabularize_it(cyx, rows):

  max_sizes=[]
  for column in cyx.columns:
    max_sizes+=[len(column)]
  
  new_rows=[]
  for row in rows:
    (str_list,new_sizes)=cyx.format_row_as_a_list(row)
    max_sizes=[ a if a> b else b for a,b in zip(max_sizes,new_sizes) ]
    new_rows+=[str_list]
  
  format_str=""
  for field,size in zip(new_rows[0],max_sizes):
    alignment = "%" if isnumber(field) else "%-"
    format_str += alignment+str(size)+"s|"

  print format_str % tuple(cyx.columns)
  for row in new_rows:
    print format_str % tuple(row)




def main(parser):
  parser.add_argument("filename",help="arquivo do tipo CYX (consulta odbc e exportacao)")
  parser.add_argument("-e","--edit",action="store_true",
                      help="Usa o editor indicado na variavel de ambiente 'CYX_EDITOR'"\
                           " para abrir o sql")
  parser.add_argument("-r","--run",action="store_true",help="Roda a query")
  parser.add_argument("-c","--convert",action="store_true",help="Converte um arquivo xqkt em cyx")
  parser.add_argument("-t","--tabularize",action="store_true",help="Formata os dados em tabela e printa na tela")
  parser.add_argument("-T","--temp",nargs=1,
                      help="Exporta dados para o arquivo FILENAME informado."\
                           "Ao final gera um arquivo FILENAME.ok."\
                           "Isso permite o intercambio de dados com outros programas."\
                           "O arquivo '.ok' indica que os dados estao prontos"
                     )
  parser.add_argument("-p","--parameters",nargs='+',help="Fornece parametros na linha de comando (caso contrario o programa espera a entrada)")
  args = parser.parse_args()
  cyx=CsvAnyware(args.filename)
  if args.edit:
    edit_it(cyx)
  elif args.run:
    run_it(cyx,args.parameters, args.tabularize, args.temp)
  elif args.convert:
    print "Converted" #Done when object is created
  else:
    print "Argumentos invalidos, veja --help"
    
  
    

if __name__=="__main__":
  parser = argparse.ArgumentParser()
  main(parser) 
  stdin.readline().rstrip("\n")  


