# Overview

Mailhack is an email management tool that takes a "white list" approach to 
email management. Only emails from senders who have been explicitly allowed 
will stay in your inbox.  Emails from non-whitelisted senders are put in a 
"Trash" folder which is purged after 90 days.  You can drag an email from the 
"Trash" folder to the "Permit" folder to add its sender to the white list and 
you can drag an email from your inbox to the "Block" folder to remove its 
sender from the white list. 

This approach has proven surprisingly useful for me.  I hope it will help you 
spend less time managing email and more time doing anything else!

# Set Up

Mailhack is written in Python 2 and requires the "imapclient" package.

```
pip install imapclient
```

Next, provide the connection information for all of the accounts you want to 
manage.  An example is shown below:

```json
{
   "accounts" : [
      {
         "description" : "Home",
         "server" : "imap.secureserver.net",
         "port": 993,
         "username" : "fred@aol.com",
         "password" : "ABC112233"
      },
      {
         "description" : "Work",
         "server" : "imap.gmail.com",
         "port": 993,
         "username" : "fred@acme.com",
         "password" : "DEF332211"
      }
   ]
}
```

You can optionally pre-populate the whitelist.  To do so, create a file called 
"whitelist.json" with content similar to that shown below.

```
[
   "nana@gmail.com",
   "harry@acme.com",
   "nancy99@gmail.com"
]
```

Creating `whitelist.json` is optional.  If you do not create it, `mailhack.py` 
will create it and manage its contents automatically based on the contents of t
he `Mailhack/Permit` and `Mailhack/Block` IMAP folders.

That is the only setup required.  It is recommended that you schedule 
`mailhack.py` to run every 20-30 minutes and `purge.py` to run once per week.

# Usage

Mailhack is a pair of python scripts that you can run from anywhere that has 
connectivity to the internet.  

`mailhack.py`

Connects to your IMAP server or servers using the information in 
`mailhack.json`. The first time it connects it will create the following 
folders: `Mailhack/Block`, `Mailhack/Permit` and `Mailhack/Trash`.  

First the white list (`whitelist.json`) is updated as follows.  For emails in 
`Mailhack/Permit`, the senders are added to the white list and the emails 
themselves are moved to the in box.  For emails in `Mailhack/Block`, their 
senders are removed from the whitelist if present and the emails themselves 
are moved to `Mailhack/Trash`.

Next the in box is processed.  All emails in the inbox from senders not on the 
white list are moved to the `Mailhack/Trash` folder.  All emails in 
`Mailhack/Trash` with senders that are on the white list are moved to the inbox.

`purge.py`

Connects to your IMAP server and processes the `Mailhack/Trash` folder.  Emails 
sent more than 90 days ago are deleted.