# coding=utf-8

"""
API ENDPOINTS IN USE

/GetChase
/UpdateChase
/AddChase
/ListChases
/DeleteChase

"""

from __future__ import absolute_import, division, generator_stop, print_function, unicode_literals

import html
import json
from pathlib import Path
import shlex
import traceback
from urllib.parse import urlparse

import pendulum
import requests
import twython

from sopel import plugin, tools
from sopel.config.types import ListAttribute, StaticSection, ValidatedAttribute


sopel_instance = None
LOGGER = tools.get_logger("chasebot")

CHANNELS = ["#Chases", "#𝓉𝓌𝑒𝓇𝓀𝒾𝓃"]
FOLLOW_LIST = [
    '108746627',            # @PCALive
    '37162208',             # @LAPolicePursuit
    '768202337764597760',   # @ChaseAlertsOnly
    '3259117872',           # @LACoScanner
    '162814209',            # @Stu_Mundel
    '277899934',            # @damonheller (smokenscan)
    '34743251',             # @SpaceX
    '44196397',             # @elonmusk
    '1071963556567048192',  # @efnetchasebot
]

APP_PREFIX = "\x02[ChaseApp]\x02 "
BOT_PREFIX = "\x02[ChaseBot]\x02 "

APP_STORE_LINKS = [
    {"os": "Android", "url": "https://play.google.com/store/apps/details?id=com.carverauto.chaseapp"},
    {"os": "iOS", "url": "Coming Soon™"},
]

CHASES = {}


class ChaseAppSection(StaticSection):
    chaseapp_api_url = ValidatedAttribute("chaseapp_api_url", str)
    chaseapp_api_key = ValidatedAttribute("chaseapp_api_key", str)
    chaseapp_mods = ListAttribute("chaseapp_mods")
    twitter_consumer_token = ValidatedAttribute("twitter_consumer_token", str)
    twitter_consumer_secret = ValidatedAttribute("twitter_consumer_secret", str)
    twitter_access_token = ValidatedAttribute("twitter_access_token", str)
    twitter_access_secret = ValidatedAttribute("twitter_access_secret", str)
    pushover_token = ValidatedAttribute("pushover_token", str)
    pushover_user = ValidatedAttribute("pushover_user", str)


