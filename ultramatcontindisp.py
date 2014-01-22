#!/usr/bin/python3
# -*- coding: utf8 -*-

import ultramat
from tkinter import *
import mdbase

SERIALNAME = "/dev/ttyUSB0"
DBNAME = "/home/pi/ultrapy.db"
LOGDATA = False

class UltramatContinDisp:
    def __init__(self, title):
        self.database = None
        self.makeGui(title)
        self.loaded()


    def makeGui(self, title):
        self.root = Tk()
        self.root.title(title)
        self.frame = Frame(self.root, width=400, height = 300, padx=5, pady=5)

        row=1
        self.connEntry = self.maketext(self.frame,
                                        caption="Schnittstelle:",
                                        width=60, height=5,
                                        ecol=1)
        self.connEntry.grid(columnspan=3)
        
        self.modusEntry = self.makeentry(self.frame,
                                         erow = 1, lrow=1,
                                         caption="Modus",
                                         width = 20)
        self.versorgSpgEntry = self.makeentry(self.frame,
                                              erow=1, lrow=1,
                                              lcol=2, ecol=3,
                                              caption="Versorg. Spannung:",
                                              width=20)
        self.spannungEntry = self.makeentry(self.frame,
                                              erow=3, lrow=3,
                                              caption="Spannung:",
                                              width=20)
        self.stromEntry = self.makeentry(self.frame,
                                         lrow=3, erow=3,
                                         lcol=2, ecol=3,
                                         caption="Strom:", width=20)
        self.deltaTEntry = self.makeentry(self.frame,
                                         lrow=4, erow=4,
                                         lcol=2, ecol=3,
                                         caption="dT:", width=20)
        self.ladungEntry = self.makeentry(self.frame,
                                          erow=4, lrow=4,
                                          caption="Ladung/Entladung:", width=20)
        
        l = Label(self.frame, text="Zellspannungen:")
        l.grid(row=5, column=0, sticky=NW)
        
        self.spgEntries = {}
        for i in range(1, 7):
            self.spgEntries['Spannung_' + str(i)] = self.makeentry(self.frame,
                                       erow=5+i, lrow=5+i,
                                       caption="Spannung #" + str(i),
                                       width=20)
        for i in range(7, 13):
            self.spgEntries['Spannung_' + str(i)] = self.makeentry(self.frame,
                                       erow=5+i-6, lrow=5+i-6,
                                       lcol=2, ecol=3,
                                       caption="Spannung #" + str(i),
                                       width=20)

        self.doDb = IntVar()
        self.storeInDb = self.makecheck(self.frame,
                                        caption="In Datenbank speichern",
                                        erow=14,
                                        variable=self.doDb,
                                        command = self.db_on_off)
        self.storeInDb.grid(columnspan=2)

        self.storeDbName = Label(self.frame, text='Datenbankame: ' + DBNAME)
        self.storeDbName.grid(row=15, column=0, columnspan = 4, sticky=NW)
        self.frame.pack()


    def loaded(self):
        #print("loading...")
        try:
            self.umr = ultramat.UltraReader(SERIALNAME)
        except Exception as exc:
            messagebox.showerror("Fehler",
                                 "Das Ultramat Ladegerät ist evtl. nicht angeschlossen oder nicht eingeschaltet.Text der Original-Ausnahmemeldung\n" + str(exc))
            sys.exit()
            print("Im here - this should not have happened!")    


        self.connEntry.insert(END, self.umr.get_info())
        self.update_values()
        #print("...loaded")

    def set_entry_text(self, entry, text):
        entry.delete(0, END)
        entry.insert(END, text)

    def update_values(self):
        l = self.umr.read_record()
        if LOGDATA==True: print(l)
        if len(l) > 75:
            pts = self.umr.get_points(l)    
            values = self.umr.get_values(pts)
            self.refresh_values_on_gui(values)
            if LOGDATA==True: print(''.join(self.umr.usage))
            #print(self.umr.usage)

        self.root.after(100, self.update_values)

    def refresh_values_on_gui(self, values):
        for val in values:
            if val.name=='VersorgungsSpg':
                self.set_entry_text(self.versorgSpgEntry,str(val.value)+val.unit)
            elif val.name=='Spannung':
                self.set_entry_text(self.spannungEntry,str(val.value)+val.unit)
            elif val.name=='Strom':
                self.set_entry_text(self.stromEntry,str(val.value)+val.unit)
            elif val.name=='Ladung':
                self.set_entry_text(self.ladungEntry,str(val.value)+val.unit)
            elif val.name=='Modus':
                self.set_entry_text(self.modusEntry, val.value)
            elif val.name=='dT':
                self.set_entry_text(self.deltaTEntry,str(val.value)+val.unit)
            else:
                if val.name in self.spgEntries:
                    self.set_entry_text(self.spgEntries[val.name],
                                        str(val.value)+val.unit)
            
        
    def db_on_off(self):
        """toggle writing to db on or off"""
        if self.database==None:
            print("switching to db write mode")
            self.database = mdbase.Mdbase(DBNAME)
            self.database.initialize()
      
    def mainloop(self):
        self.root.mainloop()

    def maketext(self, parent, lcol=0, lrow=0, erow=0, ecol=1, caption='', width=None, **options):
        Label(parent, text=caption).grid(row=lrow, column=lcol, sticky=NE)
        entry = Text(parent, **options)
        if width:
            entry.config(width=width)
    
        entry.grid(row=erow, column=ecol, sticky=W)
        return entry
    
    def makeentry(self, parent, lcol=0, lrow=0, erow=0, ecol=1, caption='', width=None, **options):
        Label(parent, text=caption).grid(row=lrow, column=lcol, sticky=E)
        entry = Entry(parent, **options)
        if width:
            entry.config(width=width)
    
        entry.grid(row=erow, column=ecol, sticky=W)
        return entry

    def makecheck(self, parent, ecol=0, erow=0, caption='', **options):
        cb = Checkbutton(parent, text=caption, **options)
        cb.grid(row=erow, column=ecol, sticky=W)
        return cb

if __name__ == "__main__":    
    ucd = UltramatContinDisp("Ultrapy")
    ucd.mainloop()
