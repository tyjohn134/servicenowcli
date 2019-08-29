#!/usr/bin/python

from PyInquirer import prompt, print_json, style_from_dict, Token, Validator, ValidationError
from pprint import pprint

from pyfiglet import Figlet

from sys import platform

import requests
import getpass
import pprint
import pysnow
import records
import db
import email_notify
#
# VALIDATOR
#

class EmptyValidator(Validator):
    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))

class ChoiceValidator(Validator):
    def validate(self, document):
        pprint(document.products)
        if len(document) == 0:
            raise ValidationError(
                message='Please choose an item')
        else:
            return True




#
#  QUESTIONS 
#

style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})


f = Figlet(font='slant')
print(f.renderText('ServiceNow Ticketing'))

def askCreds():
    questions = [
        {
            'type': 'input',
            'name': 'username',
            'default': '',
            'message': 'Please type in your username',
            'validate': EmptyValidator  
        },
        {
            'type': 'password',
            'name': 'pass',
            'message': 'Please type in your password',
            'validate': EmptyValidator    
        }
    ]
    answers = prompt(questions, style=style)
    return answers

def askTicketClose(ticketlist):
    questions = [
        {
            'type':'checkbox',
            'name':'tickets',
            'message':'Please check off the tickets you want to close',
            'choices': ticketlist, 
        },
    ]
    answers = prompt(questions, style=style)
    return answers

def askTaskEmail():
    questions = [
        {
            'type':'input',
            'name':'user_email',
            'message':"Please type in the user's email that opened this task:",
        },
    ]
    answers = prompt(questions, style=style)
    return answers    


def askTicketQuestions():
    questions = [
        {
            'type': 'list',
            'name': 'items',
            'message': 'Select which type of item you\'d like to close',
            'choices':[
                {
                    'name': 'Show Tasks'
                },
                {
                    'name': 'Show Incidents'
                },
                {
                    'name': 'Show Assigned to me'
                },  
                {
                    'name': 'Close Task'
                },
                {
                    'name': 'Close Incident'
                },
                {
                    'name': 'Update Task'
                },
                {
                    'name': 'Update Incident'
                },
                {
                    'name': 'Get Incidents Older Than x Days'
                },
                {
                    'name': 'Get Tasks Older Than x Days'
                },
                {
                    'name': 'Close Tickets Older Than x Days (both Incidents and Tasks)'
                },
                {
                    'name': 'Send Email'
                },
                {
                    'name':'Quit'
                }

            ],
            'validate':ChoiceValidator
        },
        {
            'type': 'input',
            'name': 'task_number',
            'message': 'What is the task ticket number?',
            'when':  lambda answers: answers["items"] == "Close Task" or answers["items"] == "Update Task" 
        },
        {
            'type': 'input',
            'name': 'incident_number',
            'message': 'What is the incident ticket number?',
            'when':  lambda answers: answers["items"] == "Close Incident" or answers["items"] == 'Update Incident' 
        },
        {
            'type':'input',
            'name':'incident_number',
            'message':'What is the ticket number?',
            'when': lambda answers: answers["items"] == 'Send Email'
        },
        {
            'type': 'input',
            'name': 'task_comment',
            'message': 'What would you like the task closing comment to be?',
            'when':  lambda answers: answers["items"] == "Close Task", 
        },
        {
            'type': 'input',
            'name': 'incident_comment',
            'message': 'What would you like the incident closing comment to be?',
            'when':  lambda answers: answers["items"] == "Close Incident", 
        },
        {
            'type': 'input',
            'name': 'task_comment_update',
            'message': 'What would you like the task comment to be?',
            'when':  lambda answers: answers["items"] == "Update Task", 
        },
        {
            'type': 'input',
            'name': 'incident_comment_update',
            'message': 'What would you like the incident comment to be?',
            'when':  lambda answers: answers["items"] == "Update Incident", 
        },
        {
            'type': 'input',
            'name': 'days',
            'message': 'How many days do you want to back?',
            'when':  lambda answers: answers["items"] == "Get Incidents Older Than x Days" or  answers["items"] == "Get Tasks Older Than x Days" or answers["items"] == "Close Tickets Older Than x Days (both Incidents and Tasks)", 
        },
    ]
    answers = prompt(questions, style=style)
    return answers


