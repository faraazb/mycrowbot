import asyncio
import logging
import os
import re
import sys
import time
import json

logging.basicConfig(level=logging.WARNING)
from telethon import TelegramClient, events, types, custom, utils, errors, Button
from helper import Selector, Restrictor, Communicator
from database import DatMan, ResMan, AtdMan
db = DatMan() #studenthelper merged with this
resdb = ResMan()
atdb = AtdMan() #tthelper merged with this

class Student:
    def __init__(self, bot):
        self.bot = bot
        self.select = Selector(bot)
        self.bot.add_event_handler(self.register, events.NewMessage(pattern='/register', forwards=False))
        self.bot.add_event_handler(self.resources, events.NewMessage(pattern='/resources', forwards=False))

    async def register(self, event):
        bot = self.bot
        select = self.select
        user = event.sender_id
        try:
            firstn = (await event.get_sender()).first_name
            name = firstn + ' ' + (await event.get_sender()).last_name
        except TypeError: #when the user doesn't have a last name
            name = firstn
        colleges = db.list('name', 'colleges')
        college = await select.colleges(user, colleges)
        classn = await select.classes(user, college)
        async with bot.conversation(user) as conv:
            await bot.send_message(user, 'What is your Roll No. ?')
            rollno = (await conv.wait_event(events.NewMessage(pattern='\w+'))).text
            conv.cancel()
        clearance = db.setting(college, "Access")
        details = (user, rollno, name, college, classn)
        if clearance == 'RESTRICTED':
            # thinking of using a routine to send pending requests messages to admins
            # admins = db.list("admin", "colleges", "name", college) + db.list("class_admin", college, "class", classn)
            # request = ('<b>{}</b> wants to register at <b>{}</b> at <b>{}</b> as Roll No. <b>{}</b>.\n'\
            #             'Use <b>/admin > Join Requests</b> to allow or deny.')
            # message = await bot.send_message(admins, request, parse_mode='html')
            db.register(details, '1') #passing 1 for Students_temp
            await bot.send_message(user, 'Awaiting approval from class or college admin(s)..Will Notify')
        elif clearance == 'OPEN':
            # insert or update main db also remove any entry in temp db
            db.register(details)
            await bot.send_message(user, 'Registration complete!')

    async def resources(self, event):
        bot = self.bot
        select = self.select
        user = event.sender_id
        student = db.get_user(user)
        if student:
            college = student[3]
            classn = student[4]
            config = db.setting(college, 'Cross-Class Resources')
            if config == 'ON':
                classn = await select.classes(user, college)
            path = '/'
            while isinstance(path, str):
                path = await select.directory(user, college, classn, path)
                if path == None:
                    return
            await bot.send_message(user, path[1], parse_mode='html', file=path[0])
        else:
            await bot.send_message(user, 'Since you\'re not /register ed, Idk which college you belong to!', parse_mode='html')


    async def timetable(self, event):
        bot = self.bot
        select = self.select
        user = event.sender_id
        student = db.get_user(user)
        if student:
            college = student[3]
            classn = await select.classes(user, college)
            message = ''
            timetable = db.get_timetable(college, classn) #this db function should return a dictionary
            [message + ('<b>{}</b>: {}\n\n').format(day, timetable[day]) for day in timetable]
            await bot.send_message(user, message, parse_mode='html')
        else:
            await bot.send_message(user, 'You have to /register for me to know which college you belong to!')