class MyStreamer(twython.TwythonStreamer):
    global CHANNELS
    global CHASES
    global sopel_instance

    def on_success(self, status):
        try:
            if not status.get('in_reply_to_status_id') and not status.get('in_reply_to_user_id_str'):
                if not status.get('retweeted') and 'RT @' not in status.get('text', ''):
                    if not status.get('user'):
                        return
                    text = "\x02@{}\x02 ({}): {}".format(
                        status['user']['screen_name'],
                        status['user']['name'],
                        status.get('extended_tweet', {}).get('full_text') or status['text']
                    )
                    # urls = status['entities'].get('urls')
                    try:
                        if status.get('quoted_status'):
                            text += " (\x02@{}\x02: {} - {})".format(
                                status['quoted_status']['user']['screen_name'],
                                status['quoted_status']['text'],
                                status['quoted_status_permalink'].get('url'),
                            )
                            # urls = status['quoted_status']['entities'].get('urls')
                    except Exception as e:
                        LOGGER.error(f"Error parsing quoted status: {e}")

                    text = text.replace('\n', ' ')
                    text = text.strip()
                    text = html.unescape(text)

                    LOGGER.info(f"New Tweet! - {text}")

                    valid_tweets = ["chase", "pursuit"]
                    found_valid = True
                    if status['user']['id'] == 277899934:
                        found_valid = False
                        for word in valid_tweets:
                            if word in text.lower():
                                found_valid = True
                                break
                    if found_valid:
                        # if status['user']['id'] == 3259117872:
                        #     if "ready?" in text.lower():

                        #         if not CHASES.get('current'):
                        #             CHASES['current'] = {
                        #                 'active': True,
                        #                 'time': status['created_at']
                        #             }
                        #         else:
                        #             now = pendulum.now()
                        #             if now.diff(pendulum.parse(CHASES['current']['time'], strict=False)).in_hours() >= 6:
                        #                 CHASES['current'] = {
                        #                     'active': True,
                        #                     'time': status['created_at']
                        #                 }
                        # if status['user']['id'] not in FOLLOW_LIST[6:]:
                        #     chase = False
                        #     for word in valid_tweets:
                        #         if word in text.lower():
                        #             chase = True
                        #     if CHASES.get('current', {}).get('active'):
                        #         if urls and chase:
                        #             url = urls[0]['url']
                        #             url = requests.get(url).url
                        #             CHASES['current']['url'] = url
                        #             CHASES['current']['name'] = "Chase"
                        #             CHASES['current']['desc'] = text
                        #             CHASES['current']['network'] = "TBD"
                        #             CHASES['current']['first_run'] = True
                        #     if CHASES.get('current', {}).get('first_run'):
                        #         headers = {
                        #             'User-Agent': 'chasebot@efnet (via twitter) v1.0',
                        #             'From': 'chasebot@cottongin.xyz',
                        #             'X-ApiKey': sopel_instance.config.chaseapp.chaseapp_api_key
                        #         }

                        #         payload = {
                        #             "name": CHASES['current']['name'],
                        #             "url": CHASES['current']['url'],
                        #             "desc": CHASES['current']['desc'],
                        #             "URLs": [
                        #                 {"network": CHASES['current']['network'], "url": ""}
                        #             ],
                        #             "live": True
                        #         }

                        #         api_endpoint = sopel_instance.config.chaseapp.chaseapp_api_url + "/AddChase"

                        #         data = requests.post(api_endpoint, headers=headers, json=payload)

                        #         CHASES['current']['id'] = data.text
                        #         LOGGER.info("UUID created for a new chase: {}".format(data.text))
                        #         CHASES['current']['first_run'] = False

                        for channel in CHANNELS:
                            sopel_instance.say(text, channel)
        except Exception as e:
            LOGGER.error(f"Unhandled Tweet! - {e}")
            result = traceback.format_exc()
            result = "".join(result)
            if len(result) > 1024:
                result = result[-1024:]
            post_data = {
                'token': sopel_instance.config.chaseapp.pushover_token,
                'user': sopel_instance.config.chaseapp.pushover_user,
                'message': result,
                'title': 'Chasebot is BROKEN - Unhandled'
            }
            requests.post("https://api.pushover.net/1/messages.json", data=post_data)

    def on_error(self, status_code, data):
        LOGGER.error(f"Twitter ERROR: {status_code}")
        if len(data) > 1024:
            result = data[-1024:]
        post_data = {
            'token': sopel_instance.config.chaseapp.pushover_token,
            'user': sopel_instance.config.chaseapp.pushover_user,
            'message': result,
            'title': f'Chasebot is BROKEN - Twitter ({status_code})'
        }
        requests.post("https://api.pushover.net/1/messages.json", data=post_data)


api = None
myStream = None
myStreamListener = None
firstStart = True


def configure(config):
    config.define_section("chaseapp", ChaseAppSection, validate=False)
    config.chaseapp.configure_setting("chaseapp_api_url", "Root path of API service")
    config.chaseapp.configure_setting("chaseapp_api_key", "API key for ChaseApp")
    config.chaseapp.configure_setting("chaseapp_mods", "List of authorized users for sensitive commands")
    config.chaseapp.configure_setting("twitter_consumer_token", "Twitter API Consumer Token")
    config.chaseapp.configure_setting("twitter_consumer_secret", "Twitter API Consumer Secret")
    config.chaseapp.configure_setting("twitter_access_token", "Twitter API Access Token")
    config.chaseapp.configure_setting("twitter_access_secret", "Twitter API Access Token")
    config.chaseapp.configure_setting("pushover_token", "Pushover API Token")
    config.chaseapp.configure_setting("pushover_user", "Pushover API User Hash")


def setup(bot):
    bot.config.define_section("chaseapp", ChaseAppSection)
    global CHASES
    if not CHASES:
        try:
            with open(str(Path.home()) + '/chases_db.json', 'r') as handle:
                b = json.load(handle)
            CHASES = b
        except Exception as e:
            LOGGER.debug(e)
            pass


def shutdown(bot):
    try:
        with open(str(Path.home()) + '/chases_db.json', 'w') as handle:
            json.dump(CHASES, handle)
    except Exception as e:
        LOGGER.debug(e)
        pass


