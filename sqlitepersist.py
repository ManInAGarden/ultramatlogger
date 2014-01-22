import uuid
import datetime
import os
import sqlite3

STD_TIMEOUT=20

class TypeBase():
    DbType = None

    def __init__(self, isPrimary=False):
        self.IsPrimary = isPrimary
        self.DbLength = 0

    def get_creator_part(self, attname):
        cls = self.__class__
        answ = attname + " " + cls.DbType
        if self.DbLength>0:
            answ += "(" + str(self.DbLength) + ")"
        if self.IsPrimary==True:
            answ += " PRIMARY KEY"

        return answ

class Id(TypeBase):
    DbType = "TEXT"

    def __init__(self, isPrimary=True):
        super().__init__(isPrimary)
        self.DbLength = 40

class ForeignKeyId(Id):
    DbType = "TEXT"

    def __init__(self, isPrimary=False, foreignClass=None):
        super().__init__(isPrimary)
        self.ForeignClass = foreignClass


class Text(TypeBase):
    DbType = "TEXT"

    def __init__(self, length=50, isPrimary=False):
        super().__init__(isPrimary)
        self.DbLength = length
        self.IsPrimary = isPrimary

class Number(TypeBase):
    DbType = "NUMBER"

    def __init__(isPrimary=False):
        super().__init__(isPrimary)
        
class DateTime(TypeBase):
    """ class to represent a date or time or both in the database"""
    DbType = "TIMESTAMP"

    def __init__(self, isPrimary=False):
        super().__init__(isPrimary)

