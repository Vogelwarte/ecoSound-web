#!/usr/bin/env python

# svt.py -- sound visualization tool
# http://github.com/ljvillanueva/Sound-Viewer-Tool
# Copyright (C) 2009-2013 Luis J. Villanueva
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
# Renamed to svt to keep separate from the wav2png.py script
#
# Based on wav2png.py by Bram de Jong <bram.dejong at domain.com where domain in gmail>
# From http://freesound.iua.upf.edu/blog/?p=10
#

svt_version = "1.0"

import optparse, math, sys
import scikits.audiolab as audiolab
from PIL import ImageFilter, ImageChops, Image, ImageDraw, ImageColor
import numpy


class AudioProcessor(object):
    def __init__(self, audio_file, fft_size, channel, window):
        self.fft_size = fft_size
        self.audio_file = audio_file
        self.frames = audio_file.get_nframes()
        self.samplerate = audio_file.get_samplerate()
        self.channels = audio_file.get_channels()
        self.spectrum_range = None
        self.lower = 10
        self.higher = 22050
        self.lower_log = math.log10(self.lower)
        self.higher_log = math.log10(self.higher)
        self.clip = lambda val, low, high: min(high, max(low, val))
        self.channel = channel
        self.window = window
        if self.window == "bartlett":
            self.window = numpy.bartlett(self.fft_size)
        elif self.window == "blackman":
            self.window = numpy.blackman(self.fft_size)
        elif self.window == "hanning":
            self.window = numpy.hanning(self.fft_size)
        elif self.window == "hamming":
            self.window = numpy.hamming(self.fft_size)
        elif self.window == "kaiser":
            self.window = numpy.kaiser(self.fft_size)

    def read(self, start, size, resize_if_less=False):
        """ read size samples starting at start, if resize_if_less is True and less than size
        samples are read, resize the array to size and fill with zeros """

        # number of zeros to add to start and end of the buffer
        add_to_start = 0
        add_to_end = 0

        if start < 0:
            # the first FFT window starts centered around zero
            if size + start <= 0:
                return numpy.zeros(size) if resize_if_less else numpy.array([])
            else:
                self.audio_file.seek(0)

                add_to_start = -start  # remember: start is negative!
                to_read = size + start

                if to_read > self.frames:
                    add_to_end = to_read - self.frames
                    to_read = self.frames
        else:
            self.audio_file.seek(start)

            to_read = size
            if start + to_read >= self.frames:
                to_read = self.frames - start
                add_to_end = size - to_read

        try:
            samples = self.audio_file.read_frames(to_read)
        except IOError:
            # this can happen for wave files with broken headers...
            return numpy.zeros(size) if resize_if_less else numpy.zeros(2)

        # select which channel to draw
        if self.channels > 1:
            if self.channel == 1:
                samples = samples[:, 0]
            if self.channel == 2:
                samples = samples[:, 1]

        if resize_if_less and (add_to_start > 0 or add_to_end > 0):
            if add_to_start > 0:
                samples = numpy.concatenate((numpy.zeros(add_to_start), samples), axis=0)

            if add_to_end > 0:
                samples = numpy.resize(samples, size)
                samples[size - add_to_end:] = 0

        return samples

    def spectral_centroid(self, seek_point, spec_range=120.0):
        """ starting at seek_point read fft_size samples, and calculate the spectral centroid """

        samples = self.read(seek_point - self.fft_size / 2, self.fft_size, True)

        samples *= self.window
        fft = numpy.fft.fft(samples)
        spectrum = numpy.abs(fft[:fft.shape[0] / 2 + 1]) / float(self.fft_size)  # normalized abs(FFT) between 0 and 1
        length = numpy.float64(spectrum.shape[0])

        # scale the db spectrum from [- spec_range db ... 0 db] > [0..1]
        db_spectrum = ((20 * (numpy.log10(spectrum + 1e-30))).clip(-spec_range, 0.0) + spec_range) / spec_range

        energy = spectrum.sum()
        spectral_centroid = 0

        if energy > 1e-20:
            # calculate the spectral centroid

            if type(self.spectrum_range) is not numpy.ndarray and self.spectrum_range == None:
                self.spectrum_range = numpy.arange(length)

            spectral_centroid = (spectrum * self.spectrum_range).sum() / (energy * (length - 1)) * self.samplerate * 0.5

            # clip > log10 > scale between 0 and 1
            spectral_centroid = (math.log10(self.clip(spectral_centroid, self.lower, self.higher)) - self.lower_log) / (self.higher_log - self.lower_log)

        return (spectral_centroid, db_spectrum)

    def peaks(self, start_seek, end_seek):
        """ read all samples between start_seek and end_seek, then find the minimum and maximum peak
        in that range. Returns that pair in the order they were found. So if min was found first,
        it returns (min, max) else the other way around. """

        # larger blocksizes are faster but take more mem...
        # Aha, Watson, a clue, a tradeof!
        block_size = 4096

        max_index = -1
        max_value = -1
        min_index = -1
        min_value = 1

        if end_seek > self.frames:
            end_seek = self.frames

        if block_size > end_seek - start_seek:
            block_size = end_seek - start_seek

        if block_size <= 1:
            samples = self.read(start_seek, 1)
            return samples[0], samples[0]
        elif block_size == 2:
            samples = self.read(start_seek, True)
            return samples[0], samples[1]

        for i in range(start_seek, end_seek, block_size):
            samples = self.read(i, block_size)

            local_max_index = numpy.argmax(samples)
            local_max_value = samples[local_max_index]

            if local_max_value > max_value:
                max_value = local_max_value
                max_index = local_max_index

            local_min_index = numpy.argmin(samples)
            local_min_value = samples[local_min_index]

            if local_min_value < min_value:
                min_value = local_min_value
                min_index = local_min_index

        return (min_value, max_value) if min_index < max_index else (max_value, min_value)


