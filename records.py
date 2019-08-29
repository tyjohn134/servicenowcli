

import pysnow
import db
import pprint
import config
from datetime import datetime, timedelta
from prettytable import PrettyTable

def getUser(c, record):
    user = c.resource(api_path='/table/sys_user')
    response = user.get(query={'sys_id': record['caller_id']['value']})
    return (response.one()['name'])

def getUserID(c, email):
    user = c.resource(api_path='/table/sys_user')
    response = user.get(query={'email': email})
    return (response.one()['sys_id'])

def getUserEmail(c, record):
    user = c.resource(api_path='/table/sys_user')
    response = user.get(query={'sys_id': record['caller_id']['value']})
    return (response.one()['email'])

def getUserEmailTask(c, record):
    user = c.resource(api_path='/table/sys_user')
    desc = record['short_description']
    indx = desc.find(":") + 2
    name = desc[indx:]
    response = user.get(query={'name': name})
    return (response.one()['email'])


def getGroup(c, record):
    user = c.resource(api_path='/table/sys_user_group')
    response = user.get(query={'sys_id': record['assignment_group']['value']})
    return (response.one()['name'])


def printAllAssignedToMe(username, passwd, rectype, email):
    # Create client object
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd, use_ssl=False)
    # Create PrettyTable object
    uid = getUserID(c,email)

    x = PrettyTable()

    if rectype == "incident":
        # Create query for ServiceNow
        qb = pysnow.QueryBuilder().field('active').equals('true').AND().field('assigned_to').equals(uid)
        incident = c.resource(api_path='/table/incident')
        x.field_names = ['Number', 'Caller', 'Description', 'Category', 'Assignment Group', 'Opened At', 'Contacted' ]
        response = incident.get(query=qb, limit=50, stream=True, fields=['sys_id', 'opened_at', 'assignment_group', 'number', 'state','assigned_to','short_description', 'caller_id', 'contact_type', 'priority', 'subcategory', 'u_kick_back_counter'])
        for record in response.all():
            # Check if record exists in database
            query = db.getData(record['number'])
            if query == "":
                db.saveData(record['number'], "No")
                x.add_row([record['number'], getUser(c, record), record['short_description'], record['subcategory'], getGroup(c, record), record['opened_at'], "No"])
            else:
                x.add_row([record['number'], getUser(c, record), record['short_description'], record['subcategory'], getGroup(c, record), record['opened_at'], query.contacted])
    elif rectype == "task": 
        qb = pysnow.QueryBuilder().field('active').equals('true').AND().field('assigned_to').equals(uid)
        task = c.resource(api_path='/table/task')
        x.field_names = ['Number', 'Description', 'Assignment Group', 'Opened At', 'Contacted' ]
        response = task.get(query=qb, limit=50, stream=True, fields=['sys_id', 'opened_at', 'assignment_group', 'number', 'state','assigned_to','short_description', 'contact_type', 'priority'])
        for record in response.all():
            if record['number'].startswith('TASK'):
                query = db.getData(record['number'])
                if query == "":
                    db.saveData(record['number'], "No")
                    x.add_row([record['number'], record['short_description'], getGroup(c, record), record['opened_at'], "No"])
                else:
                    x.add_row([record['number'], record['short_description'], getGroup(c, record), record['opened_at'], query.contacted])
    x.sortby = "Opened At"
    #x.reversesort = True
    return x



