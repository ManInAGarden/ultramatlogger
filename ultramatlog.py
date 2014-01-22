#!/usr/bin/python3
# -*- coding: utf8 -*-

import time
import datetime
import curses
import ultramat as umat
import mdbase

from optparse import OptionParser

SERIALNAME="/dev/ttyUSB0" # can be overriden on command line
DBNAME="/home/pi/ultrapy.db" #change on command line to user another db-file

class Base():
    def __init__(self, x=0, y=0, mode=None):
        self.x = x
        self.y = y
        self.mode = mode

    def display(self):
        pass

class Label(Base):
    def __init__(self, x=0, y=0, mode=None, text="Label:"):
        super().__init__(x=x, y=y, mode=mode)
        self.text = text

    def display(self, scr):
        if self.mode != None:
            scr.addstr(self.y, self.x, self.text, self.mode)
        else:
            scr.addstr(self.y, self.x, self.text)
    

class Text(Label):
    def __init__(self, x=0, y=0, mode=curses.A_REVERSE, text="Text", width=20):
        super().__init__(x=x, y=y, mode=mode, text=" "*width)
        self.usetext = text
        self.width = width

    def set_text(self, text):
        self.usetext = text

    def display(self, scr):
        self.text = self.usetext.ljust(self.width, " ")[0:self.width]
        super().display(scr)



