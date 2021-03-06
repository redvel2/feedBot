#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from urllib.parse import urlencode
import requests
from pprint import pformat, pprint
import json
from telegram import Bot
from models.models import *
from mongoengine import connect, DoesNotExist
from settings import *
import click
import html2text
from time import mktime
from datetime import datetime

import time
from newsworker.extractor import FeedExtractor

from settings import *
import feedparser

from utils import get_feed_context, save_image

requests.adapters.DEFAULT_RETRIES = 5


class FeedManager:
    def __init__(self):
        connect('feedrebot', host=MONGO_HOST, port=MONGO_PORT)

    def init(self, username):
        user = User(userid=username, name='@' + username, fd_per_ch=100, max_ch=100)
        user.save()
        print('User %s set as admin' % (username))

    def send(self, bot, chat_id, text):
        try:
            bot.send_message(chat_id=chat_id, text=text)
            time.sleep(BOT_TIMEOUT)
        except:
            logging.info('Exception during sending message. Timeout %d seconds' % (BOT_EXC_TIMEOUT))
            time.sleep(BOT_EXC_TIMEOUT)
            bot.send_message(chat_id=chat_id, text=text)


    def collect(self, username):
        if username is not None and username != 'all':
            try:
                user = User.objects.get(userid=username)
                feeds = Feed.objects(user=user)
            except DoesNotExist as ex:
                logging.info('User not found')
                return
        else:
            feeds = Feed.objects()
        for f in feeds:
            logging.info('Processing feed %s' % (f.url))
            if f.feedtype == FEED_TYPE_RSS:
                data = feedparser.parse(f.url)
                if len(data['entries']) == 0:
                    logging.info('Empty feed')
                    continue
                f.last_updated = datetime.now()
                try:
                    lastpost_guid = data['entries'][0]['id'] if 'id' in data['entries'][0].keys() else data['entries'][0][
                    'link']
                except KeyError as ex:
                    logging.info('Feed without urls')
                    continue

                if lastpost_guid == f.lastpost_guid:
                    logging.info("Feed doesn't need update")
                    continue
                for rec in reversed(data['entries']):
                    rec_id = rec['id'] if 'id' in rec.keys() else rec['link']
                    try:
                        #                print(rec)
                        r = Post.objects.get(feed=f, postid=rec_id)
                        logging.info('Post %s already consumed' % (rec_id))
                    except DoesNotExist as ex:
                        p = Post(feed=f)
                        p.postid = rec_id
                        p.url = rec['link']
                        p.title = rec['title'][:500]
