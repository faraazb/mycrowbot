import sqlite3
import json

class DatMan:
    def __init__(self, dbname="mydatabase.db"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def register(self, details, temp=None):
        c = self.conn.cursor()
        # details.insert(4, 'NA')
        # details is a tuple like (user_id, rollno, name, college, classn)
        user_id, rollno, name, college, classn = details[0], details[1], details[2], details[3], details[4]
        stmt = 'UPDATE students SET rollno=(?), name=(?), college=(?), class=(?), last_atd=\'NA\' WHERE user_id=(?)'
        stmt2 = 'INSERT OR IGNORE INTO students (user_id, rollno, name, college, class) VALUES (?, ?, ?, ?, ?)'
        if temp:
            stmt = 'UPDATE students_temp SET rollno=(?), name=(?), college=(?), class=(?) WHERE user_id=(?)'
            stmt2 = 'INSERT OR IGNORE INTO students_temp (user_id, rollno, name, college, class) VALUES (?, ?, ?, ?, ?)'
        else:
            stmt3 = 'DELETE FROM students_temp WHERE user_id = (?)'
            c.execute(stmt3, (user_id, ))
        # c.execute(stmt, (rollno, name, college, class, 'NA', user_id))
        c.execute(stmt, (rollno, name, college, classn, user_id))
        # user_id = details.pop(4)
        # details.insert(0, user_id)
        c.execute(stmt2, details)
        # c.execute(stmt2, (user_id, rollono, name, college, class))
        self.conn.commit()

    def list(self, what2f, table, where=None, name=None):
        c = self.conn.cursor()
        if where!=None and name!=None:
            stmt = ('SELECT {} FROM [{}] WHERE {} = (?)').format(what2f, table, where)
            c.execute(stmt, (name, ))
        elif where==None and name==None:
            stmt = ('SELECT {} FROM [{}]').format(what2f, table)
            c.execute(stmt)
        record = c.fetchall()
        if record:
            if where!=None and name!=None:
                return record[0][0].split(', ')
            elif where==None and name==None:
                return [x[0] for x in record]
        else:
            return []

    def get(self, what2g, table, where, name):
        c = self.conn.cursor()
        stmt = ('SELECT {} FROM [{}] WHERE {} = (?)').format(what2g, table, where)
        c.execute(stmt, (name, ))
        # [0][0] returns first letter of first section name for classes

        record = c.fetchone()[0]
        return record

    def get_user(self, user_id, what2g='*', table='students'):
        c = self.conn.cursor()
        stmt = ('SELECT {} FROM {} WHERE user_id=(?)').format(what2g, table)
        c.execute(stmt, (user_id, ))
        student = c.fetchone()
        # print(type(student)) #is giving a tuple, will also be a tuple when only, say, clearance is fetched
        return student

    def get_requests(self, college, classn, user_id=None):
        c = self.conn.cursor()
        stmt = 'SELECT * FROM students_temp WHERE college = (?) AND class = (?)'
        if user_id:
            stmt = 'SELECT * FROM students_temp WHERE user_id = (?)'
            c.execute(stmt, (user_id, ))
        else:
            c.execute(stmt, (college, classn, ))
        requests = c.fetchall()
        if len(requests) == 0:
            return None
        # print(requests) [(1154167416, '4', 'FileManager', 'Viva Institute of Technology', 'SE-COMP')]
        return requests

    def setting(self, colln, option=None):
        c = self.conn.cursor()
        stmt = 'SELECT settings FROM colleges WHERE name = (?)'
        c.execute(stmt, (colln, ))
        configs = c.fetchone()[0]
        configs = json.loads(configs)
        if option:
            return configs[option]['val']
        else:
            return configs

    def update(self, table, what2u, withw2u, whereclause, wherevalue):
        # db.update('colleges', 'classes', classes, 'name', college)
        stmt = ('UPDATE "{}" SET {} = "{}" WHERE (?) = "{}"').format(table, what2u, withw2u, wherevalue)
        args = (whereclause, )
        if what2u == 'settings':
            stmt = ('UPDATE "{}" SET {} = (?) WHERE {} = "{}"').format(table, what2u, whereclause, wherevalue)
            args = (withw2u, )
        self.conn.execute(stmt, args)
        self.conn.commit()



    def add_college(self, name_text, admin_text, admin_name_text):
        #making entry in table: college
        cursorObj = self.conn.cursor()
        stmt = "INSERT INTO colleges(name, admin, admin_name) VALUES(?, ?, ?)"
        args = (name_text, admin_text, admin_name_text )
        cursorObj.execute(stmt, args)
        self.conn.commit()
        #creating college table for class and class admin
        stmt = 'CREATE TABLE IF NOT EXISTS [' + name_text + '](class text PRIMARY KEY, class_admin text, class_admin_name text)'
        cursorObj.execute(stmt)
        self.conn.commit()
        #creating college table in timetable.db
        conn = sqlite3.connect("timetable.db", check_same_thread=False)
        stmt = 'CREATE TABLE IF NOT EXISTS [' + name_text + '](class text PRIMARY KEY, Monday text NOT NULL DEFAULT NA, Tuesday text NOT NULL DEFAULT NA,'\
                'Wednesday text NOT NULL DEFAULT NA, Thursday text NOT NULL DEFAULT NA, Friday text NOT NULL DEFAULT NA, Saturday text NOT NULL DEFAULT NA)'
        cursortt = conn.cursor()
        cursortt.execute(stmt)
        conn.commit()
        conn.close()
        conn = sqlite3.connect("resources.db", check_same_thread=False)
        stmt = 'CREATE TABLE IF NOT EXISTS [' + name_text + '](class text NOT NULL, subject text NOT NULL, resource text, PRIMARY KEY(class, subject))'
        cursortt = conn.cursor()
        cursortt.execute(stmt)
        conn.commit()
        conn.close()

    def class_maintainence(self, name_text, class_list):
        conTT = sqlite3.connect("timetable.db", check_same_thread=False)
        cursorTT = conTT.cursor()
        conAT = sqlite3.connect("attendance.db", check_same_thread=False)
        cAT = conAT.cursor()
        cursorObj = self.conn.cursor()
        # old_classes = DBHelper.fetch(self, 'classes', 'colleges', 'name', name_text)
        # old_classes = old_classes.split(", ")
        stmt = 'SELECT class FROM ['+name_text+']'
        cursorObj.execute(stmt)
        classes = cursorObj.fetchall()
        old_classes = []
        for item in classes:
            old_classes.append(item[0])
        for item in old_classes:
            if item not in class_list:
                stmt = 'DELETE FROM [' + name_text + '] WHERE class = (?)'
                args = (item, )
                cursorObj.execute(stmt, args)
                cursorTT.execute(stmt, args)
        for item in class_list:
            if item not in old_classes:
                stmt = 'INSERT OR IGNORE INTO [' + name_text + '](class) VALUES(?)'
                args = (item, )
                cursorObj.execute(stmt, args)
                cursorTT.execute(stmt, args)
                stmt = 'CREATE TABLE IF NOT EXISTS ['+name_text+' '+item+'] (user_id integer NOT NULL, rollno text NOT NULL, count text, Monday text, Tuesday text, Wednesday text, Thursday text, Friday text, Saturday text, PRIMARY KEY(user_id, rollno))'
                cAT.execute(stmt)
                # Never delete the class atd tables automatically through class management, we will create a super
                # admin function to clear this cache for whenever a refresh is required
        self.conn.commit()
        conTT.commit()
        conTT.close()
        conAT.commit()
        conAT.close()

    def check_admin(self, table, admin_type, user_id):
        cursorObj = self.conn.cursor()
        stmt = 'SELECT * FROM [' + table + '] WHERE ' + admin_type + ' LIKE \'%' + str(user_id) + '%\''
        cursorObj.execute(stmt)
        record = cursorObj.fetchall()
        # print(record)
        return record

    def delete_college(self, name_text):
        # stmt = "DELETE FROM items WHERE description = (?)"
        stmt = "DELETE FROM colleges WHERE name = (?)"
        args = (name_text, )
        self.conn.execute(stmt, args)
        self.conn.commit()

class ResMan:
    def __init__(self, dbname="resources2.db"):
        # dbname="resources.db"
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def getPathItems(self, college, classn, path):
        c = self.conn.cursor()
        if path != '/':
            stmt = ("SELECT * FROM [{} {}] WHERE fpath = '{}'").format(college, classn, path)
            c.execute(stmt)
            item = c.fetchall()[0]
            if item[2] == 'file':
                return item
        stmt = ("SELECT * FROM [{} {}] WHERE path = '{}'").format(college, classn, path)
        c.execute(stmt)
        items = c.fetchall()
        return items

    def getPathFolders(self, college, classn, path):
        c = self.conn.cursor()
        stmt = ("SELECT * FROM [{} {}] WHERE path = '{}' AND type = 'folder'").format(college, classn, path)
        c.execute(stmt)
        folders = c.fetchall()
        return folders

    def getPreviousPath(self, college, classn, path):
        c = self.conn.cursor()
        stmt = ("SELECT path from [{} {}] WHERE fpath = '{}'").format(college, classn, path)
        c.execute(stmt)
        previous_path = c.fetchone()[0]
        return previous_path

    def store(self, college, classn, file_id, name, path):
        c = self.conn.cursor()
        fpath = path + '/' + name
        stmt = ("INSERT INTO [{} {}] (file_id, name, type, path, fpath) VALUES (?, ?, ?, ?, ?)").format(college, classn)
        args = (file_id, name, 'file', path, fpath, )
        c.execute(stmt, args)
        self.conn.commit()
        return True

    def delete(self, college, classn, file_id, fpath):
        c = self.conn.cursor()
        stmt = ("DELETE FROM [{} {}] WHERE file_id = '{}' AND fpath = '{}'").format(college, classn, file_id, fpath)
        c.execute(stmt)
        self.conn.commit()

    def create_folder(self, college, classn, name, path, fpath):
        c = self.conn.cursor()
        stmt = ("INSERT INTO [{} {}] (file_id, name, type, path, fpath) VALUES (?, ?, ?, ?, ?)").format(college, classn)
        args = (None, name, 'folder', path, fpath, )
        c.execute(stmt, args)
        self.conn.commit()
        return True

    def delete_folder(self, college, classn, cpath):
        c = self.conn.cursor()
        stmt = ("DELETE FROM [{} {}] WHERE path = '{}'").format(college, classn, cpath)
        c.execute(stmt)
        stmt = ("DELETE FROM [{} {}] WHERE fpath = '{}'").format(college, classn, cpath)
        c.execute(stmt)
        self.conn.commit()

class AtdMan:
    def __init__(self, dbname="attendance.db"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def mark(self, table, user_id, rollno, day, date, schedule, present):
        c = self.conn.cursor()
        count = {"counter":{}}
        monday = {"records":{}}
        count = json.dumps(count)
        monday = json.dumps(monday)
        stmt = 'INSERT OR IGNORE INTO ['+table+'] (user_id, rollno, count, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)'
        args = (user_id, rollno, count, monday, monday, monday, monday, monday, monday, )
        c.execute(stmt, args)
        stmt = 'SELECT '+day+' FROM ['+table+'] WHERE user_id = (?) AND rollno = (?)'
        args = (user_id, rollno, )
        c.execute(stmt, args)
        dregister = c.fetchone()[0]
        # check type of day===========
        stmt = 'SELECT count FROM ['+table+'] WHERE user_id = (?) AND rollno = (?)'
        args = (user_id, rollno )
        c.execute(stmt, args)
        count = c.fetchone()[0]

        dregister = json.loads(dregister)
        count = json.loads(count)
        dregister["records"][date] = []
        for lecture in schedule:
            if lecture not in count["counter"]:
                count["counter"][lecture] = {"pcount": 0, "tcount": 0}
            if lecture in present:
                item = {'lecture': lecture, 'status': 'P'}
                count["counter"][lecture]["pcount"] = count["counter"][lecture].get('pcount') + 1
                present.remove(lecture)
                # if multi-lectures of a subject are present in a day, this ensures that
                # not all lectures of that subject are marked present
            else:
                item = {'lecture': lecture, 'status': 'A'}
            dregister["records"][date].append(item)
            count["counter"][lecture]["tcount"] = count["counter"][lecture].get('tcount') + 1


        dregister = json.dumps(dregister)
        count = json.dumps(count)

        stmt = 'UPDATE ['+table+'] SET '+day+' = (?) WHERE user_id = (?)'
        # not using rollno in where clause, this updates all entries with the user_id
        # ensuring that data saved with any other rollno in the same class is also updated with the newest data
        # however /report only reports the user's stats using his current active registration,
        # ignoring all other user entries with inactive rollnos and those present in diff class tables.
        args = (dregister, user_id, )
        c.execute(stmt, args)
        stmt = 'UPDATE ['+table+'] SET count = (?) WHERE user_id = (?)'
        args = (count, user_id, )
        c.execute(stmt, args)
        self.conn.commit()

    def report(self, table, user_id, rollno):
        c = self.conn.cursor()
        stmt = 'SELECT count FROM ['+table+'] WHERE user_id = (?) AND rollno = (?)'
        args = (user_id, rollno )
        c.execute(stmt, args)
        result = c.fetchone()
        if result == None:
            return 'Your records don\'t exist probably because you have never marked your attendance.'
        elif result != None:
            result = json.loads(result[0])
            if len(result['counter']) != 0:
                text = ''
                for lecture in result['counter']:
                    percentage = (float(result['counter'][lecture]['pcount'])/float(result['counter'][lecture]['tcount'])*100)
                    nofl = str(result['counter'][lecture]['pcount'])+'/'+str(result['counter'][lecture]['tcount'])
                    text = text + ('<b>{}</b>: {}%, <code>{} attended</code>\n\n').format(lecture, str(round(percentage, 2)), nofl)
                return text
            else:
                return 'Your lecture counts don\'t exist due to an error'

    def reset(self, id, table):
        c = self.conn.cursor()
        stmt = 'DELETE FROM ['+table+'] WHERE user_id = (?)'
        args = (id, )
        c.execute(stmt, args)
        self.conn.commit()

class ttHelper  :
    def __init__(self, dbname="timetable.db"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def fetchtable(self, joinday, joincollege, class_id):
        day = str(joinday)
        college = str(joincollege)
        cursorObj = self.conn.cursor()
        stmt = 'SELECT ' + day + ' FROM ' + '[' + college + ']' + ' WHERE class = (?)'
        # print(stmt)
        args = (class_id, )
        actstmt = str(stmt)
        cursorObj.execute(actstmt, args)
        table = cursorObj.fetchone()[0]
        # print(table)
        return table

    def make_text(self, college_name, class_name):
        cursorObj = self.conn.cursor()
        stmt = 'SELECT * FROM [' + college_name + '] WHERE class = (?)'
        args = (class_name, )
        cursorObj.execute(stmt, args)
        class_tt = cursorObj.fetchone()
        text2r = 'Monday: ' + class_tt[1] + '\n'\
                'Tuesday: ' + class_tt[2] + '\n'\
                'Wednesday: ' + class_tt[3] + '\n'\
                'Thursday: ' + class_tt[4] + '\n'\
                'Friday: ' + class_tt[5] + '\n'
        if len(class_tt) == 7:
            text2r = text2r + 'Saturday: ' + class_tt[6]
        return text2r

    def update(self, college_name, class_name, day, timetable):
        cursorObj = self.conn.cursor()
        stmt = 'UPDATE [' + college_name + '] SET ' + day + ' = (?) WHERE class = (?)'
        args = (timetable, class_name)
        cursorObj.execute(stmt, args)
        self.conn.commit()
