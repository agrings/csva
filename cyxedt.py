#!/usr/bin/python
# -*- coding: utf-8 -*-

import wx
import wx.grid as gridlib
import wx.stc as stc
import keyword
from csva import *
import wx.lib.newevent

ChangedEvent, EVT_CHANGED = wx.lib.newevent.NewCommandEvent()

class CodeEditorBase(stc.StyledTextCtrl):

    def __init__(self, parent):
	super(CodeEditorBase, self).__init__(parent)
	# Attributes
	font = wx.Font(10, wx.FONTFAMILY_MODERN,
	wx.FONTSTYLE_NORMAL,
	wx.FONTWEIGHT_NORMAL)
	self.face = font.GetFaceName()
	self.size = font.GetPointSize()
        self.filename = ""
	# Setup
	self.SetupBaseStyles()
      

    def EnableLineNumbers(self, enable=True):
	"""Enable/Disable line number margin"""
	if enable:
	    self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
	    self.SetMarginMask(1, 0)
	    self.SetMarginWidth(1, 25)
	else:
	    self.SetMarginWidth(1, 0)

    def GetFaces(self):
	 """Get font style dictionary"""
	 return dict(font=self.face,
		     size=self.size)

    def SetupBaseStyles(self):
	"""Sets up the the basic non lexer specific
	   styles.
	"""
	faces = self.GetFaces()
	default = "face:%(font)s,size:%(size)d" % faces
	self.StyleSetSpec(stc.STC_STYLE_DEFAULT, default)
	line = "back:#C0C0C0," + default
	self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, line)
	self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR,
			  "face:%(font)s" % faces)


class OutputGrid(wx.ListCtrl):
    def __init__(self,parent):
        super(OutputGrid,self).__init__(parent,
                                         style=wx.LC_REPORT)
    
    def addHeader(self,header_list):
        """ Add column headers """
        i=0
        for name in header_list:
            self.InsertColumn(i,name)
            i+=1
            
    def addRow(self, row_as_a_list ):
        """ Adds a row to the grid """
        item = self.Append(tuple(row_as_a_list))

  
               
class ConfigPanel(wx.Panel):
    def __init__(self, parent, config_dict):
        wx.Panel.__init__(self, parent, -1)

        self.configuration={}
        self.textCtrls={}
        if config_dict:
           self.SetLayout(config_dict)


    def SetLayout(self, config_dict):
        """ config_dict vem na forma { 'atributo' : valor  ... }
            Eh criado um TextCtrl para cada atributo e o texto
            eh setado com o valor correspondente
        """
        # Destroy componentes anteriores
        for child in self.GetChildren():
            child.Destroy() 
 
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.textCtrls={}
        self.configuration = config_dict
        for key in self.configuration.keys():
            label = wx.StaticText(self, wx.ID_ANY, key)
            if "\n" in self.configuration[key]:
                self.textCtrls[key]=wx.TextCtrl(self, wx.ID_ANY,
                                                style=wx.TE_MULTILINE, 
                                                value=self.configuration[key])
            else:
                self.textCtrls[key] = wx.TextCtrl(self, wx.ID_ANY, 
                                                  self.configuration[key])
            self.textCtrls[key].Bind(wx.EVT_KEY_UP, self.OnKeyUp)

            sizer= wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(label,0, wx.ALL|wx.ALIGN_RIGHT, 5)
            sizer.Add(self.textCtrls[key],1, wx.ALIGN_RIGHT, 5)
            main_sizer.Add(sizer,0,wx.EXPAND,5)
        self.SetSizer(main_sizer)
        self.Layout()

    def OnKeyUp(self, event):
        """ KeyUp comes last """
        print "."
        wx.PostEvent(self, ChangedEvent(self.GetId()))
        event.Skip()


class MyNotebook(wx.Notebook):
    def __init__(self, parent):
	super(MyNotebook, self).__init__(parent)

	#Attributes
	self.edt = CodeEditorBase(self)
	self.log = wx.TextCtrl(self,
				    value="The log",
				    style=wx.TE_MULTILINE)
        self.cfg = ConfigPanel(self,{})

       
        self.out = OutputGrid(self)

	# Setup
	#self.AddPage(self.textctrl, "Text Editor")
	self.AddPage(self.edt, "Text Editor")
	self.AddPage(self.log, "Activity Log")
	self.AddPage(self.cfg, "Configuration")
	self.AddPage(self.out,"Data output")

class TopPanel(wx.Panel):
    def __init__(self, parent):
	wx.Panel.__init__(self, parent, -1)

	
	sizer = wx.BoxSizer(wx.HORIZONTAL)

        bmp = wx.Bitmap("execute.bmp")
        button = wx.Button(self, label= "Executar")
        button.SetBitmap(bmp)
        self.Refresh()
	sizer.Add(button)
	button.Bind(wx.EVT_BUTTON, self.OnButton)
	
	self.SetSizer(sizer)
	
	
    def OnButton(self, event):
        event.Skip()

ID_READ_ONLY = wx.NewId()