class Reader():
    def __init__(self):
        self.parser = OptionParser()
        (self.options, self.parameters) = self.initparser()
        self.serialName = self.options.serialname
        self.dbName = self.options.dbname
        self.firststore = True
    
    def initcurses(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        self.init_screen()

    def endcurses(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


    def initparser(self):
        p = self.parser
        p.add_option("-s", "--serialdev", dest="serialname", help="name of serial device to which ultramat loader is connected", default=SERIALNAME)
        p.add_option("-q", "--quiet", action="store_false", dest="verbose", default=True,  help="don't display the data cockpit")
        p.add_option("-b", "--basefile", dest="dbname", default=DBNAME,  help="name of the sqlite database file to store data into")
        p.add_option("-d", "--delta", dest="delta", default=1000,  help="time delta in which to store data in the database, surplus values will be ignored")
        
        return p.parse_args()



    def init_screen(self):
        col0 = 0
        col1 = 45
        tcol0 = 22
        tcol1 = 59
        self.scr = {"title":Label(x=col0,y=0,text="ULTRAPY"+(" "*73), mode=curses.A_REVERSE),
                    "interfaceL":Label(x=col0, y=2, text="Interface:"),
                    "interfaceT":Text(x=tcol0, y=2, width=57),
                    "modusL":Label(x=col0, y=3, text="Modus:"),
                    "modusT":Text(x=tcol0, y=3),
                    "versorgspgL":Label(x=col0, y=4, text="Versorgungsspannung:"),
                    "versorgspgT":Text(x=tcol0, y=4),
                    "stromL":Label(x=col0, y=5, text="Strom:"),
                    "stromT":Text(x=tcol0, y=5),
                    "spannungL":Label(x=col1, y=5, text="Spannung:"),
                    "spannungT":Text(x=tcol1, y=5),
                    "ladungL":Label(x=col0, y=6, text="Ladung:"),
                    "ladungT":Text(x=tcol0, y=6),
                    "dTL":Label(x=col1, y=6, text="delta t:"),
                    "dTT":Text(x=tcol1, y=6),
                    "zellspgsL": Label(x=col0, y=8, text="Zellspannungen:")}
        
        self.spgEntries = {}
        for i in range(1,7):
            self.scr["spannung"+str(i)+"L"]=Label(x=col0, y=8+i, text="Spannung" + str(i))
            self.scr["spannung"+str(i)+"T"]=Text(x=tcol0, y=8+i)
            self.spgEntries["Spannung_"+str(i)]="spannung"+str(i)+"T"

            self.scr["spannung"+str(i+6)+"L"]=Label(x=col1, y=8+i, text="Spannung" + str(i+6))
            self.scr["spannung"+str(i+6)+"T"]=Text(x=tcol1, y=8+i)
            self.spgEntries["Spannung_"+str(i+6)]="spannung"+str(i+6)+"T"

        self.scr["dbnameL"]=Label(x=col0, y=8+7+1, text="Datenbank:")
        self.scr["dbnameT"]=Text(x=tcol0, y=8+7+1, width=57)
        self.scr["lastTimeL"]=Label(x=col0, y=8+7+2, text="Letzter DB Zeitpkt:")
        self.scr["lastTimeT"]=Text(x=tcol0, y=8+7+2, width=22, text="...")
        self.scr["cycleTimeL"]=Label(x=col0, y=8+7+3, text="Zyklusdauer:")
        self.scr["cycleTimeT"]=Text(x=tcol0, y=8+7+3, width=22)
        self.scr["infoL"]=Label(x=col0, y=8+7+5, text="Ctr+C - Beenden")


    def display_screen(self, all=True):
        for key, base in self.scr.items():
            if isinstance(base, Text) or all==True:
                base.display(self.stdscr)

        self.stdscr.refresh()
        
    def display_data(self, values):
        scr = self.scr
        for val in values:
            if val.name=="VersorgungsSpg":
                scr["versorgspgT"].set_text(str(val.value)+val.unit)
            elif val.name=="Spannung":
                scr["spannungT"].set_text(str(val.value)+val.unit)
            elif val.name=="Strom":
                scr["stromT"].set_text(str(val.value)+val.unit)
            elif val.name=="Ladung":
                scr["ladungT"].set_text(str(val.value)+val.unit)
            elif val.name=="Modus":
                scr["modusT"].set_text(val.value)
            elif val.name=="dT":
                scr["dTT"].set_text(str(val.value)+val.unit)
            elif val.name in self.spgEntries:
                scr[self.spgEntries[val.name]].set_text(str(val.value)+val.unit)
        
        self.display_screen(all=False)


    def store_db_values(self, mod, t, values):

        dostore = self.dbName != None and mod!="ENDE" and mod!="FEHLER" and mod!="STANDBY"

        if dostore==True:
            if self.firststore == True:
                self.firststore = False
                self.currentDbStore = mdbase.Mdbase(self.dbName, mod)

            for val in values:
                self.currentDbStore.store_value(t, val.name, val.value, val.unit)
        else:
            self.firststore = True

        return dostore


    def work(self):
        ur = umat.UltraReader(self.serialName)
        self.scr["interfaceT"].set_text(ur.get_info())
        self.scr["dbnameT"].set_text(self.dbName)
        
        self.display_screen()
        storageDelta = self.options.delta # STORAGE DELTA IN MS
        current = datetime.datetime.now()
        currentDelta = 0

        try:
            while True:
                starttime = datetime.datetime.now()
                l = ur.read_record()

                if len(l) > 75:
                    pts = ur.get_points(l)
                    values = ur.get_values(pts)
                    current = ur.read_time
                    if currentDelta >= storageDelta:
                        stored = self.store_db_values(ur.get_last_mode(), 
                            current,
                            values)
                        currentDelta = 0
                        if stored==True:
                            self.scr["lastTimeT"].set_text(str(current))

                    self.display_data(values)
                    currentDelta += ur.get_last_delta()
                    endtime = datetime.datetime.now()
                    self.scr["cycleTimeT"].set_text(str((endtime-starttime).total_seconds()*1000)+"ms")
                            
        finally:
            ur.close()



if __name__ == "__main__":
    print("ultramatlog V1.0 started")

    reader = Reader()
    hadex = None
    try:
        reader.initcurses()
        reader.work()
    except Exception as exc:
        hadex = exc
    finally:
        reader.endcurses()

    if hadex!=None:
        raise(hadex)

    print("ultramatlog done")
