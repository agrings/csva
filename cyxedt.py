#!/usr/bin/python
# -*- coding: utf-8 -*-

import wx
import wx.grid as gridlib
import wx.stc as stc
import keyword
from csva import *
import wx.lib.newevent
import wx.lib.agw.aquabutton as AB
import wx.lib.agw.gradientbutton as GB
import wx.lib.mixins.listctrl as listmix
import collections #Para OrderedDict


ChangedEvent, EVT_CHANGED = wx.lib.newevent.NewCommandEvent()

def AddAppPath(filename):
    """
    Adds the executable path to the filename 
    """
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)

    return os.path.join(application_path, filename)

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


class TestVirtualList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):
    def __init__(self, parent, header,data):
        wx.ListCtrl.__init__( self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)

        #adding some art
        self.il = wx.ImageList(16, 16)
        a={"sm_up":"GO_UP","sm_dn":"GO_DOWN","w_idx":"WARNING","e_idx":"ERROR","i_idx":"QUESTION"}
        for k,v in a.items():
            s="self.%s= self.il.Add(wx.ArtProvider_GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,v)
            exec(s)
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        #adding some attributes (colourful background for each item rows)
        self.attr1 = wx.ListItemAttr()
        self.attr1.SetBackgroundColour("light green")

        #building the columns
        #self.AddHeader(header)
        #self.AddRows(data)

        #These two should probably be passed to init more cleanly
        #setting the numbers of items = number of elements in the dictionary
        self.itemDataMap = data
        self.itemIndexMap = data.keys()
        self.SetItemCount(len(data))
        
        #mixins
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        #listmix.ColumnSorterMixin.__init__(self, 0)

        #sort by genre (column 2), A->Z ascending order (1)
        #self.SortListItems(2, 1)

        #events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)

    def AddHeader(self,header_list):
        """ Add column headers """
        i=0
        self.ClearAll()
        for name in header_list:
            self.InsertColumn(i,name)
            i+=1

    def AddRows(self, value_matrix ):
        """  Add values to the grid
             value_matrix is in the format:
              { 0: [ row1col1, row1col2...] 
                1: [ row2col1, rowcol2...] ...} 
        """
        for i in range(len(value_matrix)):
           self.itemDataMap[i]=value_matrix[i] 
        self.itemIndexMap = self.itemDataMap.keys()
        num_cols=self.GetColumnCount()
        listmix.ColumnSorterMixin.__init__(self, num_cols)
        self.SetItemCount(len(value_matrix))
        i=0
        for row in value_matrix:
            self.Append(tuple(row))
        for col in range(num_cols):
            self.SetColumnWidth(col, wx.LIST_AUTOSIZE)


    def OnColClick(self,event):
        event.Skip()

    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnItemDeselected(self, evt):
        print ("OnItemDeselected: %s" % evt.m_itemIndex)


    #---------------------------------------------------
    # These methods are callbacks for implementing the
    # "virtualness" of the list...

    def OnGetItemText(self, item, col):
        index=self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        return s

    def OnGetItemImage(self, item):
            return -1

    def OnGetItemAttr(self, item):
        index=self.itemIndexMap[item]

        if index%2:
            return self.attr1
        else:
            return None

    #---------------------------------------------------
    # Matt C, 2006/02/22
    # Here's a better SortItems() method --
    # the ColumnSorterMixin.__ColumnSorter() method already handles the ascending/descending,
    # and it knows to sort on another column if the chosen columns have the same value.

    def SortItems(self,sorter=cmp):
        items = list(self.itemDataMap.keys())
        items.sort(sorter)
        self.itemIndexMap = items
        
        # redraw the list
        self.Refresh()

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)


 
class ReadParamDialog(wx.Dialog):
    #----------------------------------------------------------------------
    def __init__(self,param_dict):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="Entre com os parametros para a consulta")

        # Destroy componentes anteriores
        for child in self.GetChildren():
            child.Destroy()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.textCtrls=collections.OrderedDict()

        for key in param_dict.keys():
            label = wx.StaticText(self, wx.ID_ANY, key)
            if "\n" in param_dict[key]:
                self.textCtrls[key]=wx.TextCtrl(self, wx.ID_ANY,
                                                style=wx.TE_MULTILINE,
                                                value=param_dict[key])
            else:
                self.textCtrls[key] = wx.TextCtrl(self, wx.ID_ANY,
                                                  param_dict[key])
            self.textCtrls[key].Bind(wx.EVT_KEY_UP, self.OnKeyUp)

            sizer= wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(label,0, wx.ALL|wx.ALIGN_RIGHT, 5)
            sizer.Add(self.textCtrls[key],1, wx.ALIGN_RIGHT, 5)
            main_sizer.Add(sizer,0,wx.EXPAND,5)

        # Bottom sizer (buttons)
        bottom_sizer= wx.BoxSizer(wx.HORIZONTAL)
        okBtn = wx.Button(self, wx.ID_OK)
        clBtn = wx.Button(self, wx.ID_CANCEL)

        bottom_sizer.Add(okBtn, 0, wx.ALL|wx.CENTER, 5)
        bottom_sizer.Add(clBtn, 0, wx.ALL|wx.CENTER, 5)
        main_sizer.Add(bottom_sizer,0,wx.EXPAND,5)

        #The main sizer
        self.SetSizer(main_sizer)

    def OnKeyUp(self, event):
        """ KeyUp comes last """
        event.Skip()
 
               
