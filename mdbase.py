import sqlitemeasures as sqm

class Mdbase():
    def __init__(self, dbfile, mode):
        self.dbfile = dbfile
        self.currentSeries = None
        self.mode = mode
        self.initialize()

    def initialize(self):
        #print("initializing database")
        sqm.Series.initialize(self.dbfile)
        sqm.Value.initialize(self.dbfile)
        sqm.Unit.initialize(self.dbfile)
        
        self.currentSeries = sqm.Series()
        self.currentSeries.Name = "ULTRAMAT - " + self.mode
        self.currentSeries.flush()

    def inticks(self, s):
        return "'" + str(s) +"'"

    def store_value(self, t, name, value, unit):
        units = sqm.Unit.select("Name="+ self.inticks(unit))
        if len(units)==1:
            val = sqm.Value()
            val.Value = value
            val.Name = name
            val.t = t
            val.SeriesId = self.currentSeries.Id
            val.UnitId = units[0].Id
            val.flush()
        
