import os
import time
from slackclient import SlackClient
from get_fb_auth_token import get_fb_access_token, get_fb_id
import pynder

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"

signed_in = False

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
tinder_session = None


def sign_in(command):
    inputs = command.split(' ')
    if len(inputs) < 3:
        return "Sign in like this: @tinderbot signin <Username> <Password>"
    fid, faut = None, None
    print(inputs)
    if inputs[1].startswith("faut"):
        fid, faut = inputs[2:4]
    else:
        username, password = inputs[1:3]
        faut = get_fb_access_token(username, password)
        fid = get_fb_id(faut)
    global signed_in
    signed_in = True
    print(fid)
    print(faut)
    global tinder_session
    tinder_session = pynder.Session(facebook_id=fid, facebook_token=faut)
    print(", ".join([x.name for x in tinder_session.get_fb_friends()]))
    return "Signed in!" if tinder_session else "Something went wrong"

def get_nearby_users():
    assert tinder_session
    return [user.name for user in tinder_session.nearby_users()]



def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """

    def get_response():
        if not signed_in and command.startswith("signin"):
            return sign_in(command)
        if not signed_in:
            return "Sign in like this: @tinderbot signin <Username> <Password> or @tinderbot signin faut <facebook " \
                   "id> <tinder access token> "
        if command.startswith("nearby"):
            return get_nearby_users().join(', ')

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=get_response(), as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output

    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")