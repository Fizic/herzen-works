import io
import base64
import json
import traceback

from PIL import Image
import PIL.ImageOps
import exif


def handler(event, context):
    print('========================================')
    print(f"EVENT[HTTP - {event['httpMethod']}]: {event}")

    if 'OPTIONS' == event['httpMethod']:
        headers = event['headers']
        if headers['Sec-Fetch-Mode'] == 'cors':
            print(f"CORS preflight request received. Headers: {headers}")
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST',
                    'Access-Control-Allow-Headers': 'Accept, Accept-Encoding, Accept-Language, Authorization, Content-Length, Content-Type, Date, Host, Origin, Referer, User-Agent, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site'
                }
            }

    message_text = event['body']
    if not message_text:
        print(f"MESSAGE TEXT IS EMPTY: '{message_text}'")
        return {
            'statusCode': 200,
            'body': {
                'uploaded_image_data': None,
                'image_changed_data': None,
                'uploaded_image_exif_data': None
            },
            'isBase64Encoded': False
        }

    message = json.loads(message_text)
    image_file = message['image_file']
    image_data = message['image_data']
    image_invert = message['image_invert']

    print(f"BODY: image_file = '{image_file}', image_data = '{image_data}', image_invert = '{image_invert}'")

    encoded_image = None
    image_changed_data = None
    image_exif_data_text = None
    try:
        if image_file and image_data:
            print(f"Uploaded image: '{image_file}'")

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            encoded_image = base64.b64encode(image_bytes).decode('ascii')

            if image_invert:
                print('Image inversion requested.')
                print(f"Image original format: '{image.format}'.")

                image_changed = PIL.ImageOps.invert(image.convert('RGB'))
                print(f"Changed image format: '{image_changed.format}'")

                buffer_changed_image_io = io.BytesIO()
                image_changed.save(buffer_changed_image_io, format=image.format)

                bytes_changed_image = buffer_changed_image_io.getvalue()
                image_changed_data = base64.b64encode(bytes_changed_image).decode('ascii')

            image_exif_data = exif.Image(image_bytes)
            image_exif_data_text = json.dumps(image_exif_data.get_all(), ensure_ascii=True, default=lambda o: str(o))
            print(f"Image EXIF data: {image_exif_data.get_all()}")
    except OSError as exception:
        print(f"OS ERROR: {exception}")
        print(traceback.format_exc())
    except BaseException as exception:
        print(f"EXCEPTION: {exception}")
        print(traceback.format_exc())

    return {
        'statusCode': 200,
        'body': {
            'uploaded_image_data': encoded_image,
            'image_changed_data': image_changed_data,
            'uploaded_image_exif_data': image_exif_data_text
        },
        'isBase64Encoded': False
    }