def _parseargs(passed_args):
    if passed_args:
        args = shlex.split(passed_args)

        options = {
            k: True if v.startswith('-') else v
            for k, v in zip(args, args[1:] + ["--"]) if k.startswith('-')
        }

        extra = args
        if options:
            extra = []
            for k, v in options.items():
                for arg in args:
                    if arg != k and arg != v:
                        extra.append(arg)

        options['extra_text'] = ' '.join(extra)
        return options
    else:
        return {}


@plugin.interval(10)
@plugin.thread(True)
@plugin.output_prefix(BOT_PREFIX)
def twitter_thread(bot):
    global firstStart
    if not firstStart:
        return

    global sopel_instance
    global api
    global myStream
    global myStreamListener
    sopel_instance = bot

    LOGGER.info(f"{BOT_PREFIX} Started for channels: {', '.join(CHANNELS)}")
    firstStart = False

    consumer_token = bot.config.chaseapp.twitter_consumer_token
    consumer_secret = bot.config.chaseapp.twitter_consumer_secret
    access_token = bot.config.chaseapp.twitter_access_token
    access_token_secret = bot.config.chaseapp.twitter_access_secret

    # Authenticate to Twitter
    stream = MyStreamer(consumer_token, consumer_secret,
                        access_token, access_token_secret)

    try:
        twitter = twython.Twython(consumer_token, consumer_secret, oauth_version=2)
        api_token = twitter.obtain_access_token()
        api = twython.Twython(consumer_token, access_token=api_token)
    except Exception as e:
        LOGGER.error(f"I couldn't authorize with twitter (regular API): {e}")

    try:
        stream.statuses.filter(follow=FOLLOW_LIST)
    except Exception as e:
        stream.disconnect()
        LOGGER.error(f"{BOT_PREFIX} - Twiter Stream Error. Restarting. \n{e}")
        firstStart = True

    LOGGER.info(f"{BOT_PREFIX} Stopped")
    stream.disconnect()
    firstStart = True


@plugin.command('help', 'h')
@plugin.example('.help')
@plugin.output_prefix(BOT_PREFIX)
def chasebot_help(bot, trigger):
    """Sends help link to the chasebot documentation"""
    suffix = ""
    if "leku" in trigger.nick.lower():
        suffix = " - you are beyond help though"
    return bot.say(f"https://bot.chaseapp.tv/{suffix}")


@plugin.command('applinks', 'applink', 'app')
@plugin.example('.applinks')
@plugin.output_prefix(APP_PREFIX)
def send_links(bot, trigger):
    """Sends links to the ChaseApp store pages"""
    return bot.say("Download ChaseApp here: {}".format(
        " | ".join("{}: {}".format(link['os'], link['url']) for link in APP_STORE_LINKS)
    ))


@plugin.command('supportus', 'patreon', 'giveusmoney')
@plugin.example('.supportus')
@plugin.output_prefix(APP_PREFIX)
def support_links(bot, trigger):
    """Sends patreon links"""
    return bot.say("Support our development team here: {}".format(
        "https://www.patreon.com/chaseapp"
    ))


@plugin.output_prefix(APP_PREFIX)
def _fetch_api_list(bot, caller="bot", live_mode=False, index=0):
    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(caller),
        'From': 'chasebot@cottongin.xyz'
    }

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/ListChases"

    try:
        data = requests.get(api_endpoint, headers=headers).json()
        # data = sorted(data, key=lambda i: i['CreatedAt'])
    except Exception as err:
        LOGGER.error(err)
        return bot.say("Something went wrong fetching data")

    if live_mode:
        data = [chase for chase in data if chase.get('Live')]
    else:
        data = [data[index]]

    if not data:
        return bot.say("No chases found :(")

    return data


def _get_specific_chase(bot, chase_id):
    if not chase_id:
        return

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/GetChase"

    payload = {
        "id": chase_id
    }

    try:
        data = requests.post(api_endpoint, json=payload).json()
    except Exception as err:
        LOGGER.error(err)
        data = None

    return data