class ConfigPanel(wx.Panel):
    def __init__(self, parent, config_dict):
        wx.Panel.__init__(self, parent, -1)

        self.textCtrls={}
        if config_dict:
           self.SetConfig(config_dict)


    def GetConfig(self):
        new_config={}
        for key in self.textCtrls.keys():
            new_config[key]=self.textCtrls[key].GetValue()
        return new_config

    def SetConfig(self, config_dict):
        """ config_dict vem na forma { 'atributo' : valor  ... }
            Eh criado um TextCtrl para cada atributo e o texto
            eh setado com o valor correspondente
        """
        # Destroy componentes anteriores
        for child in self.GetChildren():
            child.Destroy() 
 
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.textCtrls={}
        for key in config_dict.keys():
            if key=='sql_query':
                continue
            label = wx.StaticText(self, wx.ID_ANY, key)
            if "\n" in config_dict[key]:
                self.textCtrls[key]=wx.TextCtrl(self, wx.ID_ANY,
                                                style=wx.TE_MULTILINE, 
                                                value=config_dict[key])
            else:
                self.textCtrls[key] = wx.TextCtrl(self, wx.ID_ANY, 
                                                  config_dict[key])
            self.textCtrls[key].Bind(wx.EVT_KEY_UP, self.OnKeyUp)

            sizer= wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(label,0, wx.ALL|wx.ALIGN_RIGHT, 5)
            sizer.Add(self.textCtrls[key],1, wx.ALIGN_RIGHT, 5)
            main_sizer.Add(sizer,0,wx.EXPAND,5)
        self.SetSizer(main_sizer)
        self.Layout()

    def OnKeyUp(self, event):
        """ KeyUp comes last """
        wx.PostEvent(self, ChangedEvent(self.GetId()))
        event.Skip()


class MyNotebook(wx.Notebook):
    def __init__(self, parent):
	super(MyNotebook, self).__init__(parent)

	#Attributes
	self.edt = CodeEditorBase(self)
        #self.edt.SetLexer(stc.STC_LEX_SQL)
        #self.edt.Colourise(0, self.edt.GetTextLength())
        #self.edt.SetProperty('fold','1')
        self.edt.SetKeyWords(0,"SELECT FROM WHERE")
	self.log = wx.TextCtrl(self,
				    value="Starting log",
				    style=wx.TE_MULTILINE)
        self.cfg = ConfigPanel(self,{})
        #self.out = OutputGrid(self)
        self.out = TestVirtualList(self,[], {})
        # redirect text here
        #sys.stdout=self.log
        #sys.stderr=self.log

	# Setup
	self.AddPage(self.edt, "Text Editor")
	self.AddPage(self.log, "Activity Log")
	self.AddPage(self.cfg, "Configuration")
	self.AddPage(self.out,"Data output")

class TopPanel(wx.Panel):
    def __init__(self, parent):
	wx.Panel.__init__(self, parent, -1)

	
	sizer = wx.BoxSizer(wx.HORIZONTAL)
        bmp_path = AddAppPath("hourglass_run.png")
	bmp=wx.Bitmap(bmp_path, wx.BITMAP_TYPE_ANY)
	#bmp=wx.Bitmap("stopwatch_run.png", wx.BITMAP_TYPE_ANY)
        #button = AB.AquaButton(self, bitmap=bmp, label="Run")
        #button = GB.GradientButton(self, bitmap=bmp, label="Run")
        button = wx.BitmapButton(self, bitmap=bmp)

        button.SetBitmap(bmp,wx.TOP)
        self.Refresh()
	sizer.Add(button)
	button.Bind(wx.EVT_BUTTON, self.OnButton)
	
	self.SetSizer(sizer)
	
	
    def OnButton(self, event):
        event.Skip()

ID_READ_ONLY = wx.NewId()

