import os
import io
import base64

from flask import Flask, request, render_template
from PIL import Image
import PIL.ImageOps
import exif
import html

from pprint import pformat


def pretty_print_html_dict(my_dict):
    if not my_dict:
        return ''
    html_string = "<ul>\n"
    for key, val in my_dict.items():
        if isinstance(val, dict):
            nested_html = pretty_print_html_dict(val)
            html_string += f"\t<li><strong>{key}:</strong> {nested_html}</li>\n"
        else:
            html_string += f"\t<li><strong>{key}:</strong> {val}</li>\n"
    html_string += "</ul>"
    return html_string


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/image-convert', methods=['GET', 'POST'])
def image_convert():
    if request.method == 'POST':
        image_file = request.files['image_file']
        print(f"image_file.filename = {image_file.filename}")

        encoded_image = None
        image_changed_data = None
        image_exif_data = None
        if image_file.filename:
            image_bytes = image_file.read()
            image = Image.open(io.BytesIO(image_bytes))
            
            encoded_image = base64.b64encode(image_bytes).decode('ascii')
            print(f"Uploaded image: '{image_file.filename}'")

            if request.form.get('invert_image'):
                print('Image inversion requested.')
                print(f"Image original format: '{image.format}'.")

                image_changed = PIL.ImageOps.invert(image.convert('RGB'))
                print(f"Changed image format: '{image_changed.format}'")

                buffer_changed_image_io = io.BytesIO()
                image_changed.save(buffer_changed_image_io, format=image.format)

                bytes_changed_image = buffer_changed_image_io.getvalue()
                # image_changed = Image.open(io.BytesIO(bytes_changed_image), formats=[image.format])

                image_changed_data = base64.b64encode(bytes_changed_image).decode('ascii')

            image_exif_data = exif.Image(image_file)
            print(f"Image EXIF data:\n{pformat(image_exif_data.get_all(), indent=8)}")

        return render_template('image-convert.html',
                               uploaded_image_data=encoded_image,
                               image_changed_data=image_changed_data,
                               uploaded_image_exif_data=image_exif_data,
                               pretty_print_html_dict=pretty_print_html_dict,
                               pformat=pformat)
    else:
        print("Simple display of image upload page.")
        return render_template('image-convert.html', pretty_print_html_dict=pretty_print_html_dict)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
