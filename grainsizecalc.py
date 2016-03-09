#################################################################################################################
## CHaMP Grain Size Distribution Calculation - GUI
## James Hensleigh - Hensleigh.ride@gmail.com
##
## The purpose of this script is to take in a either a CHAMP CHANNELUNIT*.csv or a CHAMP PEBBLE_CHAMP*.csv file and 
## calculate the grain size distribution for the file. Specifically the D16, D50, and D84.
##
## For a CHANNELUNIT file the grain size distribution is calculated for each line in the file.
## For a PEBBLE_CHAMP file the grain size distribution is calculated for the entire file.
#################################################################################################################
#!/usr/bin/env python

import wx, os, math, numpy, sys, glob

upperBoundsCHANNEL = [0.06, 2, 16, 64, 255, 256, 4000]
upperBoundsPEBBLE = [0.06, 2, 5.7, 8, 11.3, 16, 22.5, 32, 45, 64, 90, 128, 180, 256, 362, 512]

def Di(x1, x2, y1, y2, i):
    '''Calculates the Dx for a given grain size distribution'''
    return math.pow(10,((math.log(x2, 10) - math.log(x1, 10)) * ((i - float(y1))/(y2 - y1)) + math.log(x1, 10)))

def processChannelFile(grainFile, ):
    with open(grainFile, 'r') as file:
        file.readline()
        for line in file:

            if 'D16' in locals():
                del D16

            if 'D50' in locals():
                del D50

            if 'D84' in locals():
                del D84

            sub = [int(i.strip('\"')) for i in line.strip().split(',')[22:29]]
            sub.reverse()
            cumSum = list(numpy.cumsum(sub))
            ct = 0
            for i in cumSum:
                if ct + 1 > len(cumSum):
                    break

                if 'D84' in locals():
                    break

                if ct == 0 and i > 16:
                    D16 = 0.06
                    print 'D16 is {0}'.format(D16)

                    if ct == 0 and i > 50:
                        D50 = 0.06
                        print 'D50 is {0}'.format(D50)
                        ct += 1
                        continue

                    elif 50 in range(cumSum[ct], cumSum[ct + 1]):
                        D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSum[ct], cumSum[ct + 1], 50)
                        print 'D50 is {0}'.format(D50)
                        ct += 1
                        continue

                    else:
                        ct += 1

                if i < 16 and cumSum[ct + 1] < 16:
                    ct += 1
                    continue

                elif 16 in range(cumSum[ct], cumSum[ct + 1]) and 50 in range(cumSum[ct], cumSum[ct + 1]) and 84 in range(cumSum[ct], cumSum[ct + 1]):

                    if 'D16' in locals():
                        ct += 1
                        continue

                    if 'D50' in locals():
                        ct += 1
                        continue

                    if 'D84' in locals():
                        ct += 1
                        continue

                    D16 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 16)
                    D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 50)
                    D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 84)
                    print 'D16 is {0}'.format(D16)
                    print 'D50 is {0}'.format(D50)
                    print 'D84 is {0}\n'.format(D84)
                    ct += 1
                    break

                elif 16 in range(cumSum[ct], cumSum[ct + 1]) and 50 in range(cumSum[ct], cumSum[ct + 1]):

                    if 'D16' in locals() and 'D50' in locals():
                        ct += 1
                        continue

                    D16 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 16)
                    D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 50)
                    print 'D16 is {0}'.format(D16)
                    print 'D50 is {0}'.format(D50)
                    ct += 1
                    continue

                elif 50 in range(cumSum[ct], cumSum[ct + 1]) and 84 in range(cumSum[ct], cumSum[ct + 1]):

                    if 'D50' in locals() and 'D84' in locals():
                        ct += 1
                        continue

                    D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 50)
                    D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 84)
                    print 'D50 is {0}'.format(D50)
                    print 'D84 is {0}\n'.format(D84)
                    ct += 1
                    continue

                elif 16 in range(cumSum[ct], cumSum[ct + 1]):

                    if 'D16' in locals():
                        ct += 1
                        continue
    
                    D16 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 16)
                    print 'D16 is {0}'.format(D16)
                    ct += 1
                    continue

                elif 50 in range(cumSum[ct], cumSum[ct + 1]):

                    if 'D50' in locals():
                        ct += 1
                        continue
    
                    D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 50)
                    print 'D50 is {0}'.format(D50)
                    ct += 1
                    continue

                elif 84 in range(cumSum[ct], cumSum[ct + 1]):

                    if 'D84' in locals():
                        ct += 1
                        continue
    
                    D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSum[ct], cumSum[ct+1], 84)
                    print 'D84 is {0}\n'.format(D84)
                    ct += 1
                    break

                else:
                    ct += 1

