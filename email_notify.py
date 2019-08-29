import config
import win32com.client as win32

def sendEmail(ticketnum, useremail, description):
    outlook = win32.Dispatch('outlook.application')
    data = saveData(ticketnum, "Yes")
    print("{0} has been updated in the database.".format(data.number))
    mail = outlook.CreateItem(0)
    mail.To = '%s' % useremail
    if ticketnum.startswith('TASK'):
        mail.Subject = "Catalog Task {num} - {desc}".format(num=ticketnum, desc=description)
    else:
        mail.Subject = "Incident {num} - {desc}".format(num=ticketnum, desc=description)
    mail.HTMLBody = config.email['message']
    mail.Send()
    