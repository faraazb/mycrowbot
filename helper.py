# Selector - used to select colleges/classes/documents using inline keyboard
# Communicator - used to receive a pre-patterned response to a question
# Restrictor - used to provide 'clearance' to admins and make 'clear' their access by selecting a college and class they manage.
# Ruler - used to help the Admin event handlers
import json, re
from telethon import TelegramClient, events, types, custom, utils, errors, Button
from database import DatMan, ResMan, AtdMan
db = DatMan()
res = ResMan()
atd = AtdMan()
import logging


class Selector:
    def __init__(self, bot):
        self.bot = bot
        # self.event = event

    async def colleges(self, user, list):
        bot = self.bot
        async with bot.conversation(user) as conv:
            keyboard = [[Button.inline(college, data=college)] for college in list]
            await bot.send_message(user, 'Choose a college:', buttons=keyboard)
            college = await conv.wait_event(events.CallbackQuery(user))
            await college.delete()
            return (college.data).decode('utf-8')

    async def classes(self, user, college=None, list=None, message=None):
        bot = self.bot
        if college == None and list == None or college != None and list != None:
            raise ValueError('Invalid parameters')
            return None
        elif college != None and list == None:
            list = db.list('classes', 'colleges', 'name', college)
            message = ('<b>{}</b>').format(college)
        if message == None:
            message = 'Choose:'
        async with bot.conversation(user) as conv:
            keyboard = [[Button.inline(classn, data=classn)] for classn in list]
            await bot.send_message(user, message, parse_mode='html', buttons=keyboard)
            classn = await conv.wait_event(events.CallbackQuery(user))
            await classn.delete()
            return (classn.data).decode('utf-8')

    async def directory(self, user, college, classn, path=None, act='SEND'):
        bot = self.bot
        if path == None:
            path = '/'
        if act == 'ADD':
            items = res.getPathFolders(college, classn, path)
        else:
            items = res.getPathItems(college, classn, path)  # 1. check type using F.path = var(path) 2. if file: throw error, return item
        if isinstance(items, tuple):
            return items
        message = ('You are here -- > <code>{}</code>').format(path)
        keyboard = []
        for item in items:
            if item[2] == 'file':
                if act == 'ADD':
                    continue #skip displaying files when action is adding a new file
                emoji = '📄'
            elif item[2] == 'folder':
                emoji = '📁'
            btext = emoji + ' ' + item[1]
            if item[3] != '/': # only add / if containing folder is not root(/)
                data = path + '/' + item[1]
            else:
                data = path + item[1]
            keyboard.append([Button.inline(btext, data=data)])
        if act == 'ADD':
            keyboard.append([Button.inline('Add here', data='addfile')])
            keyboard.append([Button.inline('New Folder here', data='makedir')])
        elif act == 'DELETE' and path != '/': #deleting while no resources checked with length of keyboard
            keyboard.append([Button.inline('Delete this folder', data='deletedir')])
        if path != None and path != '/':
            keyboard.append([Button.inline('<<Back<<', data=res.getPreviousPath(college, classn, path))])
        async with bot.conversation(user) as conv:
            if len(keyboard) == 0: #this means act is send or delete, path is root and len(items)=0 in which case there are no buttons.
                await bot.send_message(user, 'No resources have been added!')
                return
            await bot.send_message(user, message, parse_mode='html', buttons=keyboard)
            next_path = await conv.wait_event(events.CallbackQuery(user))
            await next_path.delete()
            return (next_path.data).decode('utf-8')


    async def subject(self, user, college, classn):
        bot = self.bot
        subjects = res.subjects(college, classn)
        async with bot.conversation(user) as conv:
            keyboard = [[Button.inline(subject, data=subject)] for subject in subjects]
            message = ('<b>{} - {}</b>').format(college, classn)
            await bot.send_message(user, message, parse_mode='html', buttons=keyboard)
            subject = await conv.wait_event(events.CallbackQuery(user))
            await subject.delete()
            return (subject.data).decode('utf-8')

    async def category(self, user, college, classn, subject):
        bot = self.bot
        categories = res.get(college, classn, subject)
        async with bot.conversation(user) as conv:
            keyboard = [[Button.inline(category+'s', data=category)] for category in categories]
            message = ('<b>{}:</b>').format(subject)
            await bot.send_message(user, message, parse_mode='html', buttons=keyboard)
            category = await conv.wait_event(events.CallbackQuery(user))
            await category.delete()
            return (category.data).decode('utf-8')

    async def document(self, user, college, classn, subject, category):
        bot = self.bot
        documents = res.get(college, classn, subject, category)
        async with bot.conversation(user) as conv:
            keyboard = [[Button.inline(document['title'], data=i)] for (document, i) in zip(documents, range(0, len(documents)))]
            message = ('<b>{} - {}s:</b>').format(subject, category)
            await bot.send_message(user, message, parse_mode='html', buttons=keyboard)
            document = await conv.wait_event(events.CallbackQuery(user))
            index = int((document.data).decode('utf-8'))
            message = documents[index]['title']
            file_id = documents[index]['id']
            await document.delete()
            await bot.send_message(user, message, parse_mode='html', file=file_id)
            conv.cancel()

