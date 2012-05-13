
##############################################################################
# EVEscan GUI
# tkinter - python multiplatform tk/tcl interface
#
#   - File Menu Bar
#       * prefs, archive, imp, exp, quit
#   - To/From drop down
#       * TODO: auto-update
#   - Manual To/From button region update button
#   - Force Regions check box
#   - Scan button
#   - Auto Scan button
#   - Threshold sliders w/ entry for maximum
#       * print, cargo, capital, sec status
#   - Entry for text log threshold
#   - Path selection entry/button for log files
#
# TODO : update to work with Python 3.1 and ttk or tix
#   - better, more modern look and feel
#   - access to wider range of widgets
##############################################################################

from Tkinter import *
# import EVEscan library
import EVEscan, sortableMultiListbox as sml



# digest containing current user control values
class controlsDigest:
    def __init__(self):
        self.EVElog = EVE_logs.get()
        self.textlog = logpath.get()
        self.force_regions = force_regions.get()
        self.log_thresh = log_thresh.get()
        self.print_thresh = print_thresh.get()
        self.cargo_thresh = cargo_thresh.get()
        self.capital_thresh = capital_thresh.get()
        self.to_region = tovar.get()
        self.from_region = fromvar.get()
        self.security_thresh = security_thresh.get()
        self.speculate = speculate.get()
        self.invest = invest.get()

# multipurpose popup window function
def window(option):
    top = Toplevel()
    if option == 'prefs':
        top.title("Preferences")
        msg = Message(top, text="This is the preference pane")
    elif option == 'import':
        top.title("Import")
        msg = Message(top, text="This is the import pane")
    elif option == 'export':
        top.title("Export")
        msg = Message(top, text="This is the export pane")
    elif option == 'about':
        top.title("About...")
        msg = Message(top, text="Copyright (C) 2010 Matt Shockley \
                                \nSend all mail to /dev/null")
    elif option == 'version':
        top.title("Version " + EVEscan.getversion())
        msg = Message(top, text="Still under development. \
                                \nNot yet for public use.")
    elif option == 'archive':
        top.title("Archive Market Logs...")
        msg = Message(top, text=EVEscan.archiveLogs(EVE_logs.get()))
    msg.pack()
    button = Button(top, text="OK", command=top.destroy)
    button.pack()


# scan button callback
def scan():
    displayListbox.delete(0,END)
    if not scan_cache.get():
        for line in EVEscan.scan(controlsDigest()):
            displayListbox.insert(END,line)
        if auto_scan.get():
            displayListbox.after(6000, lambda: scan())
    else:
        for line in EVEscan.scan_cache(controlsDigest()):
            displayListbox.insert(END,line)
        if auto_scan.get():
            displayListbox.after(6000, lambda: scan())

# refresh slider controls for thresholds
def update_scale(scale,top):
    scale.config(to = top.get())
    scale.after(1000, lambda: update_scale(scale,top))

# refresh region menus
#   - TODO: don't refresh when menu receives focus
def update_region(optionMenu,logpath, var):
    regions = EVEscan.getRegions(logpath.get())
    #var.set(regions[0])
    temp = var.get()

    m = optionMenu.children['menu']
    m.delete(0,END)

    for region in regions:
        m.add_command(label = region, command = lambda v = var, l = region: v.set(l))
    #var.set(regions[0])
    var.set(temp)
    #optionMenu.after(1000, lambda: update_region(optionMenu,logpath,var))
    
def update_regions(fromRegionMenu, toRegionMenu, fromvar, tovar):
    update_region(fromRegionMenu, EVE_logs, fromvar)
    update_region(toRegionMenu, EVE_logs, tovar)

# exit program callback
def exit_prog():
    root.destroy()
    root.quit()
    

# Tk GUI
root = Tk()
EVEscan.setTitleVersion(root)



# create menu bar
menu = Menu(root)
root.config(menu = menu)