def main():
    # Set the request parameters
    creds = askCreds()
    while True:
        answers = askTicketQuestions()
        if answers['items'] == 'Close Task':
            records.closeTask(answers['task_number'], answers['task_comment'], creds['username'], creds['pass'])
        elif answers['items'] == 'Close Incident':
            records.closeIncident(answers['incident_number'], answers['incident_comment'], creds['username'], creds['pass'])
        elif answers['items'] == 'Show Tasks':
            table = records.printAllRecords(creds['username'], creds['pass'], 'task')
            print(table)
            print("%s tasks are in your group's queue." % len(table._rows))
        elif answers['items'] == 'Show Incidents':
            table = records.printAllRecords(creds['username'], creds['pass'], 'incident')
            print(table)
            print("%s incidents are in your group's queue." % len(table._rows))
        elif answers['items'] == 'Show Assigned To Me':
            print("Incidents Assigned To Me: ")
            table = records.printAllAssignedToMe(creds['username'], creds['pass'], 'incident', 'tyjohnson@gategroup.com')
            print(table)
            print("Tasks Assigned To Me: ")
            table = records.printAllAssignedToMe(creds['username'], creds['pass'], 'task', 'tyjohnson@gategroup.com')
            print(table)
        elif answers['items'] == 'Get Incidents Older Than x Days':
            table = records.getAllIncidentsOlderThan(creds['username'], creds['pass'], answers['days'])
            print(table)
            print("%s incidents are in your group's queue that are older than %s days." % (len(table._rows), answers['days']))   
        elif answers['items'] == 'Get Tasks Older Than x Days':
            table = records.getAllTasksOlderThan(creds['username'], creds['pass'], answers['days'])
            print(table)
            print("%s incidents are in your group's queue that are older than %s days." % (len(table._rows), answers['days']))   
        elif answers['items'] == 'Close Tickets Older Than x Days (both Incidents and Tasks)':
            print("NOTE: This will close tickets with a 'Closing due to age' comment.")
            ticketslist = records.createTicketList(creds['username'], creds['pass'], answers['days'])
            if ticketslist:
                ticket_answers = askTicketClose(ticketslist)
                for ticket in ticket_answers['tickets']:
                    ticket_num = ticket.split('-')[0]
                    if ticket_num.startswith('TASK'):
                        records.closeTask(ticket_num, 'Closing due to age', creds['username'], creds['pass'])
                    else:
                        records.closeIncident(ticket_num, 'Closing due to age', creds['username'], creds['pass'])
            else:
                print("No tickets were found older than %s days. Please choose a different amount." % answers['days'])
        elif answers['items'] == 'Send Email':
            if answers['incident_number'].startswith('TASK'):
                item = records.getOneTask(answers['incident_number'], creds['username'], creds['pass'])
                email_notify.sendEmail(answers['incident_number'], item['email'], item['short_description'])
                records.assignTask(answers['incident_number'], creds['username'], creds['pass'])
            else:
                item = records.getOneIncident(answers['incident_number'], creds['username'], creds['pass'])
                email_notify.sendEmail(answers['incident_number'], item['email'], item['short_description'])
                records.assignIncident(answers['incident_number'], creds['username'], creds['pass'])
            print("The email has been sent. Check sent box in Outlook.")
        elif answers['items'] == 'Update Incident' or answers['items'] == 'Update Task':
            if answers['items'] == 'Update Incident':
                records.updateIncident(answers['incident_number'], answers['incident_comment_update'], creds['username'], creds['pass'])
                ans = input("Do you want to assign this ticket to yourself? Y/N")
                if ans == "Y":
                    records.assignIncident(answers['incident_number'], creds['username'], creds['pass'])
            else:
                records.updateTask(answers['task_number'], answers['task_comment_update'], creds['username'], creds['pass'])
                ans = input("Do you want to assign this task to yourself? Y/N")
                if ans == "Y":
                    records.assignTask(answers['incident_number'], creds['username'], creds['pass'])
        elif answers['items'] == 'Quit':
            exit()
          

if __name__ == "__main__":
    main()

