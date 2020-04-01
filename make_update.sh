#!/bin/bash
source ~/feed/bin/activate
/./home/viktor/feedBot/news2rsscmd.py collect $TG_ADMIN_USER_ID
/./home/viktor/feedBot/news2rsscmd.py digest $TG_ADMIN_USER_ID
deactivate