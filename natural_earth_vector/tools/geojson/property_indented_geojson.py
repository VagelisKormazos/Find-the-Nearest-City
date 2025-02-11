import sys
import json
import logging
import re

# float_pat = re.compile(r'^-?\d+(?:\.\d+)?(e-?\d+)?$')
# charfloat_pat = re.compile(r'^[\[,\,]-?\d+(?:\.\d+)?(e-?\d+)?$')

float_pat = re.compile(r'^-?\d+\.\d+(e-?\d+)?$')
charfloat_pat = re.compile(r'^[\[,\,]-?\d+\.\d+(e-?\d+)?$')
scinot_geom_pat = re.compile(r'^[\[,\,](-?\d+e-\d+?)$')
scinot_prop_pat = re.compile(r'^\b-?[1-9](?:\.\d+)?[Ee][-+]?\d+\b$')

class encoder:

    def __init__(self, **kwargs):

        indent = kwargs.get('indent', 2)
        indent = int(indent)

        if indent <= 0:
            indent = None

        # Here are the rules (derived from Who's On First):
        #
        # 1) Everything is truncated to (6) decimal points
        #
        # 2) Trailing zeros are removed from all coordinates
        #
        # Mostly this is to account for Python deciding to use scientific notation
        # on a whim which is super annoying. To that end we are enforcing some standards
        # which raises the larger question of why we let anyone specify a precision
        # at all. But that is tomorrow's problem...

        precision = kwargs.get('precision', 6)

        if precision != None:

            precision = int(precision)

            if precision <= 0:
                precision = None

            if precision > 14:
                raise Exception, "WHY U SO PRECISE?"

        self.indent = indent
        self.precision = precision

        # See comments about precision above. We reset fmt below in '_encode_feature'
        # if that is necessary. (20151202/thisisaaronland)

        self.fmt = "%.6f"

    def _encode(self, data, fh, indent, precision=None):

        # From TileStache's vectiles GeoJSON encoder thingy
        # (20130317/straup)

        encoder = json.JSONEncoder(separators=(',', ':'), indent=indent, sort_keys=True)
        encoded = encoder.iterencode(data)

        # Remember - see the comments about precision above
        # in __init__

        # I hate you, Python...
        # I really hate you0000000000000...

        def enzeroify (n):

            n = n.rstrip('0')

            # Because apparently you can't have float values without
            # something after the decimal point... I don't know, maybe
            # there's some logic to that decision but it escapes me
            # right now... (20151221/thisisaaronland)

            if n.endswith('.'):
                n = n + '0'

            return n

        # Sigh...

        fmt = self.fmt

        if precision != None:

            precision = int(precision)

            if precision <= 0:
                precision = None

        if precision != None:
            fmt = "%." + str(precision) + "f"

        for token in encoded:

            if scinot_geom_pat.match(token):

                f = fmt % float(token[1:])

                f = enzeroify(f)

                f = token[0] + f

                fh.write(f)

            elif charfloat_pat.match(token):
                # in python 2.7, we see a character followed by a float literal

                f = fmt % float(token[1:])

                f = enzeroify(f)

                f = token[0] + f

                fh.write(f)

            # in python 2.6, we see a simple float literal

            elif float_pat.match(token) or scinot_prop_pat.match(token):

                f = fmt % float(token)
                f = enzeroify(f)

                fh.write(f)

            else:
                fh.write(token)

    def encode_feature(self, feature, fh=sys.stdout):

        spec = {
            'id' : '',
            'type': 'Feature',
            'properties': {},
            'bbox': [],
            'geometry': {}
        }

        fh.write("{\n")

        for k in ('id', 'type', 'properties', 'bbox', 'geometry'):

            default = spec[k]

            fh.write(' ' * self.indent)
            fh.write('"%s": ' % k)

            # See comments in __init__ and note the way we are explicitly
            # not passing a precision (20151202/thisisaaronland)

            if k in ('geometry'):
                self._encode(feature.get(k, default), fh, None)
            else:

                # See comments in __init__ and note the way we are explicitly
                # reseting precision unless the user says otherwise... which
                # is not necessarily what we want to do in the first place
                # (20151202/thisisaaronland)

                precision = self.precision

                if precision == None:
                    precision = 6

                self._encode(feature.get(k, default), fh, self.indent * 2, precision)

            if k != 'geometry':
                fh.write(',')

            fh.write('\n')

        fh.write('}')

if __name__ == '__main__':

    import geojson

    e = encoder()

    for path in sys.argv[1:]:

        fh = open(path, 'r')
        f = geojson.load(fh)
        fh = open(path, 'w')

        e.encode_feature(f, fh)