@plugin.command('getchase', 'get', 'gc')
@plugin.example('.get [ChaseApp ID]')
@plugin.output_prefix(APP_PREFIX)
def get_chase(bot, trigger):
    """Get chase

    Allows you to fetch a specific chase from the ChaseApp API. Requires a
    ChaseApp ID (^list --showid)

        e.g. ^get [ChaseApp ID]
    """

    if not trigger.group(2):
        return bot.reply("I need a chase ID")

    chase = _get_specific_chase(bot, trigger.group(2))

    if not chase:
        return bot.say("No chase found by that ID")

    output = ""
    for key, value in chase.items():
        output += "{}: {}, ".format(key, value)

    bot.say(output)


@plugin.rate(user=3)
@plugin.command('vote', 'v')
@plugin.example('.vote')
@plugin.output_prefix(APP_PREFIX)
def vote_on_chase(bot, trigger):
    """Vote on chases

    Allows users to vote on live chases!

        e.g. ^vote
    """

    chases = _fetch_api_list(bot, caller=trigger.nick, live_mode=True, index=0) or []
    if not chases:
        return bot.reply("No live chase to vote on! Sorry")

    chase = chases[0]

    payload = {
        'id':       '{}'.format(chase['ID']),
        'votes':    int(chase['Votes']) + 1,
        'name':     '{}'.format(chase['Name']),
        'desc':     '{}'.format(chase['Desc']),
        'networks':  chase['Networks'],
        'createdAt': chase['CreatedAt'],
        'live':      chase['Live']
    }

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz',
        'X-ApiKey': bot.config.chaseapp.chaseapp_api_key
    }

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/UpdateChase"

    data = requests.post(api_endpoint, headers=headers, json=payload)
    if data.status_code != 200:
        return bot.say("Something went wrong")


@plugin.command('listchases', 'list', 'lc', 'chases', 'chase', 'last', 'c', 'l')
@plugin.example('.list --showlive')
@plugin.output_prefix(APP_PREFIX)
def list_chases(bot, trigger):
    """List chases

    Pass `--showlive` to see only active chases. Pass `--index [#]`
    to fetch a specific chase (working backwards from most recent).

        e.g. ^list --index 2
             ^list --showlive
             ^list --index 4 --showid
    """

    show_id = False
    list_live = False

    index = 0
    if trigger.group(2):
        args = _parseargs(trigger.group(2))
        index = int(args.get('--index', 1)) - 1
        show_id = args.get('--showid')
        list_live = args.get('--showlive')

    chases = _fetch_api_list(bot, caller=trigger.nick, live_mode=list_live, index=index) or []

    for chase in chases:
        started = pendulum.parse(chase.get('CreatedAt'))
        ended = pendulum.parse(chase.get('EndedAt'))
        duration = abs(ended.int_timestamp - started.int_timestamp)
        if duration <= 604800:
            duration_string = " | Duration: {}".format(ended.diff(started).in_words())
        else:
            if chase['Live']:
                ended = pendulum.now()
                duration = abs(ended.int_timestamp - started.int_timestamp)
                duration_string = " | Duration: {}".format(ended.diff(started).in_words())
            else:
                duration_string = ""
        bot.write(['PRIVMSG', trigger.sender], "({recent}{date}) \x02{name}\x02 - {desc} | {status} | 🍩 {votes} donut{donuts}{duration}".format(
            recent="\x1FMost Recent\x0F - " if (chase == chases[0] and index == 0) else "",
            name=chase['Name'],
            desc=chase['Desc'],
            date=pendulum.parse(chase['CreatedAt']).in_tz('US/Pacific').format("MM/DD/YYYY h:mm A zz"),
            votes=chase['Votes'],
            status="\x02\x0309LIVE\x03\x02" if chase['Live'] else "\x0304Inactive\x03",
            donuts="" if chase['Votes'] == 1 else "s",
            duration=duration_string
        ))

        num_links = 5
        links = []
        networks = chase.get('Networks', [{}])
        networks = sorted(networks, key=lambda i: i['Tier'], reverse=True)
        for network in networks[:(num_links + 1)]:
            name = ""
            if network.get('Name'):
                name += network.get('Name')
            if network.get('Tier', 0) == 1:
                name = "{}{}".format(
                    "(Primary) " if name else "Primary",
                    name
                )
            links.append("\x02{}\x02 {}".format(
                name,
                network.get('URL', 'no link found')
            ))

        if chase['Live']:
            if len(chase.get('Networks', [{}])) > (num_links + 1):
                slug = "More links @ "
            else:
                slug = ""
            links.append("{}https://chaseapp.tv/chase/{}".format(
                slug,
                chase['ID']))

        for link in links:
            bot.write(['PRIVMSG', trigger.sender], link)
            # bot.say(link)

        if show_id:
            bot.say(f"(ID) {chase['ID']}")


