import wx
import wx.grid as gridlib
import wx.stc as stc
import keyword
from csva import *

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


class BaseList(wx.ListCtrl):

      def __init__(self, parent):

          super(BaseList, self).__init__(parent,
                                         style=wx.LC_REPORT)


class OutputGrid(BaseList):
    def __init__(self,parent):
        super(OutputGrid,self).__init__(parent)
    
    def addHeader(self,header_list):
        """ Add column headers """
        i=0
        for name in header_list:
            self.InsertColumn(i,name)
            i+=1
            
    def addRow(self, row_as_a_list ):
        """ Adds a row to the grid """
        item = self.Append(tuple(row_as_a_list))
               
class MyNotebook(wx.Notebook):
    def __init__(self, parent):
	super(MyNotebook, self).__init__(parent)

	#Attributes
	self.edt = CodeEditorBase(self)
	self.log = wx.TextCtrl(self,
				    value="The log",
				    style=wx.TE_MULTILINE)


        font1 = wx.Font(10, wx.MODERN, wx.NORMAL, 
                        wx.NORMAL, False, u'Andale Mono')

	self.out = wx.TextCtrl(self,
				  style=wx.TE_MULTILINE|wx.HSCROLL)
        self.out.SetFont(font1)
       
        self.out2 = OutputGrid(self)

	# Setup
	#self.AddPage(self.textctrl, "Text Editor")
	self.AddPage(self.edt, "Text Editor")
	self.AddPage(self.log, "Activity Log")
	self.AddPage(self.out,"Data output")
	self.AddPage(self.out2,"Data output 2")

class TopPanel(wx.Panel):
    def __init__(self, parent):
	wx.Panel.__init__(self, parent, -1)

	
	sizer = wx.BoxSizer(wx.HORIZONTAL)


	btn = wx.Button(self, -1, 'Executar')
	sizer.Add(btn, 1, wx.TOP|wx.BOTTOM, 15)
	btn.Bind(wx.EVT_BUTTON, self.OnButton)
	
	self.SetSizer(sizer)
	
	
    def OnButton(self, event):
        event.Skip()

ID_READ_ONLY = wx.NewId()

class MainFrame(wx.Frame):
     
    def __init__(self):
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
	 self.SetSize((400, 300))
	 
	 # Setup the Menu
	 menub = wx.MenuBar()

	 # File Menu
	 filem = wx.Menu()
	 filem.Append(wx.ID_OPEN,"&Abrir\tCtrl+O")
	 filem.Append(wx.ID_SAVE,"&Salvar\tCtrl+S")
	 filem.Append(wx.ID_SAVEAS,"Salvar &como\tShift+Ctrl+S")
	 menub.Append(filem,"&Arquivo")

	 # Edit Menu
	 editm = wx.Menu()
	 editm.Append(wx.ID_COPY,"Copiar\tCtrl+C")
	 editm.Append(wx.ID_CUT,"Cortar\tCtrl+X")
	 editm.Append(wx.ID_PASTE,"Colar\tCtrl+V")
	 editm.AppendSeparator()
	 editm.Append(ID_READ_ONLY,"Read Only",
		      kind=wx.ITEM_CHECK)
	 menub.Append(editm,"E&ditar")

 
	 self.SetMenuBar(menub)

	 #Event Handler
	 self.Bind(wx.EVT_MENU,self.OnMenu)  
         self.Bind(wx.EVT_BUTTON, self.OnButton)

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
          self.nbk.out2.addHeader(self.cyx.columns)
          for row in rows:
              self.nbk.out2.addRow(row)
          self.nbk.out.Clear()
          for linha in self.cyx.tabularize_it(rows):
            self.nbk.out.AppendText(linha+"\n")
        finally:
          btn.Enabled=True
	 
    def LoadFromFile(self, fname):
        self.cyx=CsvAnyware(fname)
        self.nbk.edt.SetText(self.cyx.sql_query)
        

    def SaveToFile(self):
        self.cyx.sql_query=self.nbk.edt.GetText()
        self.cyx.write_config(self.cyx.filename)

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
	       self.PushStatusText(fname)
        else:
           event.Skip()
if __name__=="__main__":
     app = wx.App(False)
     win = MainFrame()
     win.Show(True)
     app.MainLoop()
