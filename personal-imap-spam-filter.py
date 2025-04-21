#! /usr/bin/env python

from configparser  import ConfigParser
from imapclient import IMAPClient
from email.header import Header, decode_header, make_header
from email import message_from_bytes
import subprocess
import time
from datetime import datetime
import sys
import os

# open config file
config = ConfigParser()
try:
    config.read(os.path.dirname((__file__)) + "/pisf.conf")
except:
    sys.exit('Problem reading config file')

# set config variables
try:
    IMAP_SERVER       = config['pisf']['IMAP_SERVER']
    IMAP_USERNAME     = config['pisf']['IMAP_USERNAME']
    IMAP_PASSWORD     = config['pisf']['IMAP_PASSWORD']
    SA_CHECK          = config['pisf']['SA_CHECK'].split(' ')
    SA_SPAMC          = config['pisf']['SA_SPAMC'].split(' ')
    MAILBOX_TO_CHECK  = config['pisf']['MAILBOX_TO_CHECK']
    MESSAGES_TO_CHECK = config['pisf']['MESSAGES_TO_CHECK'].split(' ')
    CHECK_FREQUENCY   = int(config['pisf']['CHECK_FREQUENCY'])
    SPAM_FLAG         = config['pisf']['SPAM_FLAG']
    SPAM_VALUE        = config['pisf']['SPAM_VALUE']
    SPAM_MAILBOX      = config['pisf']['SPAM_MAILBOX']
except KeyError as e:
    sys.exit("Key error in config file: " + str(e))
except:
    sys.exit("Error while setting configuration")

def ping_spamd():
    p = subprocess.run(SA_CHECK, capture_output=True)
    return p.returncode == 0
    
def run_spamc(email_content):
    p = subprocess.run(SA_SPAMC, input=email_content, text=True, capture_output=True)
    return [ p.returncode, str(p.stdout.strip()) ]

def process_emails():
    last_msgids = []
    with IMAPClient(IMAP_SERVER) as client:
        client.login(IMAP_USERNAME, IMAP_PASSWORD)
        client.select_folder(MAILBOX_TO_CHECK)

        try:
            while True:
                current_msgids = []
                # Fetch unread emails
                messages = client.search(MESSAGES_TO_CHECK)
                for msgid in messages:
                    current_msgids.append(msgid)
                    if msgid in last_msgids:
                        continue

                    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " check e-mail with msgid = " + str(msgid))
                    raw_message = client.fetch([msgid], ["RFC822"])[msgid][b"RFC822"]
                    try:
                        email_content = raw_message.decode("utf-8")
                    except:
                        email_content = False
                    try:
                        msg = message_from_bytes(raw_message)
                    except:
                        print("Problem running 'message_from_bytes' - here the 'raw_message'")
                        print("--------------------------------------------------------------------------------")
                        print(raw_message)
                        print("--------------------------------------------------------------------------------")
                        continue
                    print("  Date:    " + str(make_header(decode_header(msg['Date']))))
                    print("  From:    " + str(make_header(decode_header(msg['From']))))
                    print("  Subject: " + str(make_header(decode_header(msg['Subject'].replace('\r\n', '')))))

                    # Restore unread (unseen) status
                    client.remove_flags([msgid], [b"\\Seen"])

                    # if e-mail already marked as spam, move it to Junk/Hostpoint
                    if msg[SPAM_FLAG] == SPAM_VALUE:
                        print("  => moved to " + SPAM_MAILBOX + " (since already spam)\n")
                        client.move([msgid], SPAM_MAILBOX)
                    elif email_content == False:
                        print("  => e-mail could not be decodes?!?\n")
                    else:
                        [ sa_exit_code, sa_summary ] = run_spamc(email_content)
                        if sa_exit_code == 1:
                            print("  => moved to " + SPAM_MAILBOX + " (" + sa_summary + ")\n")
                            client.move([msgid], SPAM_MAILBOX)
                        elif sa_exit_code == 0:
                            print("  => not recognized as spam (" + sa_summary + ")\n")
                        else:
                            print("  => spamd exit code " + str(sa_exit_code)) + "\n"

                last_msgids = current_msgids
                sys.stdout.flush()
                time.sleep(CHECK_FREQUENCY)

        except KeyboardInterrupt:
            print("\r", end="")
            print("Stopping imap-spamassassin.py...\n")
            sys.stdout.flush()
            client.logout()

if __name__ == "__main__":
    if ping_spamd():
        process_emails()
    else:
        print("The 'spamd' is not running...\n");