@plugin.command('endchase', 'end', 'ec')
@plugin.example('.end')
@plugin.output_prefix(APP_PREFIX)
def end_chase(bot, trigger):
    """Update chases

    Assumes the most recent chase unless `--id [ChaseApp chase ID]` is passed.
    Fields to modify (`--title "[new title]"` or `--url [new url]` etc). Any
    values that contain spaces must be surrounded by quotation marks. If
    `--networks` is passed, will assume you want to append a new network and
    url to the chase, pass `--edit` with an existing `--name` to edit an
    existing network.
    !*Only specific users are granted access to this command.*!

    Valid fields:
    ```
        --title "LA Chase"
        --desc "some description here"
        --live true(default)/false
        --networks
            --name ABC7
            --url https://abc7.com/watch/live/
            --tier 1
            --edit
                --name ABC7 --newname "ABC 7"
                --url https://abc7.com/watch/live
                --tier 0
                --votes 0
    ```

        e.g. ^update --title "LA Chase"
             ^update --id 7e171514-9c51-11ea-b6a3-0b58aa4cbde4 --live true
             ^update --networks --name CBSLA --url https://cbs.com
             ^update --networks --edit --name CBSLA --tier 2 --votes 0
    """

    check = trigger.hostmask.split("!")[1]
    if check not in bot.config.chaseapp.chaseapp_mods:
        LOGGER.error("{} tried to update a chase".format(trigger.hostmask))
        return bot.reply("You're not authorized to do that!")

    # if not trigger.group(2):
    #     return bot.reply("I need some info to update")

    args = _parseargs(trigger.group(2))
    # if not args:
    #     return bot.reply("Something went wrong parsing your input")

    # if not any(elem in args for elem in ('--id')):
    #     return bot.reply("Your input was missing some required information")

    # if args.get('--networks'):
    #     if not any(elem in args for elem in ('--name', '--url')):
    #         return bot.reply("I need a --name and --url")

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz',
        'X-ApiKey': bot.config.chaseapp.chaseapp_api_key
    }

    if not args.get('--id'):
        chases = _fetch_api_list(bot)
        update_id = chases[0]['ID']
    else:
        update_id = args.get('--id')

    chase_info = _get_specific_chase(bot, update_id)
    chase_info_networks = chase_info.get('Networks', [{}])

    now = pendulum.now()
    now_ts = now.timestamp()

    if not args.get('--live'):
        args['--live'] = 'false'

    payload = chase_info
    for arg, value in args.items():
        # ignore junk returned from _parseargs
        if arg in ["extra_text", '--id', '--last']:
            continue
        elif arg == '--live':
            if value:
                if value.lower() == 'false':
                    value = False
                else:
                    value = True
            else:
                value = True
        # elif arg == '--votes':
        #     try:
        #         value = int(value)
        #     except Exception as err:
        #         LOGGER.debug(err)
        #         return bot.reply("That's an invalid vote count! STOP THE COUNT")
        # elif arg == '--title':
        #     arg = 'name'
        # elif arg == '--networks':
        #     if args.get('--edit'):
        #         network_to_edit = None
        #         for idx, network in enumerate(chase_info_networks):
        #             if network.get('Name') == args.get('--name'):
        #                 network_to_edit = network
        #                 break
        #         if not network_to_edit:
        #             return bot.reply("I couldn't find that network to modify")
        #         # print(args.get('--tier'))
        #         tier = args.get('--tier')
        #         # print(type(tier))
        #         if tier:
        #             if int(tier) == 0:
        #                 # if network_to_edit['Tier'] == 1:
        #                 tier = 0
        #             else:
        #                 tier = int(tier)
        #         else:
        #             tier = int(network_to_edit['Tier'])
        #         value = {
        #             'Name': args.get('--newname') or network_to_edit['Name'],
        #             'URL': args.get('--url') or network_to_edit['URL'],
        #             'Tier': tier,
        #             'Logo': args.get('--logo', '') or network_to_edit['Logo'],
        #             'Other': args.get('--other', '') or network_to_edit['Other'],
        #         }
        #         chase_info_networks[idx] = value
        #     else:
        #         chase_info_networks.append(
        #             {
        #                 'Name': args.get('--name'),
        #                 'URL': args.get('--url'),
        #                 'Tier': int(args.get('--tier', 0)),
        #                 'Logo': urlparse(args['--url']).netloc.replace('www.', ''),
        #                 'Other': '',
        #             }
        #         )
        #     value = chase_info_networks
        # if arg in ['--name', '--url']:
        #     continue
        # else:
        #     payload[arg.replace('--', '').title()] = value

    print(chase_info.get('EndedAt'))

    current_ended_at = pendulum.parse(chase_info.get('EndedAt', '2001-01-01T00:00:00Z'), strict=False)
    # print(now_ts - current_ended_at.int_timestamp)

    if abs(now_ts - current_ended_at.int_timestamp) >= 604800:
        payload['EndedAt'] = "{}".format(now)
    if not chase_info.get('EndedAt'):
        payload['EndedAt'] = "{}".format(now)
        # payload['EndedAt'] = now_ts
    else:
        payload['EndedAt'] = chase_info.get('EndedAt')
    payload['Live'] = False
    print(payload['EndedAt'])

    # for key, value in chase_info.items():
    #     for key_, value_ in payload.items():
    #         if key.lower() == key_.lower():
    #             chase_info[key] = value_
    # bot.say('test')
    # print(payload)
    # print("---------------")
    # print(chase_info)
    payload['id'] = update_id

    # print(payload)

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/UpdateChase"

    data = requests.post(api_endpoint, headers=headers, json=payload)
    if data.status_code != 200:
        return bot.say("Something went wrong")
    bot.say("Successfully Ended Chase ({} - {})".format(data.status_code, update_id))