class MainFrame(wx.Frame):
     
    def __init__(self, filename=''):
	 wx.Frame.__init__(self, None, -1, 'CyxEditor 1.0')
 
	 # Attributes
	 self.nbk = MyNotebook(self)
	 self.tp = TopPanel(self)
	 
	 #layout
	 sizer = wx.BoxSizer(wx.VERTICAL)
	 sizer.Add(self.tp, 0, wx.EXPAND)
	 sizer.Add(self.nbk, 1, wx.EXPAND)
	 self.CreateStatusBar()
	 self.SetSizer(sizer)
	 self.SetSize((800, 600))
	 
	 # Setup the Menu
	 self.menub = wx.MenuBar()

	 # File Menu
	 filem = wx.Menu()
	 filem.Append(wx.ID_OPEN,"&Abrir\tCtrl+O")
	 filem.Append(wx.ID_SAVE,"&Salvar\tCtrl+S")
	 filem.Append(wx.ID_SAVEAS,"Salvar &como\tShift+Ctrl+S")
	 self.menub.Append(filem,"&Arquivo")

	 # Edit Menu
	 editm = wx.Menu()
	 editm.Append(wx.ID_COPY,"Copiar\tCtrl+C")
	 editm.Append(wx.ID_CUT,"Cortar\tCtrl+X")
	 editm.Append(wx.ID_PASTE,"Colar\tCtrl+V")
	 editm.AppendSeparator()
	 editm.Append(ID_READ_ONLY,"Read Only",
		      kind=wx.ITEM_CHECK)
	 self.menub.Append(editm,"E&ditar")

 
	 self.SetMenuBar(self.menub)

	 #Event Handler
	 self.Bind(wx.EVT_MENU,self.OnMenu)  
         self.Bind(wx.EVT_BUTTON, self.OnButton)
         self.Bind(EVT_CHANGED, self.OnConfigChanged)

         if filename:
             self.LoadFromFile(filename)
         else:
             self.cyx = CsvAnywhere(filename)
             self.SetConfiguration()

    def OnButton(self, event):
	btn = event.GetEventObject()
        btn.Enabled=False
        try:
          sav_sql=self.cyx.sql_query
          new_sql=self.nbk.edt.GetText()
          ini,fim = self.nbk.edt.GetSelection()
          if ini != fim: 
            new_sql=self.nbk.edt.GetSelectedText()

          self.cyx.sql_query=new_sql
          self.cyx.connect_db()
          rows=self.cyx.execute_query()
          self.nbk.out.ClearAll()
          self.nbk.out.addHeader(self.cyx.columns)
          for row in rows:
              self.nbk.out.addRow(row)
        finally:
          btn.Enabled=True

    def SetConfiguration(self):
        #Apenas essas configuracoes sao aceitas
        #O Sql nao eh carregado aqui
        keys =[
		"resumo", 
		"exportar", 
		"pos_exec",
		"exportar_nomes_campos", 
		"caracter_separacao",
		"descricao", 
                "string_conexao_pyodbc",
                "separador_decimal"]
        
	config_dict ={ key: self.cyx.__dict__[key] for key in keys }
        self.nbk.cfg.SetLayout(config_dict)	 

    def LoadFromFile(self, fname):
        self.cyx=CsvAnywhere(fname)
        self.nbk.edt.SetText(self.cyx.sql_query)
	self.PushStatusText(fname)
        self.SetConfiguration()
        

    def SaveToFile(self):
        self.cyx.sql_query=self.nbk.edt.GetText()
        self.cyx.write_config(self.cyx.filename)
        self.menub.Enable(wx.ID_SAVE,False)

    def OnConfigChanged(self,event):
        self.menub.Enable(wx.ID_SAVE,True)
        

    def OnKeyUp(self, event):
        print "OnKeyUp Called 2"
        self.Modified() 
        event.Skip()

    def OnMenu(self, event):
	""" Handle menu clicks """
	evt_id = event.GetId()
                  
        editor = self.nbk.edt

	actions = { wx.ID_COPY : editor.Copy,
		    wx.ID_CUT : editor.Cut,
		    wx.ID_PASTE : editor.Paste }
	action = actions.get(evt_id,None)
	
	if action:
	   action()
	elif evt_id == ID_READ_ONLY:
	   #Toogle enabled state
	   editor.Enable(not editor.Enabled)
	elif evt_id == wx.ID_OPEN:
	   dlg = wx.FileDialog(self,"Abrir arquivo",
			       style=wx.FD_OPEN)
	   if dlg.ShowModal() == wx.ID_OK:
	       fname = dlg.GetPath()
	       self.LoadFromFile(fname)
	elif evt_id == wx.ID_SAVE:
            self.SaveToFile()
            
        else:
           event.Skip()

def main(parser):
  parser.add_argument("filename",nargs='?',default='',help="arquivo do tipo CYX (consulta odbc e exportacao)")
  args = parser.parse_args()
  app = wx.App(False)
  win = MainFrame(args.filename)
  win.Show(True)
  app.MainLoop()
  
    

if __name__=="__main__":
  parser = argparse.ArgumentParser()
  try:
    main(parser) 
  except:
    traceback.print_exc(file=sys.stdout)
    print "Pressione qualquer tecla para continuar..."
    stdin.readline().rstrip("\n") 