def interpolate_colors(colors, flat=False, num_colors=256):
    """ given a list of colors, create a larger list of colors interpolating
    the first one. If flatten is True a list of numers will be returned. If
    False, a list of (r,g,b) tuples. num_colors is the number of colors wanted
    in the final list """

    palette = []

    for i in range(num_colors):
        index = (i * (len(colors) - 1)) / (num_colors - 1.0)
        index_int = int(index)
        alpha = index - float(index_int)

        if alpha > 0:
            r = (1.0 - alpha) * colors[index_int][0] + alpha * colors[index_int + 1][0]
            g = (1.0 - alpha) * colors[index_int][1] + alpha * colors[index_int + 1][1]
            b = (1.0 - alpha) * colors[index_int][2] + alpha * colors[index_int + 1][2]
        else:
            r = (1.0 - alpha) * colors[index_int][0]
            g = (1.0 - alpha) * colors[index_int][1]
            b = (1.0 - alpha) * colors[index_int][2]

        if flat:
            palette.extend((int(r), int(g), int(b)))
        else:
            palette.append((int(r), int(g), int(b)))

    return palette


class WaveformImage(object):
    def __init__(self, image_width, image_height):
        self.image = Image.new("RGB", (image_width, image_height))

        self.image_width = image_width
        self.image_height = image_height

        self.draw = ImageDraw.Draw(self.image)
        self.previous_x, self.previous_y = None, None

        colors = [
            (0, 0, 0),
            (58 / 4, 68 / 4, 65 / 4),
            (80 / 2, 100 / 2, 153 / 2),
            (90, 180, 100),
            (224, 224, 44),
            (255, 60, 30),
            (255, 255, 255)
        ]

        # this line gets the old "screaming" colors back...
        # colors = [self.color_from_value(value/29.0) for value in range(0,30)]

        self.color_lookup = interpolate_colors(colors)
        self.pix = self.image.load()

    def color_from_value(self, value):
        """ given a value between 0 and 1, return an (r,g,b) tuple """

        return ImageColor.getrgb("hsl(%d,%d%%,%d%%)" % (int((1.0 - value) * 360), 80, 50))

    def draw_peaks(self, x, peaks, spectral_centroid):
        """ draw 2 peaks at x using the spectral_centroid for color """

        y1 = self.image_height * 0.5 - peaks[0] * (self.image_height - 4) * 0.5
        y2 = self.image_height * 0.5 - peaks[1] * (self.image_height - 4) * 0.5

        line_color = self.color_lookup[int(spectral_centroid * 255.0)]

        if self.previous_y != None:
            self.draw.line([self.previous_x, self.previous_y, x, y1, x, y2], line_color)
        else:
            self.draw.line([x, y1, x, y2], line_color)

        self.previous_x, self.previous_y = x, y2

        self.draw_anti_aliased_pixels(x, y1, y2, line_color)

    def draw_anti_aliased_pixels(self, x, y1, y2, color):
        """ vertical anti-aliasing at y1 and y2 """

        y_max = max(y1, y2)
        y_max_int = int(y_max)
        alpha = y_max - y_max_int

        if alpha > 0.0 and alpha < 1.0 and y_max_int + 1 < self.image_height:
            current_pix = self.pix[x, y_max_int + 1]

            r = int((1 - alpha) * current_pix[0] + alpha * color[0])
            g = int((1 - alpha) * current_pix[1] + alpha * color[1])
            b = int((1 - alpha) * current_pix[2] + alpha * color[2])

            self.pix[x, y_max_int + 1] = (r, g, b)

        y_min = min(y1, y2)
        y_min_int = int(y_min)
        alpha = 1.0 - (y_min - y_min_int)

        if alpha > 0.0 and alpha < 1.0 and y_min_int - 1 >= 0:
            current_pix = self.pix[x, y_min_int - 1]

            r = int((1 - alpha) * current_pix[0] + alpha * color[0])
            g = int((1 - alpha) * current_pix[1] + alpha * color[1])
            b = int((1 - alpha) * current_pix[2] + alpha * color[2])

            self.pix[x, y_min_int - 1] = (r, g, b)

    def save(self, filename):
        # draw a zero "zero" line
        a = 25
        for x in range(self.image_width):
            self.pix[x, self.image_height / 2] = tuple([p + a for p in self.pix[x, self.image_height / 2]])

        self.image.save(filename)


