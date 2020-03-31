#!/bin/bash
source ~/feed/bin/activate
.~/feedBot/news2rsscmd.py collect $TG_ADMIN_USER_ID
.~/feedBot/news2rsscmd.py digest $TG_ADMIN_USER_ID