def printAllRecords(username, passwd, rectype):
    # Create client object
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd, use_ssl=False)
    # Create PrettyTable object
    x = PrettyTable()

    if rectype == "incident":
        # Create query for ServiceNow
        qb = pysnow.QueryBuilder().field('active').equals('true').AND().field('assignment_group').equals('').OR().field('assignment_group').equals('').AND().field('assigned_to').is_empty().AND().field('state').not_equals('6')
        incident = c.resource(api_path='/table/incident')
        x.field_names = ['Number', 'Caller', 'Description', 'Category', 'Assignment Group', 'Opened At', 'Contacted' ]
        response = incident.get(query=qb, limit=50, stream=True, fields=['sys_id', 'opened_at', 'assignment_group', 'number', 'state','assigned_to','short_description', 'caller_id', 'contact_type', 'priority', 'subcategory', 'u_kick_back_counter'])
        for record in response.all():
            # Check if record exists in database
            query = db.getData(record['number'])
            if query == "":
                db.saveData(record['number'], "No")
                x.add_row([record['number'], getUser(c, record), record['short_description'], record['subcategory'], getGroup(c, record), record['opened_at'], "No"])
            else:
                x.add_row([record['number'], getUser(c, record), record['short_description'], record['subcategory'], getGroup(c, record), record['opened_at'], query.contacted])
    elif rectype == "task": 
        qb = pysnow.QueryBuilder().field('assignment_group').equals('').OR().field('assignment_group').equals('').AND().field('assigned_to').is_empty().AND().field('active').equals('true')
        incident = c.resource(api_path='/table/task')
        x.field_names = ['Number', 'Description', 'Assignment Group', 'Opened At', 'Contacted']
        response = incident.get(query=qb, limit=50, stream=True, fields=['sys_id', 'opened_at', 'assignment_group', 'number', 'state','assigned_to','short_description', 'contact_type', 'priority'])
        for record in response.all():
            if record['number'].startswith('TASK'):
                query = db.getData(record['number'])
                if query == "":
                    db.saveData(record['number'], "No")
                    x.add_row([record['number'], record['short_description'], getGroup(c, record), record['opened_at'], "No"])
                else:
                    x.add_row([record['number'], record['short_description'], getGroup(c, record), record['opened_at'], query.contacted])
    x.sortby = "Opened At"
    x.reversesort = True
    return x

def closeTask(task_number, comment, username, passwd):
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd)
    # Define a resource, here we'll use the incident table API
    task = c.resource(api_path='/table/task')

    update = {"state":"3", "active": "false", "work_notes":"%s" % comment}

    # Update 'short_description' and 'state' for 'INC012345'
    updated_record = task.update(query={'number': "%s" % task_number}, payload=update)

    # Print out the updated record
    pprint.pprint('%s was closed on %s' % (updated_record.one()['number'], updated_record.one()['closed_at']))

def updateTask(task_number, comment, username, passwd):
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd)
    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/task')

    update =  {"comments_and_work_notes": "%s" % comment} 

    # Update 'short_description' and 'state' for 'INC012345'
    updated_record = incident.update(query={'number': '%s' % task_number} , payload=update)

    # Print out the updated record
    pprint.pprint('%s was closed on %s' % (updated_record.one()['number'], updated_record.one()['closed_at']))

def createTicketList(username, passwd, daysago):
    
    ####### INCIDENTS #########

    today = datetime.today()
    days_ago_time = today - timedelta(days=int(daysago))
    # Create client object
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd, use_ssl=False)

    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/incident')

    qb = pysnow.QueryBuilder().field('assignment_group').equals('').OR().field('assignment_group').equals('').AND().field('assigned_to').is_empty().AND().field('active').equals('true').AND().field('state').not_equals('6').AND().field('sys_created_on').less_than(days_ago_time)

    # Query for incidents with state 1
    response = incident.get(query=qb, limit=50, stream=True, fields=['sys_id', 'opened_at', 'assignment_group', 'number', 'state','assigned_to','short_description', 'contact_type', 'priority'])

    ######## TASKS #########

     # Define a resource, here we'll use the incident table API
    tasks = c.resource(api_path='/table/task')

    qb_t = pysnow.QueryBuilder().field('assignment_group').equals('').OR().field('assignment_group').equals('').AND().field('assigned_to').is_empty().AND().field('active').equals('true').AND().field('sys_created_on').less_than(days_ago_time)

    # Query for incidents with state 1
    response_t = tasks.get(query=qb_t, limit=50, stream=True, fields=['sys_id', 'opened_at', 'assignment_group', 'number', 'state','assigned_to','short_description', 'contact_type', 'priority', 'subcategory', 'u_kick_back_counter'])

    tickets = []
    # Iterate over the result and print out `sys_id` of the matching records.
    for record in response.all():
        tickets.append({'name': "%s - %s" % (record["number"], record["short_description"])})

    for record in response_t.all():
        if record['number'].startswith('TASK'):
            tickets.append({'name': "%s - %s" % (record["number"], record["short_description"])})    
    return tickets 

def closeIncident(incident_number, comment, username, passwd):
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd)
    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/incident')

    update =  {"close_code":"Closed/Resolved by Caller", "close_notes": "%s" % comment, "incident_state":"6","state":"6"} 

    # Update 'short_description' and 'state' for 'INC012345'
    updated_record = incident.update(query={'number': '%s' % incident_number} , payload=update)

    # Print out the updated record
    pprint.pprint('%s was closed on %s' % (updated_record.one()['number'], updated_record.one()['closed_at']))

