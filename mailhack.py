import imapclient
import json
import logging
import os.path
import sys

BATCH_SIZE=20

MAILHACK_FOLDER = 'Mailhack'
TRASH_FOLDER = 'Mailhack/Trash'
PERMIT_FOLDER = 'Mailhack/Permit'
BLOCK_FOLDER = 'Mailhack/Block'
INBOX_FOLDER = 'INBOX'

def address_to_string(addr):
    if addr.mailbox is None or addr.host is None:
        return None
        
    return str(addr.mailbox, encoding='utf-8').lower() + '@' + str(addr.host, encoding='utf-8').lower()

def always(envelope):
    return True

def not_permitted(envelope):
    return not permitted(envelope)

def permitted(envelope):
    for address in list(envelope.from_):
        sender = address_to_string(address)
        if sender is None:
            continue
            
        if sender in whitelist:
            return True
            
    return False
    
def from_addresses(folder):
    server.select_folder(folder)
    message_ids = server.search()
    message_count = len(message_ids)
    from_address_list = []
    
    for batch_start in range(0,message_count,BATCH_SIZE):
        if batch_start + BATCH_SIZE < message_count:
            batch = message_ids[batch_start:batch_start + BATCH_SIZE]
        else:
            batch = message_ids[batch_start:]
            
        data = server.fetch(batch,[b'ENVELOPE'])
        for id, d in data.items():
            envelope = d[b'ENVELOPE']
            for address in list(envelope.from_):
                sender = address_to_string(address)
                if sender is None:
                    continue
                else:
                    if sender not in from_address_list:
                        from_address_list.append(sender)
                        
    return from_address_list
        
    

def move(from_folder, to_folder, condition):
    server.select_folder(from_folder)
    message_ids = server.search()
    message_count = len(message_ids)
    print('there are {0} messages in the in {1}'.format(message_count, from_folder))

    total_moved = 0
    for batch_start in range(0,message_count,BATCH_SIZE):
        messages_to_move = []
        
        if batch_start + BATCH_SIZE < message_count:
            batch = message_ids[batch_start:batch_start + BATCH_SIZE]
        else:
            batch = message_ids[batch_start:]
            
        data = server.fetch(batch,[b'ENVELOPE'])
        for id, d in data.items():
            envelope = d[b'ENVELOPE']
            if condition(envelope):
                messages_to_move.append(id)
        
        if len(messages_to_move) > 0:
            server.copy(messages_to_move,to_folder)            
            server.delete_messages(messages_to_move)
            server.expunge()
            total_moved += len(messages_to_move)
        
    print('moved {0} messages from {1} to {2}'.format(total_moved, from_folder, to_folder))

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
        
    # load the white list
    whitelist = []
    whitelist_file = os.path.join(here,'whitelist.json')
    if os.path.exists(whitelist_file):
        with open(whitelist_file,'r') as f:
            whitelist = json.load(f)
            print('loaded white list from {0}'.format(whitelist_file))
    
    # TODO process the Permit/Block folders on all servers first
    for account in config['accounts']: 
        server = imapclient.IMAPClient(account['server'], port=account['port']) 
        response = server.login(account['username'],account['password'])
        print('connected to {0}'.format(account['server']))
    
        # check for required folders and create whatever doesn't exist
        for folder in [MAILHACK_FOLDER,TRASH_FOLDER,PERMIT_FOLDER,BLOCK_FOLDER]:
            if not server.folder_exists(folder):
                server.create_folder(folder)
                print('created folder: {0}'.format(folder))

        # check the Permit folder
        permit_list = from_addresses(PERMIT_FOLDER)
        for address in permit_list:
            if address not in whitelist:
                whitelist.append(address)
                print('{0} added to white list'.format(address))
                
        move(PERMIT_FOLDER, INBOX_FOLDER, always)
                
        # check the Block folder
        block_list = from_addresses(BLOCK_FOLDER)
        for address in block_list:
            if address in whitelist:
                whitelist.remove(address)
                print('removed {0} from white list'.format(address))
                
        move(BLOCK_FOLDER,TRASH_FOLDER, always)

        server.logout()
    
    # for each account    
    for account in config['accounts']: 
        server = imapclient.IMAPClient(account['server'], port=account['port']) 
        response = server.login(account['username'],account['password'])
        print('connected to {0}'.format(account['server']))

        move(INBOX_FOLDER,TRASH_FOLDER,not_permitted)
        move(TRASH_FOLDER,INBOX_FOLDER, permitted)
        
        server.logout()
        print('done processing {0}'.format(account['server']))
        
    with open(whitelist_file, 'w') as f:
        json.dump(sorted(whitelist),f, indent = 3)
        
    print('saved white list to {0}'.format(whitelist_file))