def processPebbleFile(grainFile):

    pebbCount = [['0.02 - 0.06mm', 0],
            ['0.06 - 2mm' ,0],
            ['4 - 5.7mm' ,0],
            ['5.7 - 8mm' ,0],
            ['8 - 11.3mm' ,0],
            ['11.3 - 16mm' ,0],
            ['16 - 22.5mm' ,0],
            ['22.5 - 32mm' ,0],
            ['32 - 45mm' , 0],
            ['45 - 64mm' , 0],
            ['64 - 90mm' ,0],
            ['90 - 128mm' , 0],
            ['128 - 180mm' ,0],
            ['180 - 256mm' , 0],
            ['256 - 362mm' ,0],
            ['362 - 512mm' ,0]]
    
    if 'D16' in locals():
        del D16

    if 'D50' in locals():
        del D50

    if 'D84' in locals():
        del D84

    with open(grainFile, 'r') as file:
        file.readline()
        for line in file:
            sub = [i.strip('\"') for i in line.strip().split(',')][15]
            for i in pebbCount:
                if i[0] == sub:
                    i[1] += 1

    count = []
    for i in pebbCount:
        count.append(i[1])

    percent = [round(i/float(sum(count)),3) for i in count]
    cumSum = list(numpy.cumsum(percent) * 100)
    cumSum = [int(i) for i in cumSum]

    ct = 0
    for i in cumSum:
        if ct + 1 > len(cumSum):
            break

        if 'D84' in locals():
            break

        if ct == 0 and i > 16:
            D16 = "< 0.06"
            print 'D16 is {0}'.format(D16)

            if ct == 0 and i > 50:
                D50 = "< 0.06"
                print 'D50 is {0}'.format(D50)
                ct += 1
                continue

            elif 50 in range(cumSum[ct], cumSum[ct + 1]):
                D50 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct + 1], cumSum[ct], cumSum[ct + 1], 50)
                print 'D50 is {0}'.format(D50)
                ct += 1
                continue

            else:
                ct += 1

        if i < 16 and cumSum[ct + 1] < 16:
            ct += 1
            continue

        elif 16 in range(cumSum[ct], cumSum[ct + 1]) and 50 in range(cumSum[ct], cumSum[ct + 1]) and 84 in range(cumSum[ct], cumSum[ct + 1]):

            if 'D16' in locals():
                ct += 1
                continue

            if 'D50' in locals():
                ct += 1
                continue

            if 'D84' in locals():
                ct += 1
                continue

            D16 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 16)
            D50 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 50)
            D84 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 84)
            print 'D16 is {0}'.format(D16)
            print 'D50 is {0}'.format(D50)
            print 'D84 is {0}\n'.format(D84)
            ct += 1
            break

        elif 16 in range(cumSum[ct], cumSum[ct + 1]) and 50 in range(cumSum[ct], cumSum[ct + 1]):

            if 'D16' in locals() and 'D50' in locals():
                ct += 1
                continue

            D16 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 16)
            D50 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 50)
            print 'D16 is {0}'.format(D16)
            print 'D50 is {0}'.format(D50)
            ct += 1
            continue

        elif 50 in range(cumSum[ct], cumSum[ct + 1]) and 84 in range(cumSum[ct], cumSum[ct + 1]):

            if 'D50' in locals() and 'D84' in locals():
                ct += 1
                continue

            D50 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 50)
            D84 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 84)
            print 'D50 is {0}'.format(D50)
            print 'D84 is {0}\n'.format(D84)
            ct += 1
            continue

        elif 16 in range(cumSum[ct], cumSum[ct + 1]):

            if 'D16' in locals():
                ct += 1
                continue
                    
            D16 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 16)
            print 'D16 is {0}'.format(D16)
            ct += 1
            continue

        elif 50 in range(cumSum[ct], cumSum[ct + 1]):

            if 'D50' in locals():
                ct += 1
                continue
                    
            D50 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 50)
            print 'D50 is {0}'.format(D50)
            ct += 1
            continue
                
        elif 84 in range(cumSum[ct], cumSum[ct + 1]):

            if 'D84' in locals():
                ct += 1
                continue
                    
            D84 = Di(upperBoundsPEBBLE[ct], upperBoundsPEBBLE[ct+1], cumSum[ct], cumSum[ct+1], 84)
            print 'D84 is {0}\n'.format(D84)
            ct += 1
            break

        else:
            ct += 1
    