class Restrictor:
    def __init__(self, bot):
        self.bot = bot
        self.select = Selector(self.bot)

    #this just determines the level of access a user has
    async def clearance(self, user_id, state=0):
        select = self.select
        student = db.get_user(user_id)
        if student:
            clearance = student[6]
            # clearance = json.loads(clearance)
            if not clearance:
                return 'STUDENT'
            elif clearance: #the empty dictionary case, wherein it'll just exist and clear this check, should be patched in edit admin function
                # clearance = student[6]
                if clearance == 'SUPER':
                    if state == 1:
                        return 'SUPER'
                    else:
                        return db.list('name', 'colleges')
                clearance = json.loads(clearance)
                college_admin = [college for college in clearance['colleges'] if clearance['colleges'][college]=='ALL']
                if len(college_admin) > 0:
                    if state == 1:
                        return 'COLLEGE ADMIN'
                    else:
                        return college_admin
                else:
                    return 'CLASS ADMIN'
        else:
            return None

    #this helps in selecting college and class only accessible to an admin
    async def clear(self, user_id):
        select = self.select
        student = db.get_user(user_id) ##HAAAAAAAAAAAAVE TO PROGRAMMMMMMMMMMM BETTTTTTTTTTTTTTTTTTTTTER
        if student:
            clearance = student[6]
            if not clearance:
                return 'STUDENT'
            elif clearance:
                if clearance == 'SUPER':
                    college = await select.colleges(user_id, db.list('name', 'colleges'))
                    classn = await select.classes(user_id, college)
                    return [college, classn]
                colleges = [college for college in clearance['colleges']]
                if len(colleges) > 1:
                    college = await select.colleges(colleges)
                elif len(colleges) == 1:
                    college = colleges[0]
                if clearance['colleges'][college][0] == 'ALL': #college-admin case
                    classn = await select.classes(college)
                    return [college, classn]
                elif len(clearance['colleges'][college]) == 1: #ony-1 class-admin case
                    permit = [college, clearance['colleges'][college][0]]
                    return permit
                elif len(clearance['colleges'][college]) > 1: #more than 1 class-admin case
                    classn = await select.classes(clearance['colleges'][college])
                    return [college, classn]
        else:
            return None

class Communicator:
    def __init__(self, bot):
        self.bot = bot

    async def communicate(self, user, info2c, instruction, error, pattern=None):
        bot = self.bot
        cancelkey = [Button.inline('Cancel', data='CANCEL')]
        async with bot.conversation(user) as conv:
            if info2c != None:
                await bot.send_message(user, info2c, parse_mode='html')
            await bot.send_message(user, instruction, parse_mode='html', buttons=cancelkey)
            response = (await conv.get_response(0)).message
            if pattern:
                while re.match(pattern, response) is None:
                    await bot.send_message(user, error, parse_mode='html', buttons=cancelkey)
                    response = (await conv.get_response(0)).message
            return response

    async def confirm(self, user, caution, options=['Yes', 'No']):
        bot = self.bot
        keys = [Button.inline(opt, data=opt) for opt in options]
        async with bot.conversation(user) as conv:
            await bot.send_message(user, caution, parse_mode='html', buttons=keys)
            confirmation = await conv.wait_event(events.CallbackQuery(user))
            confirmation = (confirmation.data).decode('utf-8')
            return confirmation