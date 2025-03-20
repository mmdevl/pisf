#! /usr/bin/env python

from configparser  import ConfigParser
from imapclient import IMAPClient
from email.header import Header, decode_header, make_header
from email import message_from_bytes
import subprocess
import time
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
    SA_LEARN          = config['pisf']['SA_LEARN'].split(' ')
    SPAMBOX_TO_CHECK  = config['pisf']['SPAMBOX_TO_CHECK']
    SPAM_TO_CHECK     = config['pisf']['SPAM_TO_CHECK']
except KeyError as e:
    sys.exit("Key error in config file: " + str(e))
except:
    sys.exit("Error while setting configuration")

def learn_spams():
    with IMAPClient(IMAP_SERVER) as client:
        client.login(IMAP_USERNAME, IMAP_PASSWORD)
        client.select_folder(SPAMBOX_TO_CHECK)

        try:
            # Fetch unread emails
            messages = client.search(SPAM_TO_CHECK)
            for msgid in messages:

                print("Learning as SPAM e-mail with msgid = " + str(msgid) + "...")
                raw_message = client.fetch([msgid], ["RFC822"])[msgid][b"RFC822"]
                out = os.path.dirname((__file__)) + "/spam-learned/" + str(time.time())
                f = open(out, 'w')
                f.write(raw_message.decode('utf-8'))
                f.close()

                client.delete_messages(msgid)
                client.expunge()

                p = subprocess.run(SA_LEARN, input=raw_message.decode('utf-8'), text=True, capture_output=True)
                print(p.stdout.strip())
                
                time.sleep(1)
            sys.stdout.flush()

        except KeyboardInterrupt:
            print("\r", end="")
            print("Stopping imap-spamassassin.py...\n")
            sys.stdout.flush()
            client.logout()

if __name__ == "__main__":
    learn_spams()