@plugin.command('updatechase', 'update', 'uc')
@plugin.example('.update --last --name "LA Chase"')
@plugin.output_prefix(APP_PREFIX)
def update_chase(bot, trigger):
    """Update chases

    Assumes the most recent chase unless `--id [ChaseApp chase ID]` is passed.
    Fields to modify (`--title "[new title]"` or `--url [new url]` etc). Any
    values that contain spaces must be surrounded by quotation marks. If
    `--networks` is passed, will assume you want to append a new network and
    url to the chase, pass `--edit` with an existing `--name` to edit an
    existing network.
    !*Only specific users are granted access to this command.*!

    Valid fields:
    ```
        --title "LA Chase"
        --desc "some description here"
        --live true(default)/false
        --networks
            --name ABC7
            --url https://abc7.com/watch/live/
            --tier 1
            --edit
                --name ABC7 --newname "ABC 7"
                --url https://abc7.com/watch/live
                --tier 0
                --votes 0
    ```

        e.g. ^update --title "LA Chase"
             ^update --id 7e171514-9c51-11ea-b6a3-0b58aa4cbde4 --live true
             ^update --networks --name CBSLA --url https://cbs.com
             ^update --networks --edit --name CBSLA --tier 2 --votes 0
    """

    check = trigger.hostmask.split("!")[1]
    if check not in bot.config.chaseapp.chaseapp_mods:
        LOGGER.error("{} tried to update a chase".format(trigger.hostmask))
        return bot.reply("You're not authorized to do that!")

    if not trigger.group(2):
        return bot.reply("I need some info to update")

    args = _parseargs(trigger.group(2))
    if not args:
        return bot.reply("Something went wrong parsing your input")

    if not any(elem in args for elem in ('--title', '--desc', '--networks', '--live', '--votes')):
        return bot.reply("Your input was missing some required information")

    if args.get('--networks'):
        if not any(elem in args for elem in ('--name', '--url')):
            return bot.reply("I need a --name and --url")

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz',
        'X-ApiKey': bot.config.chaseapp.chaseapp_api_key
    }

    if not args.get('--id'):
        chases = _fetch_api_list(bot)
        update_id = chases[0]['ID']
    else:
        update_id = args.get('--id')

    chase_info = _get_specific_chase(bot, update_id)
    chase_info_networks = chase_info.get('Networks', [{}])

    if not args.get('--live'):
        args['--live'] = 'true'

    payload = chase_info
    for arg, value in args.items():
        # ignore junk returned from _parseargs
        if arg in ["extra_text", '--id', '--last']:
            continue
        elif arg == '--live':
            if value:
                if value.lower() == 'false':
                    value = False
                else:
                    value = True
            else:
                value = True
        elif arg == '--votes':
            try:
                value = int(value)
            except Exception as err:
                LOGGER.debug(err)
                return bot.reply("That's an invalid vote count! STOP THE COUNT")
        elif arg == '--title':
            arg = 'name'
        elif arg == '--networks':
            if args.get('--edit'):
                network_to_edit = None
                for idx, network in enumerate(chase_info_networks):
                    if network.get('Name') == args.get('--name'):
                        network_to_edit = network
                        break
                if not network_to_edit:
                    return bot.reply("I couldn't find that network to modify")
                # print(args.get('--tier'))
                tier = args.get('--tier')
                # print(type(tier))
                if tier:
                    if int(tier) == 0:
                        # if network_to_edit['Tier'] == 1:
                        tier = 0
                    else:
                        tier = int(tier)
                else:
                    tier = int(network_to_edit['Tier'])
                value = {
                    'Name': args.get('--newname') or network_to_edit['Name'],
                    'URL': args.get('--url') or network_to_edit['URL'],
                    'Tier': tier,
                    'Logo': args.get('--logo', '') or network_to_edit['Logo'],
                    'Other': args.get('--other', '') or network_to_edit['Other'],
                }
                chase_info_networks[idx] = value
            else:
                chase_info_networks.append(
                    {
                        'Name': args.get('--name'),
                        'URL': args.get('--url'),
                        'Tier': int(args.get('--tier', 0)),
                        'Logo': urlparse(args['--url']).netloc.replace('www.', ''),
                        'Other': '',
                    }
                )
            value = chase_info_networks
        if arg in ['--name', '--url']:
            continue
        else:
            payload[arg.replace('--', '').title()] = value

    # for key, value in chase_info.items():
    #     for key_, value_ in payload.items():
    #         if key.lower() == key_.lower():
    #             chase_info[key] = value_
    # bot.say('test')
    # print(payload)
    # print("---------------")
    # print(chase_info)
    payload['id'] = update_id

    print(payload)

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/UpdateChase"

    data = requests.post(api_endpoint, headers=headers, json=payload)
    if data.status_code != 200:
        return bot.say("Something went wrong")
    bot.say("Successfully Updated ({} - {})".format(data.status_code, update_id))


