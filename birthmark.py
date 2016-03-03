import pyodbc
class BirthMarkFunctions(object):
    """
    Contains methods to interact with BirthMark database i.e. query for all clients,balances,renewals,extensions
     and new invoices.
     """

    def __init__(self, dsn="BirthMark", passwd="linet"):
        self.dsn = dsn
        self.birthmark_passwd = passwd

    def _connect(self):
        conn = pyodbc.connect(DSN=self.dsn, PWD=self.birthmark_passwd)
        cursor = conn.cursor()
        
        return conn, cursor

    def clients_with_balance(self):
        """
        Get clients with balance of more than 500 and return a list of dictionaries of each client
        """
        
        conn, cursor = self._connect()
        clients = []
        cursor.execute("""SELECT  distinct c.ClientID as ClientID,c.[Name] as Client_Name,c.Town as location,
        c.Occupation as occupation,c.Address as Address, c.Mobile as Phone_Number,c.Domant as Domant, ct.bal
          as Balance From (SELECT SUM(Amount) AS bal, ClientID FROM ClientTrans  GROUP BY ClientID)
           ct INNER JOIN Clients c ON ct.ClientID = c.ClientID""")
        try:
            for i in cursor.fetchall():
                dic = dict()
                dic['Id'], dic['Name'], dic['Town'], dic['Occ'], dic['Address'], dic['Phone'], dic['Domant'], dic['Amount']=i
                clients.append(dic)
        except:
            pass
        finally:
            conn.close()
            
        return clients
    
    def clients_with_renewal(self):
        """
        Get clients with renewals and return a list of dictionaries of each client
        """

        conn, cursor = self._connect()
        clients = []
        cursor.execute("SELECT c.ClientID as ClientID,c.[Name] as Client_Name,c.Town as locatio,c.Occupation as occupation,c.Address as Address,c.Domant as Domant, dm.TransNo AS Invoice_Number, c.Mobile as Phone_Number , Policies.[Name] AS Risk, dv.RegNo AS Insured_Policy, dm.DuePremium AS Amount, dm.Business AS Policy_Status FROM  (((DebitMaster dm LEFT OUTER JOIN Clients C ON C.ClientID = dm.ClientID) LEFT OUTER JOIN DebitVehicles dv ON dm.TransNo = dv.DebitNoteNo) LEFT OUTER JOIN Policies ON Policies.ClassID & Policies.Policycode = dm.ClassCode) ")        
        try:
            for i in cursor.fetchall():
                if i[9]:                    
                    i[8] = "%s %s"%(i[9],i[8])    
                dic = dict()
                dic['Id'],dic['Name'],dic['Town'],dic['Occ'],dic['Address'],dic['Domant'],dic['TransNo'],dic['Phone'],dic['Policy'],dic['RegNo'],dic['Amount'],dic['PolicyStatus']=i
                clients.append(dic)
        except:
            pass
        
        finally:
            conn.close()
        
        return clients
    
    def clients_with_expiry(self):
        """
        Get clients with expiry and return a list of dictionaries of each client
        """
        
        conn, cursor = self._connect()
        clients = []
        cursor.execute("""SELECT c.ClientID as ClientID,c.Name as Client_Name,c.Town as locatio,c.Occupation as
         occupation,c.Address as Address,c.Domant as Domant, c.Mobile  as Phone_Number, po.[Name] AS
         Policy_Type, pv.RegNo AS Reg, pm.[To] AS Expiry FROM (((Clients c INNER JOIN Polmaster pm ON
         c.ClientID = pm.ClientID) LEFT OUTER JOIN Policies po ON po.ClassID & po.Policycode = pm.ClassCode)
          LEFT OUTER JOIN PolicyVehicles pv ON pm.ProposalNo = pv.ProposalNo) WHERE (pm.Status = 'current')""")
        try:
            for i in cursor.fetchall():
                dic = {}
                dic['Id'], dic['Name'],dic['Town'],dic['Occ'],dic['Address'],dic['Domant'],dic['Phone'],dic['Policy'],\
                dic['RegNo'],dic['To']=i
                if i[8]:
                    dic['Policy'] = "%s %s" % (i[8], i[7])
                clients.append(dic)
        except:
            pass
        finally:
            conn.close()
            
        return clients

    def clients_with_extension(self):
        clients = []
        for client in self.clients_with_renewal():
            if client['PolicyStatus'] == 'EXTENSION':
                clients.append(client)
                
        return clients
    
    def all_clients(self):
        
        conn, cursor = self._connect()
        clients = []
        sql = "select ClientID, Name,Address,Town,Occupation,Mobile,Email,Total,Domant,DOB  from clients"
        cursor.execute(sql)
        try:
            for i in cursor.fetchall():
                dic = dict()
                dic['Id'],dic['Name'], dic['Address'], dic['Town'], dic['Occ'], dic['Phone'], dic['email'], dic['bal'],\
                dic['Domant'], dic['dob'] = i
                clients.append(dic)
        except:
            pass
        finally:
            conn.close()
        return clients

    def get_company_details(self):
        """
        Returns the company details as saved in birthmark database
        """
        conn, cursor = self._connect()
        sql = "select CompName,Address,Location,Town,Telephone,Mobile,Website,Email,Branches  from Company"
        cursor.execute(sql)
        diction = dict()
        diction["Name"], diction["Address"], diction["Location"], diction["Town"], diction["Telephone"],\
            diction["Mobile"], diction["Website"], diction["Email"], diction["Branches"] = cursor.fetchone()
        return diction

    def get_birthmark_users(self):
        """
        Returns the users of the birthmark application
        """
        conn, cursor = self._connect()
        sql = "select Username, FullName,Title,Password from Users"
        cursor.execute(sql)
        users = list()
        for user in cursor.fetchall():
            diction = dict()
            try:
                fname, lname = user[1].split(" ")
            except ValueError:
                fname, lname = user[1], ""
            diction["username"] = user[0]
            diction["firstname"] = fname
            diction["lastname"] = lname
            diction["title"] = user[2]
            diction["password"] = user[3]
            users.append(diction)
        return users