# file menu
filemenu = Menu(menu)
menu.add_cascade(label = "File", menu = filemenu)
filemenu.add_command(label = "Preferences", command = lambda: window('prefs'))
filemenu.add_command(label = "Archive", command = lambda: window('archive'))
filemenu.add_command(label = "Import...", command = lambda: window('import'))
filemenu.add_command(label = "Export...", command = lambda: window('export'))
filemenu.add_command(label = "Exit", command = exit_prog)
# help menu
helpmenu = Menu(menu)
menu.add_cascade(label = "Help", menu = helpmenu)
helpmenu.add_command(label = "About", command = lambda: window('about'))
helpmenu.add_command(label = "Version", command = lambda: window('version'))

# create grid geometry and populate
#   adjust app height and width
#   widgets resize accordingly
app_height = 37
app_width = 135
rightp_height = app_height 
rightp_width =  int(.6 * app_width)
leftp_height = app_height
leftp_width = int(.4 * app_width)
logp_height = int(.2 * leftp_height)
logp_width = leftp_width
scanp_height = int(.2 * leftp_height)
scanp_width = leftp_width
sliderp_height = int(.4 * leftp_height)
sliderp_width = leftp_width
displayp_height = int(.9 * rightp_height)
displayp_width =  int(.9 * rightp_width)
regionp_height = int(.2 * leftp_height)
regionp_width = leftp_width

masterFrame = Frame(root, height = app_height , width = app_width)
masterFrame.pack()

leftFrame = Frame(masterFrame, height = leftp_height, width = leftp_width)
leftFrame.pack(side = LEFT, ipadx = 10, ipady = 10)
rightFrame = Frame(masterFrame, height = rightp_height, width = .7 * rightp_width, bd = 1, relief = SUNKEN)
rightFrame.pack(side = RIGHT, padx = 10, pady = 10, fill=Y)

scanFrame = Frame(leftFrame, height = scanp_height, width = scanp_width)
scanFrame.pack(pady = 5)
logFrame = Frame(leftFrame, height = logp_height, width = logp_width)
logFrame.pack(pady = 10)



# log paths interface
EVE_logs = StringVar()
logpath = StringVar()
EVEscan.setlogs(EVE_logs,logpath)

Label(logFrame, text = "EVE Market Log Path").grid(row = 0, column = 0, columnspan = 3)
Label(logFrame, text = "Text Log Path").grid(row = 2, column = 0, columnspan = 3)
Entry(logFrame, textvariable = EVE_logs, state = "readonly").grid(row = 1, column = 0, columnspan = 2)
Entry(logFrame, textvariable = logpath, state = "readonly").grid(row = 3, column = 0, columnspan = 2)
Button(logFrame, text = "Browse", command =  lambda: EVEscan.select_path(EVE_logs)).grid(row = 1, column = 2)
Button(logFrame, text = "Browse", command =  lambda: EVEscan.select_path(logpath)).grid(row = 3, column = 2)

# to/from region selection drop down menus
regionFrame = Frame(scanFrame, height = regionp_height, width = regionp_width)
regionFrame.pack(pady = 5)

regions = EVEscan.getRegions(EVE_logs.get())
regions.insert(0,"Any")
tovar = StringVar()
fromvar = StringVar()
tovar.set(regions[0])
fromvar.set(regions[0])
Label(regionFrame, text = "From").grid(row = 0, column = 0)
fromRegionMenu = OptionMenu(regionFrame, fromvar, *regions)
fromRegionMenu.grid(row = 0, column = 1)
#update_region(fromRegionMenu, EVE_logs, fromvar)
Label(regionFrame, text = "To").grid(row = 1, column = 0)
toRegionMenu = OptionMenu(regionFrame, tovar, *regions)
toRegionMenu.grid(row = 1, column = 1)
#update_region(toRegionMenu, EVE_logs, tovar)