class SpectrogramImage(object):
    def __init__(self, image_width, image_height, fft_size, f_max, f_min, nyquist_freq):
        self.image = Image.new("P", (image_height, image_width))

        self.image_width = image_width
        self.image_height = image_height
        self.fft_size = fft_size
        self.f_max = f_max
        self.f_min = f_min
        self.nyquist_freq = nyquist_freq

        if nyquist_freq < f_max:
            print(
                "\nWarning: The specified maximum frequency to draw (%d Hz) is higher that what the digital file allows, which is %d Hz. The image file will have blank areas on top that correspond to empty data.\n" % (
                    f_max, nyquist_freq))

        colors = [
            (0, 0, 0),
            (58 / 4, 68 / 4, 65 / 4),
            (80 / 2, 100 / 2, 153 / 2),
            (90, 180, 100),
            (224, 224, 44),
            (255, 60, 30),
            (255, 255, 255)
        ]

        self.image.putpalette(interpolate_colors(colors, True))

        # generate the lookup which translates y-coordinate to fft-bin
        self.y_to_bin = []
        y_min = math.log10(f_min)
        y_max = math.log10(f_max)
        for y in range(self.image_height):
            #            log scale
            #            freq = math.pow(10.0, y_min + y / (image_height - 1.0) *(y_max - y_min))
            #            arithmetic scale
            freq = f_min + y / (image_height - 1.0) * (f_max - f_min)
            #            uses the nyquist frequency to allow files of different sampling rate
            bin = freq / nyquist_freq * (self.fft_size / 2 + 1)
            #            bin = freq / 22050.0 * (self.fft_size/2 + 1)

            if bin < self.fft_size / 2:
                alpha = bin - int(bin)

                self.y_to_bin.append((int(bin), alpha * 255))

        # this is a bit strange, but using image.load()[x,y] = ... is
        # a lot slower than using image.putadata and then rotating the image
        # so we store all the pixels in an array and then create the image when saving
        self.pixels = []

    def draw_spectrum(self, x, spectrum):
        for (index, alpha) in self.y_to_bin:
            self.pixels.append(int(((255.0 - alpha) * spectrum[index] + alpha * spectrum[index + 1])))

        for y in range(len(self.y_to_bin), self.image_height):
            self.pixels.append(0)

    def save(self, filename):
        self.image.putdata(self.pixels)
        self.image.transpose(Image.ROTATE_90).save(filename)


