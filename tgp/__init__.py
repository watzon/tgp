import sys
import zlib
import random
import base64
from io import BytesIO

from PIL import Image

__version__ = '0.1.0'

class TermImage(object):
    def __init__(self, data: str):
        """Creates a new TermImage object using base64 encoded image data"""
        
        # The raw base64 encoded data
        self._raw = data

        # PIL image, allowing us to get information about the
        # raw data, necessary for displaying the image in
        # the terminal
        self._pil_img = Image.open(BytesIO(base64.b64decode(data)))

        # Give this image a random id so that it can be used in
        # multiple places without regenerating the image
        self.id = random.randint(0, 4294967295)

        # Set the format for this image. This can't be accessed after
        # resize apparently, so it needs to be done here.
        self.format = self._pil_img.format

    @classmethod
    def open(cls, file_path: str):
        """Open a local image as a TermImage instance"""
        data = open(file_path, "rb").read()
        encoded = base64.b64encode(data)
        return cls(encoded)

    @property
    def width(self):
        """Returns the width of this image"""
        return self._pil_img.width
        
    @property
    def height(self):
        """Returns the height of this image"""
        return self._pil_img.height

    def resize(self, width: int, height: int, resample: int = 1):
        """Wrapper around Image.resize, allowing this image to be resized.
        This is a destructive operation."""
        self._pil_img = self._pil_img.resize((width, height), resample)
        return self

    def base64(self):
        """Return this image as base64. This is needed because on resize
        the raw data will change."""
        buffered = BytesIO()
        self._pil_img.save(buffered, format=self.format)
        return base64.b64encode(buffered.getvalue())

    def render(self):
        cmd = {
            'a': 'T',
            # 'i': self.id,
            's': self.width,
            'v': self.height
        }
        
        if self.format == "PNG":
            cmd['f'] = 100
        else:
            cmd['f'] = 24

        self._write_chunked(cmd, self.base64())

    # def delete(self):
    #     cmd = {'a': 'd', 'i': self.id}
    #     self._write_gr_cmd(cmd)

    def _write_gr_cmd(self, cmd, payload=None):
        sys.stdout.buffer.write(self._serialize_gr_command(cmd, payload))
        sys.stdout.flush()

    def _serialize_gr_command(self, cmd, payload=None):
        cmd = ','.join('{}={}'.format(k, v) for k, v in cmd.items())
        ans = []
        w = ans.append
        w(b'\033_G'), w(cmd.encode('ascii'))
        if payload:
            w(b';')
            w(payload)
        w(b'\033\\')
        return b''.join(ans)

    def _write_chunked(self, cmd, data):
        if cmd['f'] != 100:
            data = zlib.compress(data)
            cmd['o'] = 'z'
        while data:
            chunk, data = data[:4096], data[4096:]
            m = 1 if data else 0
            cmd['m'] = m
            self._write_gr_cmd(cmd, chunk)
            cmd.clear()

img = TermImage.open("avatar.png")
img.resize(80, 80)
img.render()