def basicErrorHandle(self):
    '''Provides basic error handling for the try except statements of each event handling function.'''
    dlg = wx.MessageDialog(self,'An error has occured!!.\n Consider these errors:\n {0}'.format(sys.exc_info()[1]),
                                'Error!!', wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy() 

class Frame(wx.Frame):
    '''Defines the main frame for the GUI'''
    def __init__(self, parent, id, title, pos, size):
        wx.Frame.__init__(self, parent, id, title, pos,  size)
        self.dirname = ''
        self.CreateStatusBar()
        self.createMenuBar()

        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour('White')

        self.createButtons(panel)

        
    def createMenuBar(self):
        #Set up File menu
        fileMenu = wx.Menu()
        menuOpen = fileMenu.Append(wx.ID_OPEN, '&Open', ' Open a file to edit')
        menuAbout = fileMenu.Append(wx.ID_ABOUT, '&About', ' Information about this program')
        fileMenu.AppendSeparator()
        menuExit = fileMenu.Append(wx.ID_EXIT, 'E&xit', ' Terminate the program')        

        #Set up Help menu
        helpMenu = wx.Menu()
        menuHelp = helpMenu.Append(wx.ID_HELP, '&Help', ' Links to help documentation')

        #Actually create the menubar
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, '&File')
        menuBar.Append(helpMenu, '&Help')
        self.SetMenuBar(menuBar)

    def createButtons(self, panel):
        b1 = wx.Button(panel, -1, 'Calculate grain size distribution for one file', pos = (25, 35))
        b1.SetDefault()
        b1.Enable(True)

        b2 = wx.Button(panel, -1, 'Calculate grain size distribution for multiple files', pos = (25, 75))
        b2.SetDefault()
        b2.Enable(True)
        
        b3 = wx.Button(panel, -1, 'Grain Size Distribution for One Pebble Count File', pos = (25, 115))
        b3.SetDefault()
        b3.Enable(True)

        b4 = wx.Button(panel, -1, 'Grain Size Distribution for Multiple Pebble Count File', pos = (25, 155))
        b4.SetDefault()
        b4.Enable(True)

        b5 = wx.Button(panel, -1, 'Grain Size Distribution BATCH CALCULATION', pos = (25, 195))
        b5.SetDefault()
        b5.Enable(False)

        
        #Event handling for buttons
        self.Bind(wx.EVT_BUTTON, self.onCalcOneFileCHANNEL, b1)
        self.Bind(wx.EVT_BUTTON, self.onCalcMultFilesCHANNEL, b2)
        self.Bind(wx.EVT_BUTTON, self.onCalcOneFilePEBBLE, b3)
        self.Bind(wx.EVT_BUTTON, self.onCalcMultFilesPEBBLE, b4)
        

    #Define Event Handling

    def onCalcOneFileCHANNEL(self, event):
        try:
            fileDlg = wx.FileDialog(self, 'Choose a file', self.dirname, "", "*.csv", wx.OPEN)
            if fileDlg.ShowModal() == wx.ID_OK:
                self.filename = fileDlg.GetFilename()
                self.dirname = fileDlg.GetDirectory()
                grainFile = os.path.join(self.dirname, self.filename)
                processChannelFile(grainFile)
        except:
            basicErrorHandle(self)


    def onCalcMultFilesCHANNEL(self, event):
        try:
            folderDlg = wx.DirDialog(self, 'Choose a directory', style = wx.DD_DEFAULT_STYLE)
            if folderDlg.ShowModal() == wx.ID_OK:
                dirWalk = os.walk(folderDlg.GetPath())
                for i in dirWalk:
                    files = glob.glob(i[0] + '\\CHANNELUNIT_CHAMP*.csv')
                    for j in files:
                        try:
                            sys.stdout.write(j + '\n\n')#
                            processChannelFile(j)
                        except:
                            basicErrorHandle(self)
            folderDlg.Destroy()
        except:
            basicErrorHandle(self)

    def onCalcOneFilePEBBLE(self, event):
        try:
            fileDlg = wx.FileDialog(self, 'Choose a file', self.dirname, "", "*.csv", wx.OPEN)
            if fileDlg.ShowModal() == wx.ID_OK:
                self.filename = fileDlg.GetFilename()
                self.dirname = fileDlg.GetDirectory()
                grainFile = os.path.join(self.dirname, self.filename)
                processPebbleFile(grainFile)
        except:
            basicErrorHandle(self)


    def onCalcMultFilesPEBBLE(self, event):
        try:
            folderDlg = wx.DirDialog(self, 'Choose a directory', style = wx.DD_DEFAULT_STYLE)
            if folderDlg.ShowModal() == wx.ID_OK:
                dirWalk = os.walk(folderDlg.GetPath())
                for i in dirWalk:
                    files = glob.glob(i[0] + '\\PEBBLE_CHAMP*.csv')
                    for j in files:
                        try:
                            sys.stdout.write(j + '\n\n')#
                            processPebbleFile(j)
                        except:
                            basicErrorHandle(self)
            folderDlg.Destroy()
        except:
            basicErrorHandle(self)

class App(wx.App):
    '''Main application class, helps to handle error messages through stdout'''
    def __init__(self, redirect = True, filename = None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = Frame(parent = None, id = -1, title = 'Easy Grain Size Distribution Calculator',
                           pos = wx.DefaultPosition, size = (650, 650))
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

    def OnExit(self):
        pass

if __name__ == '__main__':
    app = App(redirect = True)
    app.MainLoop()
