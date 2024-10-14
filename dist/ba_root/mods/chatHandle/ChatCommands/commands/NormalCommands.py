from .Handlers import send
import ba
import _ba
import ba.internal
from stats import mystats
from ba._general import Call
import _thread
###
import os
import json
import threading
###
Commands = ['me', 'list', 'uniqeid', 'ping','password']
CommandAliases = ['stats', 'score', 'rank',
                  'myself', 'l', 'id', 'pb-id', 'pb', 'accountid']


def ExcelCommand(command, arguments, clientid, accountid):
    """
    Checks The Command And Run Function

    Parameters:
        command : str
        arguments : str
        clientid : int
        accountid : int

    Returns:
        None
    """
    if command in ['me', 'stats', 'score', 'rank', 'myself']:
        fetch_send_stats(accountid, clientid)

    elif command in ['password']:#==============================nani===========================
        fetch_password(accountid,clientid)

    elif command in ['list', 'l']:
        list(clientid)

    elif command in ['uniqeid', 'id', 'pb-id', 'pb', 'accountid']:
        accountid_request(arguments, clientid, accountid)

    elif command in ['ping']:
        get_ping(arguments, clientid)


def fetch_password(account_id, clientid):#==============================nani===========================
    # Define the function that will fetch the password from bank.json
    def get_password_from_bank():
        # Get the directory where server files are located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the path to the bank.json file located in the shop folder
        json_file = os.path.join(current_dir, '..', '..' , '..' , 'shop', 'bank.json')

        # Check if the file exists and is not empty
        if os.path.exists(json_file) and os.path.getsize(json_file) > 0:
            with open(json_file, 'r') as f:
                try:
                    bank_data = json.load(f)
                    if account_id in bank_data:
                        # Get the password from bank.json
                        obj = bank_data[account_id]
                        reply = f"Your UserID: {account_id}  &&  Password: {obj['password']}"
                    else:
                        reply = "Account not found."
                except json.JSONDecodeError as e:
                    reply = f"Error decoding JSON: {e}"
        else:
            reply = "Bank file does not exist or is empty."

        # Display the reply to the user
        _ba.pushcall(Call(send, reply, clientid), from_other_thread=True)

    # Create a new thread to execute the password fetching
    thread = threading.Thread(target=get_password_from_bank)
    thread.start()  # Start the thread


def get_ping(arguments, clientid):
    if arguments == [] or arguments == ['']:
        send(f"Your ping {_ba.get_client_ping(clientid)}ms ", clientid)
    elif arguments[0] == 'all':
        pingall(clientid)
    else:
        try:
            session = ba.internal.get_foreground_host_session()

            for index, player in enumerate(session.sessionplayers):
                name = player.getname(full=True, icon=False),
                if player.inputdevice.client_id == int(arguments[0]):
                    ping = _ba.get_client_ping(int(arguments[0]))
                    send(f" {name}'s ping {ping}ms", clientid)
        except:
            return


def stats(ac_id, clientid):
    stats = mystats.get_stats_by_id(ac_id)
    if stats:
        reply = "Score:"+str(stats["scores"])+"\nGames:"+str(stats["games"])+"\nKills:"+str(
            stats["kills"])+"\nDeaths:"+str(stats["deaths"])+"\nAvg.:"+str(stats["avg_score"])
    else:
        reply = "Not played any match yet."

    _ba.pushcall(Call(send, reply, clientid), from_other_thread=True)


def fetch_send_stats(ac_id, clientid):
    _thread.start_new_thread(stats, (ac_id, clientid,))

def pingall(clientid):
    """Returns The List Of Players Clientid and index"""

    p = u'{0:^16}{1:^34}ms'
    seprator = '\n______________________________\n'

    list = p.format('Name', 'Ping (ms)')+seprator
    session = ba.internal.get_foreground_host_session()

    for index, player in enumerate(session.sessionplayers):
        list += p.format(player.getname(icon=True),
                         _ba.get_client_ping(int(player.inputdevice.client_id)))+"\n"

    send(list, clientid)

def list(clientid):
    """Returns The List Of Players Clientid and index"""

    p = u'{0:^16}{1:^15}{2:^10}'
    seprator = '\n______________________________\n'

    list = p.format('Name', 'Client ID', 'Player ID')+seprator
    session = ba.internal.get_foreground_host_session()

    for index, player in enumerate(session.sessionplayers):
        list += p.format(player.getname(icon=False),
                         player.inputdevice.client_id, index)+"\n"

    send(list, clientid)


def accountid_request(arguments, clientid, accountid):
    """Returns The Account Id Of Players"""

    if arguments == [] or arguments == ['']:
        send(f"Your account id is {accountid} ", clientid)

    else:
        try:
            session = ba.internal.get_foreground_host_session()
            player = session.sessionplayers[int(arguments[0])]

            name = player.getname(full=True, icon=True)
            accountid = player.get_v1_account_id()

            send(f" {name}'s account id is '{accountid}' ", clientid)
        except:
            return