class MainFrame(wx.Frame):
    def writeLog(self, mensagem):
        self.nbk.log.AppendText(mensagem+"\n");
        #Manda tambem para stdout
        print mensagem
        
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
         self.StatusBar.SetFieldsCount(2)
         self.StatusBar.SetStatusWidths([-4,-1]) #Relative widths
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
         self.Bind(stc.EVT_STC_MODIFIED, self.OnModifyQuery)
         self.Bind(stc.EVT_STC_UPDATEUI, self.OnPosChanged)

         self.nbk.edt.EnableLineNumbers()

         #print 'After Line Numbers'
         if filename:
             self.LoadFromFile(filename)
         else:
             self.cyx = CsvAnywhere(filename)
             #SetConfig

    def OnPosChanged(self,event):
        edt=self.nbk.edt
        pos=edt.GetCurrentPos()
        pos_tuple=(edt.GetColumn(pos)+1,edt.LineFromPosition(pos)+1)
        self.StatusBar.SetStatusText("C=%d,L=%d" % pos_tuple,1)

    def OnModifyQuery(self,event):
        self.menub.Enable(wx.ID_SAVE,True)

    def OnButton(self, event):
        if self.cyx.param_names :
          params = collections.OrderedDict()
          for k in self.cyx.param_names:
              params[k]=''
              #print k
          self.writeLog("Lendo parametros");
          #print params
          dlg = ReadParamDialog(params)
          res=dlg.ShowModal()
          self.cyx.param_values=[]
          if res== wx.ID_OK:
              for key in dlg.textCtrls:
                  self.cyx.param_values+=[dlg.textCtrls[key].GetValue()] 
          dlg.Destroy()
          if res != wx.ID_OK:
            return 
        
	btn = event.GetEventObject()
        btn.Enabled=False
        
        try:
          sav_sql=self.cyx.sql_query
          new_sql=self.nbk.edt.GetText()
          ini,fim = self.nbk.edt.GetSelection()
          if ini != fim: 
            new_sql=self.nbk.edt.GetSelectedText()

          self.cyx.sql_query=new_sql
          
          self.writeLog("Conectando ao banco...")
          self.cyx.connect_db()
          self.writeLog("Executando query...")
          rows=self.cyx.execute_query()
          
          self.writeLog("Preenchendo grid...")
          self.nbk.out.AddHeader(self.cyx.columns)
          self.nbk.out.AddRows(rows)
        except:
            self.writeLog("ERRO:\n "+traceback.format_exc())
          
        finally:
          btn.Enabled=True
          event.Skip()


    def LoadFromFile(self, fname):
        self.cyx=CsvAnywhere(fname)
        self.nbk.edt.SetText(self.cyx.sql_query)
        self.nbk.cfg.SetConfig(self.cyx.get_config())	 
	self.SetStatusText(fname,0)
	self.SetStatusText("l1,c1",1)
        self.nbk.edt.Colourise(0, self.nbk.edt.GetTextLength())
 
        

    def SaveToFile(self):
        new_config=self.nbk.cfg.GetConfig()
        self.cyx.set_config(new_config)
        self.cyx.sql_query=self.nbk.edt.GetText()
        self.cyx.write_config(self.cyx.filename)
        self.menub.Enable(wx.ID_SAVE,False)

    def OnConfigChanged(self,event):
        self.menub.Enable(wx.ID_SAVE,True)
        


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
        elif evt_id == wx.ID_SAVEAS:
            dlg = wx.FileDialog(self, "Salvar arquivo como...", 
                                os.getcwd(), "", "*.cyx", \
                    wx.SAVE|wx.OVERWRITE_PROMPT)
            result = dlg.ShowModal()
            fname = dlg.GetPath()
            dlg.Destroy()

            if result == wx.ID_OK:          #Save button was pressed
                self.cyx.filename=fname
                self.SaveToFile()
        else:
           event.Skip()

def main(parser):
  parser.add_argument("filename",nargs='?',default='',help="arquivo do tipo CYX (consulta odbc e exportacao)")
  args = parser.parse_args()

  #print 'args'
  app = wx.App(False)
  #print 'app'
  win = MainFrame(args.filename)
  #print 'MainFrame'
  win.Show(True)
  #print 'Show'
  app.MainLoop()
  #print 'MainLoop'
  
    

if __name__=="__main__":
  parser = argparse.ArgumentParser()
  try:
    #print 'main'
    main(parser) 
  except:
    mensagem="ERRO:\n "+traceback.format_exc()
    wx.MessageBox(mensagem,caption='Erro', style=wx.OK| wx.ICON_INFORMATION)
    traceback.print_exc(file=sys.stdout)
    print "Pressione qualquer tecla para continuar..."
    stdin.readline().rstrip("\n") 
