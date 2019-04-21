import datetime
import imapclient
import json
import logging
import os.path
import sys

KEEP_DAYS = 90

TRASH_FOLDER = 'Mailhack/Trash'

MAX_MESSAGE_LIST_SIZE = 100
    
if __name__ == '__main__':
#    logging.basicConfig(
#        format='%(asctime)s - %(levelname)s: %(message)s',
#        level=logging.DEBUG
#    )    
    
    here = os.path.abspath(os.path.dirname(sys.argv[0])) 
    
    # load the config file
    config_file = os.path.join(here,'mailhack.json')
    if os.path.exists(config_file):
        with open(os.path.join(here,'mailhack.json'),'r') as f:
            config = json.load(f)
            print('loaded configuration from {0}'.format(config_file))
    else:
        sys.exit('require configuration file "{0}" not found'.format(config_file))
    
    keep_date = datetime.date.today() - datetime.timedelta(days=KEEP_DAYS)
        
    for account in config['accounts']: 
        server = imapclient.IMAPClient(account['server'], port=account['port']) 
        response = server.login(account['username'],account['password'])
        print('connected to {0}'.format(account['server']))

        if not server.folder_exists(TRASH_FOLDER):
            print('The {0} folder was not found. There is nothing to do for this account.'.format(TRASH_FOLDER))
            continue
            
        server.select_folder(TRASH_FOLDER)
        messages = server.search(['BEFORE',keep_date])
        
        l = len(messages)
        start = 0
        while start  < l:
            server.delete_messages(messages[start:start + MAX_MESSAGE_LIST_SIZE])
            start += MAX_MESSAGE_LIST_SIZE
            
        server.expunge()
        print('deleted {0} messages older than {1} days'.format(len(messages),KEEP_DAYS))
        server.logout()
    