class PBase(object):
    """
         workhorse class doing any database work. Inherit from this class
        or it's children to make your class persistent in sqlite
    """
    TypeDict = {"Id":Id()}
    FileName = None
    TableName = None
    LogStatements = False
    TableExists = False
    LogFile = None
    
    def __init__(self):
        cls = self.__class__
        if cls.FileName == None:
            raise Exception("persistent class <" + cls.__name__ + "> is not initialized")
        
        self.Id = uuid.uuid4()
        if cls.TableExists==False:
            cls.evtly_create_table()


    @classmethod
    def initialize(cls, filename):
        #print("initializing", cls.TypeDict)
        cls.FileName = filename
        cls.LogFile = os.path.split(cls.FileName)[0]

    @classmethod
    def add_to_types(tdict):
        TypeDict.update(tdict)

    @classmethod
    def set_log_all_statements(cls, bval):
        cls.LogStatements = bval


    @classmethod
    def log_to_file(cls, s):
        f = open(cls.LogFile, 'a')
        with f:
            f.write(s + "\n")


    @classmethod
    def log_statement(cls, stmt):
        if cls.LogStatements!=None and cls.LogStatements==True:
            if LogFile==None:
                print('{0} - Executing: {1} '.format(datetime.datetime.now(), stmt))
            else:
                cls.log_to_file(cls.LogFile, '{0} - Executing: {1} '.format(datetime.datetime.now(), stmt))



    @classmethod
    def get_persistent_atts(cls):
        mypersatts = {}
        for attname in cls.TypeDict:
            tdesc = cls.TypeDict[attname]
            if isinstance(tdesc, TypeBase):
                mypersatts[attname] = tdesc

            
        return mypersatts

    @classmethod
    def create_vanilla_data(cls):
        #overwrite me for vanilla data initialization
        pass
        

    @classmethod
    def select(cls, whereClause=None, orderBy=None):
        """select data from the class"""
        answ = []
        
        if cls.FileName == None:
              raise Exception("persistent class <" + cls.__name__ + "> is not initialized")

        if cls.TableExists == False:
            cls.evtly_create_table()
        
        con = sqlite3.connect(cls.FileName)
        con.row_factory = sqlite3.Row
        stmt = "SELECT * from " + cls.TableName

        if whereClause != None:
            stmt += " WHERE " + whereClause

        if orderBy != None:
            stmt += " ORDER BY " + orderBy

        cls.log_statement(stmt)

        rows = None
        with con:
            cur = con.cursor()
            cur.execute(stmt)
            rows = cur.fetchall()

        
        persatts = cls.get_persistent_atts()
        
        if rows != None:
            for row in rows:
                curro = cls() #WOW!!!
                for att, tdesc in persatts.items():
                    pydta = cls.get_data_py_style(row[att], tdesc)
                    setattr(curro, att, pydta)

                answ.append(curro)
                
            
        return answ

    @classmethod
    def get_data_py_style(cls, dta, tdesc):
        answ = None
        if type(tdesc) == Text:
            answ = dta
        elif type(tdesc) == DateTime:
            answ = datetime.datetime.fromtimestamp(dta)
        elif type(tdesc) == Id:
            answ = uuid.UUID(dta)
            
        
        return answ
    

    @classmethod
    def evtly_create_table(cls):
        if cls.TableName==None:
            raise Exception("table name not defined in <" + cls.__name__ + ">")

        #check for table existance
        con = cls.connect_me()
        with con:
            docreate = False
            try:
                cursor = con.execute("SELECT * FROM " + cls.TableName)
            except sqlite3.OperationalError as operr:
                if str(operr).startswith("no such table:"):
                    docreate = True

            if docreate:
                cls.TableExists = cls.really_create_table(con)
            else:
                cls.TableExists = True
        
    @classmethod
    def connect_me(cls):
        return sqlite3.connect(cls.FileName, timeout=STD_TIMEOUT)

    @classmethod
    def really_create_table(cls, con):

        #print("creating table <" + cls.TableName + ">")
        
        #find all attributes derived from class TypeBase because these are the
        #persistent attributes which will be collumns of our table
        persatts = cls.get_persistent_atts()
        
        #now set up the create statement
        comma = ""
        stmt = "CREATE TABLE " + cls.TableName + " ("
        for attname, tdesc in persatts.items():
            stmt += comma + tdesc.get_creator_part(attname)
            
            comma = ", "
            
        stmt += ")"

        curs = con.cursor()
        curs.execute(stmt)

        cls.create_vanilla_data()

        return True
        

    def get_value_db_style(self, attname, tdesc):
        answ = None
        #print("getting <" + attname + "> for Type <" + str(tdesc) + ">")
        if type(tdesc)==Text:
            answ = "'" + str(getattr(self, attname, "None")) +  "'"
        elif type(tdesc)==DateTime:
            since_70 = getattr(self, attname, datetime.datetime(1970,1,1)) - datetime.datetime(1970,1,1)
            answ = str(since_70.total_seconds())
        elif type(tdesc)==Id or type(tdesc)==ForeignKeyId: 
            answ = "'" + str(getattr(self, attname, "None")) + "'"
        elif type(tdesc)==Number:
            answ = str(getattr(self, attname, "0"));
        else:
            raise Exception("unknown type <" + str(tdesc) + ">")

        return answ


    def __do_update(self, con):
        cls = self.__class__
        answ = False
        persatts = cls.get_persistent_atts()
        komma = ""
        stmt = "UPDATE " + cls.TableName + " SET "
        for attname, tdesc in persatts.items():
            if tdesc.IsPrimary==False:
                stmt += komma + attname + "=" + self.get_value_db_style(attname, tdesc)
                komma = ", "
            
        stmt += " WHERE "

        ands = ""
        for attname, tdesc in persatts.items():
            if tdesc.IsPrimary==True:
                stmt += ands + attname + "=" + self.get_value_db_style(attname, tdesc)
                ands = "AND "

        
        if len(ands)>0:
            cls.log_statement(stmt)
            try:
                cur = con.cursor()
                cur.execute(stmt)

                if cur.rowcount == 1:
                    answ = True
            except Exception as exc:
                print("Exception during update \n" + str(exc))
        else:
            raise Exception("no primary key(s) given - update impossible")
                
        return answ

    def __do_insert(self, con):
        cls = self.__class__
        answ = False
        persatts = cls.get_persistent_atts()
        komma = ""
        stmt = "INSERT INTO " + cls.TableName + "("
        for attname, tdesc in persatts.items():
            stmt += komma + attname
            komma = ", "
        stmt += ") VALUES("
        komma = ""
        for attname, tdesc in persatts.items():
            stmt += komma + self.get_value_db_style(attname, tdesc)
            komma = ", "

        stmt += ")"

        cls.log_statement(stmt)
        try:
            cur = con.cursor()
            cur.execute(stmt)
            answ = True
        except Exception as exc:
            print("Exception during insert \n" + str(exc))
        
        return answ
    
    def flush(self, updateFirst = True):
        """
        writes data to database
        """
        cls = self.__class__
        succ = False
        con = self.connect_me()
        with con:
            if updateFirst==True:
                succ = self.__do_update(con)
                if succ==False:
                    succ = self.__do_insert(con)
            else:
                succ = __do_insert(con)
                if succ == false:
                    __do_update(con)
        
        if succ == False:
            raise Exception("flush failed for class" + str(cls))

        
                
class PBaseTimed(PBase):
    TypeDict = PBase.TypeDict.copy()
    TypeDict.update({"Created": DateTime(),
        "LastUpdate": DateTime()})

    def flush(self, updateFirst = True):
        self.LastUpdate = datetime.datetime.now()
        super().flush(updateFirst)
    
    def __init__(self):
        super().__init__()
        self.Created = datetime.datetime.today()

class PBaseTimedCached(PBaseTimed):
    TypeDict = PBaseTimed.TypeDict.copy()
    SelCache = {}

    @classmethod
    def select(cls, where=None, order=None):
        cachek = str(where) + "_____" + str(order)

        if cachek in cls.SelCache:
            erg = cls.SelCache[cachek]
        else:
            erg = super().select(where, order)
            cls.SelCache[cachek] = erg

        return erg

        def flush(self):
            cls = self.__class__
            cls.SelCache.clear()
            super().flush()