class Admin:
    def __init__(self, bot):
        self.bot = bot
        self.select = Selector(bot)
        self.restrict = Restrictor(bot)
        self.comm = Communicator(bot)
        self.bot.add_event_handler(self.admin, events.NewMessage(pattern='/admin', forwards=False))
        self.bot.add_event_handler(self.add_file, events.NewMessage(pattern='/add', forwards=False))
        self.bot.add_event_handler(self.delete_file, events.NewMessage(pattern='/delete', forwards=False))
        self.bot.add_event_handler(self.self_report, events.NewMessage(pattern='/selfreport', forwards=False))
        self.bot.add_event_handler(self.report, events.NewMessage(pattern='/report', forwards=False))

    async def report(self, event):
        bot = self.bot
        user = event.sender_id
        message2 = 'Do you think you medical services like ambulance are required?'
        keyboard = [[Button.inline('Yes')],
                    [Button.inline('No')]]
        async with bot.conversation(user) as conv:
            await bot.send_message(user, message2, parse_mode='html', buttons=keyboard)
            query = await conv.wait_event(events.CallbackQuery(user))
            # option = (query.data).decode('utf-8')
            # await query.delete()
            # option = (query.data).decode('utf-8')
            # await query.delete()


    async def self_report(self, event):
        bot = self.bot
        user = event.sender_id
        keyboard = [[Button.inline('I think I am an asymptomatic contact')],
                    [Button.inline('I have symptoms')]]
        keyboard2 = [[Button.inline('Person 1', data='EDITA')],
                    [Button.inline('Person 2', data='EDITT')],
                    [Button.inline('Person 3', data='JOIN')]]
        message2 = 'Okayy, you think you could be a contact. Who did you come in contact with?'
        message = 'Do you think or know you are Covid positive?'
        async with bot.conversation(user) as conv:
            await bot.send_message(user, message, parse_mode='html', buttons=keyboard)
            query = await conv.wait_event(events.CallbackQuery(user))
            # option = (query.data).decode('utf-8')
            # await query.delete()
            await bot.send_message(user, message2, parse_mode='html', buttons=keyboard2)
            query = await conv.wait_event(events.CallbackQuery(user))
            # option = (query.data).decode('utf-8')
            # await query.delete()


    async def admin(self, event):
        bot = self.bot
        select = self.select
        restrict = self.restrict
        user = event.sender_id
        keyboard = [[Button.inline('Assign/Unassign Class Admins', data='EDITA')],
                    [Button.inline('Edit Time-Table', data='EDITT')],
                    [Button.inline('Join Requests', data='JOIN')]]
        access = await restrict.clearance(user)
        if not access:
            await bot.send_message(user, 'You have to be /register ed and also be a college/class admin to do this!')
            return
        elif access == 'STUDENT':
            await bot.send_message(user, 'You don\'t have permission to do this!')
            return
        elif access == 'CLASS ADMIN':
            message = '<b>Class Admin Menu</b>'
        elif isinstance(access, list): #this means access is a list of colleges, this is multiple/sinlge college Admin and Super Admin case
            keyboard.insert(0, [Button.inline('Add/Delete Classes', data='EDITC')])
            keyboard.append([Button.inline('Settings', data='CONFIG')])
            message = '<b>Admin Menu</b>'
        async with bot.conversation(user) as conv:
            await bot.send_message(user, message, parse_mode='html', buttons=keyboard)
            query = await conv.wait_event(events.CallbackQuery(user))
            option = (query.data).decode('utf-8')
            await query.delete()
            conv.cancel()
        if option == 'EDITC':
            await self.edit_classes(user, access)
        elif option == 'EDITA':
            access = await restrict.clear(user)
            if access and access!='STUDENT':#this means we have a college+class successfully selected: [college, class]
                await self.edit_class_admins(user, access)
        elif option == 'EDITT':
            access = await restrict.clear(user)
            if access and access!='STUDENT':
                await self.edit_timetable(user, access)
        elif option == 'CONFIG':
            access = await restrict.clearance(user)
            #using clearance because this is a college/super admin setting and changes are made at college level and selecting a class is not important
            #here access is a list of colleges if the person is a college admin or super admin
            if access and isinstance(access, list):
                await self.settings(user, access)
        elif option == 'JOIN':
            access = await restrict.clear(user)
            if access and access!='STUDENT':
                await self.join_requests(user, access)
        else:
            bot.send_message(user, 'I have no idea how you got here!', parse_mode='html')


    async def edit_classes(self, user, access):
        print(access)
        bot = self.bot
        select = self.select
        comm = self.comm
        if len(access) == 1:
            college = access[0]
        else:
            college = await select.colleges(user, access)
        classes = db.get('classes', 'colleges', 'name', college)
        ins = '<i>Copy the above message, add a class seprated with \', \' to add or erase an existing one to delete; and send it back.</i>'
        error = 'Seperate each class with a <b>comma and space</b>!\n<i>E.g. FE-A<b>, </b>FYBA-C<b>, </b>SYCOMP-D'
        pattern = r'^[^,\s]*(,\s[^,\s]+)*$'
        classes = await comm.communicate(user, classes, ins, error, pattern)
        db.update('colleges', 'classes', classes, 'name', college)
        await bot.send_message(user, ('Classes updated at {}!').format(college))


    async def edit_class_admins(self, user, access):
        bot = self.bot
        comm = self.comm
        college, classn = access[0], access[1]
        old_admins = db.list('class_admins', college, 'class', classn)
        ins = '<i>Copy the above message, add a user id seprated with \', \' to add or erase an existing one to delete; and send it back.</i>'
        error = 'Seperate each ids with a <b>comma and space</b>!\n<i>E.g. 123456789<b>, </b>012345678<b>, </b>876543210'
        pattern = r'^\d{9}(,\s\d{9})*$'
        if old_admins == []:
            ins = '<i>No class admins have been assigned. Send comma+space seperated user ids to assign.\nE.g. 123456789<b>, </b>012345678<b>, </b>876543210'
        admins = await comm.communicate(user, classes, ins, error, pattern)
        admins_l = admins.split(', ')
        allclass = db.list('classes', 'colleges', 'name', college)
        for id in old_admins:
            if id not in admins_l:
                clearance = db.get_user(id, 'clearance')[0] #check indexing PROPERLY
                clearance = json.loads(clearance)
                clearance[college].delete(classn)
                if clearance[college]==[]:
                    del clearance[college]
                if clearance == {}:
                    clearance = 'NULL'
                db.update('students', 'clearance', clearance, 'user_id', id)
        for id in admins_l:
            if id not in old_admins:
                student = db.get_user(id) #check indexing PROPERLY
                if not student:
                    await bot.send_message(user, id+' is not registered and wasn\'t given admin access!')
                    admins_l.delete(id)
                    continue
                clearance = student[6]
                if not clearance:
                    clearance = {}
                    clearance[college] = []
                else:
                    clearance = json.loads(clearance)
                    if not clearance[college]:
                        clearance[college] = []
                clearance[college].append(classn)
                if clearance[college] == allclass:
                    clearance[college] = 'ALL'
                    # yet to decide behaviour: whether allclass class admin should be made college admin
                clearance = json.dumps(clearance)
                db.update('students', 'clearance', clearance, 'user_id', id) #check if db queries can be made with string user_ids
        #the student does not exist case is yet to be patched bc the id will be entered in colleges table irrespectively!!!
        admins = ', '.join(admins_l)
        db.update(college, 'class_admins', admins, 'class', classn)
        await bot.send_message(user, ('Admins updated for <b>{}</b> at <b>{}</b>!').format(classn, college))

    async def edit_timetable(self, user, access):
        bot = self.bot
        comm = self.comm
        college, classn = access[0], access[1]
        ttable = db.get('*', college, 'class', classn)
        ins = '<i>Copy the above message, edit and send it back.</i>\n'
        error = '<i>Seperate each lecture with a <b>comma and space</b> and each new day on a new line. Use \'NA\' for holidays!</i>'
        pattern = r'^(([^,]{3,6}day:\s[^,]+)(,\s[^,]+)*){7}$'
        table = (await comm.communicate(user, classes, ins+error, pattern, error)).split("\n")
        for dayt in table:
            dayt = dayt.split(": ")
            day, schedule = dayt[0], dayt[1]
            atd.update(college, day, schedule, 'class', classn)
        await bot.send_message(user, ('Time-Table updated for <b>{}</b> at <b>{}</b>!').format(classn, college))

    # {property:{val:active_val, options:val1, val2, val3}}
    # {"Access": {"val": "OPEN", "options": ["OPEN", "RESTRICTED"]}, "Cross-Class Resources": {"val":"ON", "options": ["ON", "OFF"]}}
    async def settings(self, user, access):
        bot = self.bot
        select = self.select
        college = access[0]
        if len(access) != 1:
            college = await select.colleges(user, access)
        settings = db.setting(college)
        keyboard = [[Button.inline(property+': '+settings[property]['val'], data=property+': '+settings[property]['val'])] for property in settings]
        async with bot.conversation(user) as conv:
            await bot.send_message(user, 'Settings', buttons=keyboard)
            queryobj = await conv.wait_event(events.CallbackQuery(user))
            query = ((queryobj.data).decode('utf-8')).split(': ')
            property, value = query[0], query[1]
            # value = query[1]
            opt_copy = settings[property]['options'][:]
            # using : slice to make a copy otherwise opt_copy is just an alias if only = assignment is used
            settings[property]['options'].remove(value)
            keyboard = [[Button.inline(opt, data=opt)] for opt in settings[property]['options']]
            await queryobj.delete()
            await bot.send_message(user, property+': '+value, buttons=keyboard)
            queryobj = await conv.wait_event(events.CallbackQuery(user))
            query = (queryobj.data).decode('utf-8')
            settings[property]['val']=query
            settings[property]['options'] = opt_copy
            settings = json.dumps(settings)
            db.update('colleges', 'settings', settings, 'name', college)
            await queryobj.delete()
            await bot.send_message(user, ('Settings updated for <b>{}</b>').format(college), parse_mode='html')
            conv.cancel()

    async def join_requests(self, user, access):
        bot = self.bot
        college, classn = access[0], access[1]
        requests = db.get_requests(college, classn)
        if requests == None:
            bot.send_message(user, 'No pending requests!')
            return
        keyboard = [[Button.inline(str(request[0])+' - '+request[2]+' as Roll No. '+request[1], data=str(request[0]))] for request in requests]
        allow_deny = [[Button.inline('Allow', data='Allow')], [Button.inline('Deny', data='Deny')]]
        async with bot.conversation(user) as conv:
            await bot.send_message(user, college+' - '+classn+'\nSelect a request:', buttons=keyboard)
            query = await conv.wait_event(events.CallbackQuery(user))
            request_id = (query.data).decode('utf-8')
            await query.delete()
            await bot.send_message(user, 'Select action:', buttons=allow_deny)
            query = await conv.wait_event(events.CallbackQuery(user))
            action = (query.data).decode('utf-8')
            await query.delete()
            conv.cancel()
        user = db.get_requests(college, classn, request_id)[0] #(1154167416, '4', 'FileManager', 'Viva Institute of Technology', 'SE-COMP')
        if action == 'Allow':
            db.register(user)
            message = ('Registration complete!\nYou\'ve been allowed to join {} at {}.').format(classn, college)
            await bot.send_message(user[0], message, parse_mode='html')
        elif action == 'Deny':
            # will have to delete the request from students_temp
            message = ('Sorry! Your request to join {} at {} has been denied by the college or class admin.').format(classn, college)
            await bot.send_message(request_id, message, parse_mode='html')

    async def add_file(self, event):
        bot = self.bot
        select = self.select
        restrict = self.restrict
        comm = self.comm
        user = event.sender_id
        file_message = await event.message.get_reply_message()
        if file_message:
            access = await restrict.clear(user)
            if access == 'STUDENT' or access == None:
                await bot.send_message(user, 'You don\'t have the permission to add resources!')
                return
            college, classn = access[0], access[1]
            name = (event.message.text).split('/add ')[1]
            if not name:
                # check message caption for file name when no args with /add
                await bot.send_message(user, 'Please specify the file name with add command. <i>E.g. /add FileName</i>',
                                       parse_mode='html')
                return
            file_id = file_message.file.id
            path = '/'
            while path != 'addfile':
                actual_path = path
                path = await select.directory(user, college, classn, path, 'ADD')
                if path == 'makedir':
                    ins = ('<code>{}</code>\nSend folder name').format(actual_path)
                    err = 'Please do not use *, /, \\ or other special characters'
                    folder_name = await comm.communicate(user, None, ins, err, r'(^(\w+\s*)+$)')
                    if actual_path == '/':
                        path = actual_path + folder_name #path is fpath of the created folder and actual_path is the contain path
                    else:
                        path = actual_path + '/' + folder_name
                    if resdb.create_folder(college, classn, folder_name, actual_path, path):
                        continue
                    else:
                        await bot.send_message(user, 'There was some problem while creating this folder!')
                        return
            if resdb.store(college, classn, file_id, name, actual_path): #actual_path is contain path
                await bot.send_message(user, 'File added!')
            else:
                await bot.send_message(user, 'There was some problem while adding the file!')
        else:
            await bot.send_message(user, 'Send the /add command as a reply to a file!')

    async def delete_file(self, event):
        bot = self.bot
        select = self.select
        restrict = self.restrict
        comm = self.comm
        user = event.sender_id
        access = await restrict.clear(user)
        if access == 'STUDENT' or access == None:
            await bot.send_message(user, 'You don\'t have the permission to delete resources!')
            return
        college, classn = access[0], access[1]
        path = '/'
        while isinstance(path, str):
            cpath = path
            path = await select.directory(user, college, classn, path, 'DELETE')
            if path == 'deletedir':
                caution = ('Are you sure you want to delete <code>{}</code> and everything inside it?').format(cpath)
                confirm = await comm.confirm(user, caution)
                if confirm == 'Yes':
                    resdb.delete_folder(college, classn, cpath)
                    await bot.send_message(user, 'Folder and it\'s contents deleted!')
                    return
                else:
                    path = cpath
        resdb.delete(college, classn, path[0], path[4])
        await bot.send_message(user, ('File: <code>{}</code> deleted!').format(path[1]))