def create_png(input_filename, output_filename_w, output_filename_s, image_width, image_height, fft_size, f_max, f_min, wavefile, channel, window):
    audio_file = audiolab.sndfile(input_filename, 'read')

    samples_per_pixel = audio_file.get_nframes() / float(image_width)
    nyquist_freq = (audio_file.get_samplerate() / 2) + 0.0
    numpy_window = window
    #    processor = AudioProcessor(audio_file, fft_size, channel, numpy.hanning)
    processor = AudioProcessor(audio_file, fft_size, channel, numpy_window)

    if wavefile == 1:
        waveform = WaveformImage(image_width, image_height)
    spectrogram = SpectrogramImage(image_width, image_height, fft_size, f_max, f_min, nyquist_freq)
    arr = []
    for x in range(image_width):

        if x % (image_width / 10) == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        seek_point = int(x * samples_per_pixel)
        next_seek_point = int((x + 1) * samples_per_pixel)

        (spectral_centroid, db_spectrum) = processor.spectral_centroid(seek_point)

        if wavefile == 1:
            peaks = processor.peaks(seek_point, next_seek_point)
            waveform.draw_peaks(x, peaks, spectral_centroid)

        spectrogram.draw_spectrum(x, db_spectrum)
        arr.append(db_spectrum)

    if wavefile == 1:
        waveform.save(output_filename_w)
    spectrogram.save(output_filename_s)
    print(" done")

if __name__ == '__main__':
    parser = optparse.OptionParser("usage: %prog [options] input-filename", conflict_handler="resolve")
    parser.add_option("-a", "--waveout", action="store", dest="output_filename_w", type="string", help="output waveform image (default input filename + _w.png)")
    parser.add_option("-o", "--wavefile", action="store", dest="wavefile", type="int", help="draw waveform image (yes:1, no: 0; default: no)")
    parser.add_option("-s", "--specout", action="store", dest="output_filename_s", type="string", help="output spectrogram image (default input filename + _s.png)")
    parser.add_option("-w", "--width", action="store", dest="image_width", type="int", help="image width in pixels (default %default)")
    parser.add_option("-h", "--height", action="store", dest="image_height", type="int", help="image height in pixels (default %default)")
    parser.add_option("-f", "--fft", action="store", dest="fft_size", type="int", help="fft size, power of 2 for increased performance (default %default)")
    parser.add_option("-n", "--window", action="store", dest="window", type="string", help="window to use for the FFT: bartlett, blackman, hanning, hamming, or kaiser (default %default)")
    parser.add_option("-m", "--fmax", action="store", dest="f_max", type="int", help="Maximum freq to draw, in Hz (default %default)")
    parser.add_option("-i", "--fmin", action="store", dest="f_min", type="int", help="Minimum freq to draw, in Hz (default %default)")
    parser.add_option("-c", "--channel", action="store", dest="channel", type="int", help="Which channel to draw in a stereo file, 1 for left or 2 for right (default %default)")
    parser.add_option("-v", "--version", action="store_true", dest="version", help="display version information")

    parser.set_defaults(output_filename_w=None, output_filename_s=None, image_width=500, image_height=170, fft_size=2048, f_max=22050, f_min=10, wavefile=0, channel=1, window="hanning")

    (options, args) = parser.parse_args()

    if not options.version:
        if len(args) == 0:
            parser.print_help()
            parser.error("not enough arguments")

        if len(args) > 1 and (options.output_filename_w != None or options.output_filename_s != None):
            parser.error("when processing multiple files you can't define the output filename!")

        # process all files so the user can use wildcards like *.wav
        for input_file in args:
            if options.channel == 2:
                output_file_w = options.output_filename_w or input_file + "_w_r.png"
                output_file_s = options.output_filename_s or input_file + "_s_r.png"
            else:
                output_file_w = options.output_filename_w or input_file + "_w.png"
                output_file_s = options.output_filename_s or input_file + "_s.png"

            args = (
                input_file, output_file_w, output_file_s, options.image_width, options.image_height, options.fft_size, options.f_max, options.f_min, options.wavefile, options.channel, options.window)

        print("\nsvt version " + str(svt_version) + "\n")
        create_png(*args)
    else:
        print("\nsvt version " + str(svt_version) + "\n")