def updateIncident(incident_number, comment, username, passwd):
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd)
    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/incident')

    update =  {"comments_and_work_notes": ""} 

    # Update 'short_description' and 'state' for 'INC012345'
    updated_record = incident.update(query={'number': '%s' % incident_number} , payload=update)

    # Print out the updated record
    pprint.pprint('%s was closed on %s' % (updated_record.one()['number'], updated_record.one()['closed_at']))


def assignIncident(incident_number, username, passwd):
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd)
    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/incident')

    update =  {"assigned_to": ""} 

    # Update 'short_description' and 'state' for 'INC012345'
    updated_record = incident.update(query={'number': '%s' % incident_number} , payload=update)

    # Print out the updated record
    pprint.pprint('%s was closed on %s' % (updated_record.one()['number'], updated_record.one()['closed_at']))

def assignTask(incident_number, username, passwd):
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd)
    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/incident')

    update =  {"assigned_to": ""} 

    # Update 'short_description' and 'state' for 'INC012345'
    updated_record = incident.update(query={'number': '%s' % incident_number} , payload=update)

    # Print out the updated record
    pprint.pprint('%s was closed on %s' % (updated_record.one()['number'], updated_record.one()['closed_at']))


def getAllIncidentsOlderThan(username, passwd, daysago):

    today = datetime.today()
    days_ago_time = today - timedelta(days=int(daysago))
    # Create client object
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd, use_ssl=False)

    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/incident')

    qb = pysnow.QueryBuilder().field('assignment_group').equals('').OR().field('assignment_group').equals('6230ba480f872500d7f84b9ce1050ec7').AND().field('assigned_to').is_empty().AND().field('active').equals('true').AND().field('state').not_equals('6').AND().field('sys_created_on').less_than(days_ago_time)

    # Query for incidents with state 1
    response = incident.get(query=qb, limit=50, stream=True, fields=['sys_id', 'opened_at', 'assignment_group', 'number', 'state','assigned_to','short_description', 'caller_id', 'contact_type', 'priority', 'subcategory', 'u_kick_back_counter'])

    x = PrettyTable()

    x.field_names = ['Number', 'Caller', 'Description', 'Category', 'Assignment Group', 'Opened At' ]

    # Iterate over the result and print out `sys_id` of the matching records.
    for record in response.all():
         x.add_row([record['number'], getUser(c, record), record['short_description'], record['subcategory'], getGroup(c, record), record['opened_at']])
    
    x.sortby = "Opened At"
    x.reversesort = True
    return x



def getAllTasksOlderThan(username, passwd, daysago):

    today = datetime.today()
    days_ago_time = today - timedelta(days=int(daysago))
    # Create client object
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd, use_ssl=False)

    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/task')

    qb = pysnow.QueryBuilder().field('assignment_group').equals('').OR().field('assignment_group').equals('6230ba480f872500d7f84b9ce1050ec7').AND().field('assigned_to').is_empty().AND().field('active').equals('true').AND().field('sys_created_on').less_than(days_ago_time)

    # Query for incidents with state 1
    response = incident.get(query=qb, limit=50, stream=True, fields=['sys_id', 'opened_at', 'assignment_group', 'number', 'state','assigned_to','short_description', 'contact_type', 'priority', 'subcategory', 'u_kick_back_counter'])

    x = PrettyTable()

    x.field_names = ['Number', 'Description', 'Assignment Group', 'Opened At' ]

    # Iterate over the result and print out `sys_id` of the matching records.
    for record in response.all():
        if record['number'].startswith('TASK'):
            x.add_row([record['number'], record['short_description'], getGroup(c, record), record['opened_at']])
    x.sortby = "Opened At"
    x.reversesort = True
    return x


def getOneIncident(incident_number, username, passwd):

    # Create client object
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd)
    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/incident')

    # Query for incident with number INC012345
    response = incident.get(query={'number': '%s' % incident_number})

    user_email = getUserEmail(c, response.one())
    
    item = {"email": user_email, "ticket_number": incident_number, "short_description": response.one()['short_description'] }
    # Print out the matching record
    return item

def getOneTask(task_number, username, passwd):

    # Create client object
    c = pysnow.Client(instance=config.servicenow['instance'], user=username, password=passwd)
    # Define a resource, here we'll use the incident table API
    incident = c.resource(api_path='/table/task')

    # Query for incident with number INC012345
    response = incident.get(query={'number': '%s' % task_number})

    email = getUserEmailTask(c, response.one())
    
    item = {"email": email, "ticket_number": task_number, "short_description": response.one()['short_description'] }
    # Print out the matching record
    return item