class Super:
    def __init__(self, bot):
        self.bot = bot
        self.select = Selector(bot)
        self.restrict = Restrictor(bot)
        self.comm = Communicator(bot)
        self.bot.add_event_handler(self.superman, events.NewMessage(pattern='/super', forwards=False))

    async def superman(self, event):
        bot = self.bot
        select = self.select
        restrict = self.restrict
        user = event.sender_id
        access = await restrict.clear(user, 1) #passing 1 for just getting clearance and not college list
        if access == 'SUPER':
            keyboard = [[Button.inline('Add a College', data='ADDC')],
                        [Button.inline('Delete a College', data='DELC')],
                        [Button.inline('Modify College Admins', data='MODA')]]
            async with bot.conversation(user) as conv:
                await bot.send_message(user, 'Super Admin Menu', parse_mode='html', buttons=keyboard)
                query = await conv.wait_event(events.CallbackQuery(user))
                option = (query.data).decode('utf-8')
                await query.delete()
                conv.cancel()
            if option == 'ADDC':
                self.add_college(user)
            elif option == 'DELC':
                self.delete_college(user)
            elif option == 'MODA':
                self.modify_college_admins(user)
        else:
            await bot.send_message(user, 'You are not Superman! :(')
            return

    async def add_college(self, user):
        bot = self.bot
        comm = self.comm
        college = await comm.communicate(user, None, 'College Name:', '0')
        decide = await comm.confirm(user, 'Add admin(s) now or later?', [Now, Later])
        if decide == 'Now':
            ins = 'Send College Admin user ids'
            err = 'Seperate each user id with a comma and space!'
            admins = await comm.communicate(user, None, ins, err, r'^\d{9}(,\s\d{9})*$')
        elif decide == 'Later':
            await bot.send_message(user, 'Okayy, Adding college...')
            admins = None
        done = db.adddb_college(college, admins) #database function to be written
        if done == 1:
            await bot.send_message(user, 'College added!')
            return
        else:
            await bot.send_message(user, 'Some problem occurred!')
            return

    async def delete_college(self, user):
        bot = self.bot
        select = self.select
        comm = self.comm
        college = await select.colleges(user, db.list('name', 'colleges'))
        confirm = await comm.confirm(user, ('Are you sure you want to delete <b>{}</b>?').format(college))
        if confirm == 'Yes':
            done = db.deldb_college(college) #database function to be written
            if done == 1:
                await bot.send_message(user, 'College deleted!')
                return
            else:
                await bot.send_message(user, 'Some problem occurred!')
                return
        else:
            await bot.send_message(user, 'No problemo!')
            return