@plugin.command('addchase', 'add', 'ac')
@plugin.example('.addchase')
@plugin.output_prefix(APP_PREFIX)
def add_chase(bot, trigger):
    """Add chases

    Requires `--title, --desc, --network, --url` any other fields are optional.
    Any values that contain spaces must be surrounded by quotation marks.
    Assumes `--tier` will be 1 since most of the time adding a new chase will
    set whatever network and url are passed to primary tier.
    !*Only specific users are granted access to this command.*!

    Valid fields:
    ```
        --title "LA Chase"
        --desc "some description here"
        --network CBSLA
        --url fancyurlhere.com
        --live true(default)/false
    ```

        e.g. ^add --title "Test Chase" --desc "Testing API Changes" --network "FOX11" --url "https://www.foxla.com/live"
    """

    check = trigger.hostmask.split("!")[1]
    if check not in bot.config.chaseapp.chaseapp_mods:
        LOGGER.error("{} tried to add a chase".format(trigger.hostmask))
        return bot.reply("You're not authorized to do that!")

    if not trigger.group(2):
        return bot.reply("I need some info to add")

    args = _parseargs(trigger.group(2))
    if not args:
        return bot.reply("Something went wrong parsing your input")

    if not all(elem in args for elem in ('--title', '--desc', '--url', '--network')):
        return bot.reply("Your input was missing some required information")

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz',
        'X-ApiKey': bot.config.chaseapp.chaseapp_api_key
    }

    if args.get('--live'):
        if args['--live'] == 'false':
            args['--live'] = False
        else:
            args['--live'] = True
    else:
        args['--live'] = True
    networks = [{
        'Name': args['--network'],
        'URL': args['--url'],
        'Logo': args.get('--logo', urlparse(args['--url']).netloc.replace('www.', '')) or '',
        'Tier': int(args.get('--tier', 1)),
        'Other': args.get('--other', '')
    }]
    payload = {
        "name": args['--title'],
        "desc": args['--desc'],
        "live": args.get('--live'),
        "networks": networks,
    }

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/AddChase"

    data = requests.post(api_endpoint, headers=headers, json=payload)
    if data.status_code != 200:
        return bot.say("Something went wrong")
    bot.say("Successfully Added ({})".format(data.text))


