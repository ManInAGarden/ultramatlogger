#!/usr/bin/python3
# -*- coding: utf8 -*-

import serial
import time
import datetime

SERIALNAME = "/dev/ttyUSB0"

class Value():
    unit = ''
    value = 0.0
    name = ''

    def __repr__(self):
        return self.name + ": " + str(self.value) + self.unit



class UltraReader:
    ser = None
    units = {'Spannung':'V',
             'Strom' :'mA',
             'Ladung':'mAh',
             'Leistung':'mW',
             'Energie':'mAh',
             'VersorgungsSpg':'V',
             'Balance':'V',
             'dT':'ms',
             'Spannung_1': 'V',
             'Spannung_2': 'V',
             'Spannung_3': 'V',
             'Spannung_4': 'V',
             'Spannung_5': 'V',
             'Spannung_6': 'V',
             'Spannung_7': 'V',
             'Spannung_8': 'V',
             'Spannung_9': 'V',
             'Spannung_10': 'V',
             'Spannung_11': 'V',
             'Spannung_12': 'V'}
    
    factors = {'Spannung':0.001,
             'Strom' :1.0,
             'Ladung':1.0,
             'Leistung': 1.0,
             'Energie':1.0,
             'VersorgungsSpg':0.001,
             'Balance':0.001,
             'dT':0.01,
             'Spannung_1': 0.001,
             'Spannung_2': 0.001,
             'Spannung_3': 0.001,
             'Spannung_4': 0.001,
             'Spannung_5': 0.001,
             'Spannung_6': 0.001,
             'Spannung_7': 0.001,
             'Spannung_8': 0.001,
             'Spannung_9': 0.001,
             'Spannung_10': 0.001,
             'Spannung_11': 0.001,
             'Spannung_12': 0.001}
    modus_dict = { '00':'STANDBY',
                   '01':'LADEN',
                   '02':'ENTLADEN',
                   '03':'ZYKLPAUSE',
                   '04':'ENDE',
                   '05':'FEHLER'}
    

    def __init__(self, name):
        self.ser = serial.Serial(name, timeout = 1.0)
        self.last_delta = 0.0
        self.last_mode = "00"
        self.read_time = datetime.datetime.now()

    def show_info(self):
        if self.ser != None:
            print('init OK for ' + str(self.ser.name))
            print(self.ser)

    def get_info(self):
        if self.ser != None:
            return str(self.ser)
        else:
            return 'Not initialized'    

    def readline(self):
        line = self.ser.readline()
        return line

    def read_record(self):
        line = ''
        done = False
        halfdone = False

        while done == False:
            c = self.ser.read(1)
            i = int.from_bytes(c, 'little')
            if i == 0x0c:
                done = True
            elif i == 0x0d:
                halfdone = True
            else:
                line += chr(i)
                
        return line

    def read(self, maximum):
        data = self.ser.read(maximum)
        return data

    def close(self):
        print("closing serial")
        self.ser.close()

    def getasint(self, line, startpos, endpos):
        part = line[startpos:endpos]
        #print(part)
        self.reflect_usage(startpos, endpos, 'n')
            
        return int(part, 16)

    def get_as_modus(self, line, startpos, endpos):
        answ = ""
        part = line[startpos:endpos]
        self.reflect_usage(startpos, endpos, 'm')
        if part in UltraReader.modus_dict:
            answ = UltraReader.modus_dict[part]
        else:
            answ = part

        return answ
        

    def showusage_init(self):
        self.usage = list(' ' * 76)

    def reflect_usage(self, s, e, marker):
            for i in range(s,e):
                self.usage[i] = marker
        
    def get_points(self, line):
        points = {}
        validbalance = False
        minVoltage = 10000
        maxVoltage = -10000
        self.showusage_init()
        points['Rohdaten'] = line
        points['Spannung'] = self.getasint(line, 12, 16)
        points['Strom'] = self.getasint(line, 16, 20)
        points['Ladung'] = self.getasint(line, 20, 24)
        points['Leistung'] = points['Spannung'] * points['Strom'] / 1000
        points['Energie'] = points['Spannung'] * points['Ladung'] / 1000
        points['VersorgungsSpg'] = self.getasint(line, 4, 8)
        points['Balance'] = 0
        points['Modus'] = self.get_as_modus(line,8,10)
        points['dT'] = self.getasint(line, 72, 76)
       
        for i in range(12):
            validbalance = True
            voltage = self.getasint(line, 24+i*4, 28+i*4)
            points['Spannung_' + str(i+1)] = voltage

            if voltage < minVoltage:
                minVoltage = voltage

            if voltage > maxVoltage:
                maxVoltage = voltage
            
        if validbalance == True:
            points['Balance'] = maxVoltage - minVoltage
        else:
            points['Balance'] = 0.0
    
        return points


    def get_last_delta(self):
        return self.last_delta


    def get_last_mode(self):
        return self.last_mode

    def get_values(self, points):
        values = []
        for idx, key in enumerate(points):
            val = Value()
            #print(key, value)
            if key in self.units:
                currval = points[key]
                val.unit = self.units[key]
                val.value = currval * self.factors[key]
                if key=="dT":
                    self.last_delta = val.value
            else:
                val.value = points[key] 
                if key=="Modus":
                    self.last_mode = val.value
                
            val.name = key
            values.append(val)

        self.read_time += datetime.timedelta(seconds=1)
        #readings in the ultrmat are in a distance of
        #exactly one second regardless how often we read.
        #when we read more often we have to wait for the data,
        #wehen we read less often data will be buffered.

        return values


if __name__ == "__main__":
    ur = UltraReader(SERIALNAME)
    ur.show_info()
    try:
        while True:
            l = ur.read_record()
            #print(l)
            if len(l) > 75:
                pts = ur.get_points(l)
                #print(pts)
                values = ur.get_values(pts)
                print(values)
                time.sleep(1.0)
    finally:
        ur.close()
