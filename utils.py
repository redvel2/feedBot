from models.models import FEED_TYPE_RSS, FEED_TYPE_HTML, FEED_TYPE_TG_CHANNEL
import requests
import uuid
from settings import TMP_MEDIA_PATH
from os import path
import os

def tg_id2url(id):
    if id.startswith("@"):
        return "https://t.me/s/{0}".format(id[1:])
    return None


def tg_preproc(document):
    "Replaces post time with the actual date of post"
    for el in document.xpath("//time"):
        dt = el.get("datetime")
        if dt is not None:
            el.text = dt
    return document


def get_feed_type(feed, url):
    if url.startswith("https://t.me"):
        return FEED_TYPE_TG_CHANNEL
    return FEED_TYPE_HTML


def get_feed_context(feed):

    exec_context = {}

    if feed.feedtype == FEED_TYPE_TG_CHANNEL:
        exec_context["document_preprocessor"] = tg_preproc

    return exec_context

def save_image(url):
    image_name = uuid.uuid4().hex + ".jpg"
    print("-------------SAVE IMAGE ", url)
    try:
        raw = requests.get(url, stream=True)
        if not path.isdir(TMP_MEDIA_PATH):
            os.makedirs(TMP_MEDIA_PATH)
        with open(path.join(TMP_MEDIA_PATH, image_name), "wb") as fd:
            for chunk in raw.iter_content(chunk_size=128):
                fd.write(chunk)
    except:
        import traceback
        traceback.format_exc()
        return None
    return image_name