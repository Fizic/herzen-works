import re
import base64
import traceback


AUTH_HTTP_BASIC_CREDENTIALS = r'(?<=Basic\s).*'

AUTH_RESPONSE_FORBIDDEN = { 'isAuthorized': False }


def handler(event, context):
    http_headers = event['headers']

    if (not http_headers) or (not 'Authorization' in http_headers):
        print(f"Cannot authorize. Event: {event}")
        return AUTH_RESPONSE_FORBIDDEN

    try:
        encoded_credentials = http_headers['Authorization']
        found_encoded_credentials = re.findall(AUTH_HTTP_BASIC_CREDENTIALS, encoded_credentials)
        print(f"found_encoded_credentials = {found_encoded_credentials}")
        encoded_credentials = found_encoded_credentials[0] if found_encoded_credentials else None

        decoded_credentials = base64.b64decode(encoded_credentials) if encoded_credentials else None
        decoded_credentials = decoded_credentials.decode('utf-8') if decoded_credentials else None

        if ':' not in decoded_credentials:
            print(f"Cannot authorize. There is no a pair of a username and a password separated by colon.")
            return AUTH_RESPONSE_FORBIDDEN

        username, password = decoded_credentials.split(':')
        if username != 'user' and password != 'changeit':
            print(f"Cannot authorize. Invalid username and/or password.")
            return AUTH_RESPONSE_FORBIDDEN
        else:
            print(f"Successfully authorized user {username}.")
            return {
                'isAuthorized': True,
                'context': {
                    'result': 'SUCCESS'
                }
            }

    except BaseException as exception:
        print(f"Exception occured: {exception}. Traceback: {traceback.format_exc()}.")