# update regions button
Button(regionFrame, text = "Update Regions", command = lambda: update_regions(fromRegionMenu, toRegionMenu, fromvar, tovar)).grid(row = 2, column = 0, columnspan = 2)

# scan cache checkbox
scan_cache = BooleanVar()
Checkbutton(scanFrame, text = "Scan Cache", variable = scan_cache).pack()

# speculate trades
speculate = BooleanVar()
Checkbutton(scanFrame, text = "Speculate", variable = speculate).pack()

invest = BooleanVar()
Checkbutton(scanFrame, text = "Invest", variable = invest).pack()

# force regions checkbox
force_regions = BooleanVar()
Checkbutton(scanFrame, text = "Force Regions", variable = force_regions).pack()

# auto scan
auto_scan = BooleanVar()
Checkbutton(scanFrame, text = "Auto Scan", variable = auto_scan).pack()

# scan button
Button(scanFrame, text = "Scan", command = scan).pack()


# threshold sliders
sliderFrame = Frame(scanFrame, height = sliderp_height, width = sliderp_width, bd = 1, relief = SUNKEN)
sliderFrame.pack(pady = 50, ipady = 15, ipadx = 15)

Label(sliderFrame, text = "Thresholds", font = ("DEFAULT", 12)).pack()

print_thresh = DoubleVar()
print_top = DoubleVar()
print_top.set(1e6)
printScale = Scale(sliderFrame, from_ = 0, to = print_top.get(), orient = HORIZONTAL, length = 100, variable = print_thresh)
printScale.pack()
update_scale(printScale,print_top)
Entry(sliderFrame, textvariable = print_top).pack()
Label(sliderFrame, text = "Print").pack()

cargo_thresh = DoubleVar()
cargo_top = DoubleVar()
cargo_top.set(1e6)
cargoScale = Scale(sliderFrame, from_ = 0, to = cargo_top.get(), orient = HORIZONTAL, length = 100, variable = cargo_thresh)
cargoScale.pack()
update_scale(cargoScale, cargo_top)
Entry(sliderFrame, textvariable = cargo_top).pack()
Label(sliderFrame, text = "Cargo").pack()

capital_thresh = DoubleVar()
capital_top = DoubleVar()
capital_top.set(1e6)
capitalScale = Scale(sliderFrame, from_ = 0, to = capital_top.get(), orient = HORIZONTAL, length = 100, variable = capital_thresh)
capitalScale.pack()
update_scale(capitalScale, capital_top)
Entry(sliderFrame, textvariable = capital_top).pack()
Label(sliderFrame, text = "Capital").pack()

security_thresh = DoubleVar()
security_thresh.set(.5)
Entry(sliderFrame, textvariable = security_thresh).pack()
Label(sliderFrame, text = "Security").pack()

hz = Frame(sliderFrame, bd = 1, height = 2, relief = RAISED)
hz.pack(side = TOP, expand = 1, fill = X, pady = 10, padx = 10)

log_thresh = DoubleVar()
log_thresh.set(0)
Entry(sliderFrame, textvariable = log_thresh).pack()
Label(sliderFrame, text = "Text Log").pack()

# text display
#scrollbar = Scrollbar(rightFrame)
#scrollbar.pack(side=RIGHT, fill=Y)
#displayListbox = Listbox(rightFrame, width = displayp_width, height = 100, bg = "white", yscrollcommand = scrollbar.set)

# MultiListbox
displayListbox = sml.MultiListbox(rightFrame, (('Item Type',40),('Profit',10),('Cargo Eff.', 10), ('Cap. Eff.', 10), ('Buy Region',15), ('Sell Region',15),('Buy System',20),('Sell System',20),('Buy',10),('Sell',10),('Capital',10),('Volume',10),('Quantity',10)))

displayListbox.pack(expand=YES,fill=BOTH)
#scrollbar.config(command = displayListbox.yview)

root.mainloop()