@plugin.command('deletechase', 'delete', 'dc')
@plugin.example('.deletechase')
@plugin.output_prefix(APP_PREFIX)
def delete_chase(bot, trigger):
    """Delete chases

    Requires either `--last` or `--id [ChaseApp chase ID]`. !*Only specific users
    are granted access to this command.*!

        e.g. ^delete --last
             ^delete --id 7e171514-9c51-11ea-b6a3-0b58aa4cbde4
    """

    check = trigger.hostmask.split("!")[1]
    if check not in bot.config.chaseapp.chaseapp_mods:
        LOGGER.error("{} tried to delete a chase".format(trigger.hostmask))
        return bot.reply("You're not authorized to do that!")

    if not trigger.group(2):
        return bot.reply("I need a ChaseApp ID or `--last` to delete")

    args = _parseargs(trigger.group(2))
    if not args:
        return bot.reply("Something went wrong parsing your input")

    if not (args.get('--id') or args.get('--last')):
        return bot.reply("I need a chase ID to reference (or pass in `--last` to delete the most recent chase)")

    delete_id = args.get('--id')
    if not delete_id:
        chases = _fetch_api_list(bot, live_mode=True)
        if not chases:
            return bot.say("No live chases, if you want to delete an inactive chase you need to give me a chase ID")
        delete_id = chases[0]['ID']

    headers = {
        'User-Agent': 'chasebot@efnet ({}) v1.0'.format(trigger.nick),
        'From': 'chasebot@cottongin.xyz',
        'X-ApiKey': bot.config.chaseapp.chaseapp_api_key
    }

    payload = {
        "id": delete_id
    }

    api_endpoint = bot.config.chaseapp.chaseapp_api_url + "/DeleteChase"

    data = requests.post(api_endpoint, headers=headers, json=payload)
    if data.status_code != 200:
        return bot.say("Something went wrong")
    bot.say("Successfully Deleted ({} - {})".format(data.status_code, delete_id))


@plugin.command('chasenotify')
@plugin.example('.chasenotify')
@plugin.output_prefix(BOT_PREFIX)
def chase_notify(bot, trigger):
    pass


@plugin.command('following')
@plugin.example('.following')
@plugin.output_prefix(BOT_PREFIX)
def say_following(bot, trigger):
    """Who am I following?"""
    if not api:
        return
    try:
        users = api.lookup_user(user_id=",".join(FOLLOW_LIST))
        prefix = "I'm following: @{}".format(', @'.join(item.get('screen_name') for item in users))
        return bot.say(prefix)
    except Exception:
        traceback.print_exc()
        return bot.say("Hm, something went wrong!")


@plugin.command('lastseen')
@plugin.example('.lastseen')
@plugin.output_prefix(BOT_PREFIX)
def say_last(bot, trigger):
    """Fetch the last tweet I saw"""
    try:
        twitter_list = api.get_list_statuses(
            owner_screen_name='efnetchasebot',
            slug='last',
            count=1
        )
        last_tweet = twitter_list[0].get('extended_tweet', {}).get('full_text') or twitter_list[0].get('text')
        last_tweet = _sanitize(last_tweet)
        last_tweet_seen = twitter_list[0]['created_at']
        last_tweet_seen = pendulum.parse(last_tweet_seen, strict=False)
        last_tweet_seen = last_tweet_seen.diff_for_humans()
        last_tweet_name = twitter_list[0]['user'].get('screen_name')
        resp = "Last tweet I've seen: ({}) \x02@{}\x02: {}".format(last_tweet_seen, last_tweet_name, last_tweet)
        return bot.say(resp)
    except Exception:
        traceback.print_exc()
        return bot.say('Hm, something went wrong!')


def _sanitize(text):
    text = text.replace('\n', '')
    text = text.strip()
    text = html.unescape(text)
    return text