#                        import pprint
#                        pprint.pprint(rec)
                        p.published = datetime.fromtimestamp(
                            mktime(rec['published_parsed'])) if 'published_parsed' in rec.keys() else datetime.now()
                        p.description = rec['summary'][:5000]
                        if 'summary_detail' in rec.keys() and rec['summary_detail']['type'] == 'text/html':
                            text = html2text.html2text(rec['summary']) + '\n' + rec['link']
                        else:
                            text = rec['summary'] + '\n' + rec['link']
                        p.isposted = False
                        p.save()
                        logging.info('Post consumed %s' % (rec_id))
                f.lastpost_guid = lastpost_guid
            elif f.feedtype == FEED_TYPE_HTML or f.feedtype == FEED_TYPE_TG_CHANNEL:
                ext_context = get_feed_context(f)

                ext = FeedExtractor(filtered_text_length=150)
                data, session = ext.get_feed(f.url, **ext_context)
                #            print(feed)
                items = data["items"]
                if len(items) == 0:
                    logging.info('Empty feed')
                    continue

                if f.feedtype == FEED_TYPE_TG_CHANNEL:
                    items = list(reversed(items))

                f.last_updated = datetime.now()
                lastpost_guid = items[0]['unique_id']
                if items[0]['unique_id'] == f.lastpost_guid:
                    logging.info("Feed doesn't need update")
                    continue
                for rec in reversed(items):
                    if not rec['title']:
                        logging.info('Skipping entry since no title')
                        continue
                    try:
                        #                print(rec)
                        r = Post.objects.get(feed=f, postid=rec['unique_id'])
                        logging.info('Post %s already consumed' % (rec['unique_id']))
                    except DoesNotExist as ex:
                        preview_image_path = None
                        images = rec["extra"]["images"]
                        logging.info("-------Found {0} images".format(len(images)))
                        if len(images) == 1:
                            preview_image_path = save_image(images[0])
                        p = Post(feed=f)
                        p.postid = rec['unique_id']
                        p.url = rec['link']
                        p.title = rec['title'][:500]
                        p.published = rec['pubdate']
                        p.description = rec['description']
                        p.isposted = False
                        p.preview_image = preview_image_path
                        p.save()
                        logging.info('Post consumed %s' % (rec['unique_id']))
                f.lastpost_guid = lastpost_guid
            f.save()

    def digest(self, username):
        bot = Bot(open(BOT_KEY, 'r').read().replace("\n", ""))

        if username is not None and username != 'all':
            try:
                user = User.objects.get(userid=username)
                feeds = Feed.objects(user=user)
            except DoesNotExist as ex:
                logging.info('User not found')
                return
        else:
            feeds = Feed.objects()
        for f in feeds:
            posts = Post.objects(feed=f, isposted=False).order_by('published')
            logging.info('Feed %s not posted %d' % (f.url, len(posts)))
            if len(posts) == 0:
                logging.info('No new posts')
                continue
            today = datetime.now()
            pcount = 0
            if f.feedmode == 555:  # FEED_MODE_DIGEST:
                d_title = 'Дайджест от %d.%d.%d по %s\n---\n' % (today.day, today.month, today.year, f.url)
                text = '' + d_title
                for p in posts:
                    #            title = p.title if len(p.title) < 50 else p.title[:50] + '...'
                    title = p.title
                    text += title + '\n' + p.url + '\n\n'
                    pcount += 1
                    if pcount % DIGEST_LIMIT == 0:
                        logging.info('Send message to channel %s ' % (f.channel.chid))
                        self.send(bot, chat_id='@' + f.channel.chid, text=text)
                        text = '' + d_title

                if pcount % DIGEST_LIMIT != 0:
                    logging.info('Send message to channel %s ' % (f.channel.chid))
                    self.send(bot, chat_id='@' + f.channel.chid, text=text)
                logging.info('Updating posts in database')
                for p in posts:
                    p.isposted = True
                    p.save()
            else:
                #       elif f.feedmode == FEED_MODE_FULL:
                # Send only last 5 posts   
                for p in posts[0:5]:
                    title = p.title
                    text = title + '\n' + p.url + '\n\n' + html2text.html2text(p.description)[:500]
                    try:
                        logging.info('Send message to channel %s ' % (f.channel.chid))
                        logging.info(text)
                        self.send(bot, chat_id='@' + f.channel.chid, text=text)
                        p.isposted = True
                        p.save()
                    except:
                        pass
                logging.info('Updating all other posts in database')
                posts = Post.objects(feed=f, isposted=False).order_by('published')
                for p in posts:
                    p.isposted = True
                    p.save()

    def purge(self, objects):
        if objects == 'posts':
            logging.info('Posts purges')
            Post.objects().delete()
            for f in Feed.objects():
                f.lastpost_guid = ""
                f.save()
        elif objects == 'feeds':
            logging.info('Feeds purges')
            Post.objects.delete()
            Feed.objects.delete()
        else:
            logging.info('Unknown objects. Possible values: posts, feeds, channels')

@click.group()
def cli1():
    pass


@cli1.command()
@click.argument('username', default=None)
def collect(username=None):
    """Collects posts from all news"""
    man = FeedManager()
    man.collect(username)



@click.group()
def cli2():
    pass


@cli2.command()
@click.argument('username', default=None)
def digest(username=None):
    """Sends digests of the news"""
    man = FeedManager()
    man.digest(username)






@click.group()
def cli3():
    pass


@cli3.command()
@click.argument('objects')
def purge(objects):
    """Removes unused data"""
    man = FeedManager()
    man.purge(objects)



@click.group()
def cli4():
    pass


@cli4.command()
def update():
    """Collects and updates all feeds"""
    man = FeedManager()
    man.collect(username='all')
    man.digest(username='all')

@click.group()
def cli5():
    pass


@cli5.command()
@click.argument('username', default=None)
def init(username=None):
    """Initializes bot with admin name"""
    man = FeedManager()
    man.init(username)



cli = click.CommandCollection(sources=[cli5, cli1, cli2, cli3, cli4])

if __name__ == '__main__':
    cli()
