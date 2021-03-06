import os
from random import randint
import cv2
import os
import struct


def recalculate_crops(rgb_bb_b, rgb_bb_t, rgb_bb_l, rgb_bb_r, imgh, imgw, maxShift, minShift, crop_size):
    # center points of bounding box in the image
    center_y_global = rgb_bb_t + (rgb_bb_b - rgb_bb_t) / 2
    center_x_global = rgb_bb_l + (rgb_bb_r - rgb_bb_l) / 2

    lcrop_orig = center_x_global - crop_size/2
    rcrop_orig = center_x_global + crop_size/2
    tcrop_orig = center_y_global - crop_size/2
    bcrop_orig = center_y_global + crop_size/2



    dx, dy = random_shift(tcrop_orig, bcrop_orig, lcrop_orig, rcrop_orig, imgw, imgh, minShift, maxShift)

    lcrop = lcrop_orig + dx
    rcrop = rcrop_orig + dx
    bcrop = bcrop_orig + dy
    tcrop = tcrop_orig + dy

    # Ensure hotspot is still in cropped space, if not shift so that it is
    if center_x_global < lcrop:
        diff = lcrop - center_x_global
        lcrop -= diff
        rcrop -= diff

    if center_x_global > rcrop:
        diff = center_x_global - rcrop
        lcrop += diff
        rcrop += diff

    if center_y_global < tcrop:
        diff = center_y_global - tcrop
        bcrop += diff
        tcrop += diff

    if center_y_global > bcrop:
        diff = bcrop - center_y_global
        bcrop -= diff
        tcrop -= diff

    if tcrop < 0:
        diff = 0 - tcrop
        tcrop += diff
        bcrop += diff
    if bcrop > imgh:
        diff = bcrop - imgh
        bcrop -= diff
        tcrop -= diff
    if lcrop < 0:
        diff = 0 - lcrop
        lcrop += diff
        rcrop += diff
    if rcrop > imgw:
        diff = rcrop - imgw
        rcrop -= diff
        lcrop -= diff



    dx = lcrop_orig - lcrop
    dy = tcrop_orig - tcrop
    local_x = crop_size/2 + dx
    local_y = crop_size/2 + dy
    return tcrop, bcrop, lcrop, rcrop, local_x, local_y, dx, dy




def random_shift(topCrop, bottomCrop, leftCrop, rightCrop, w, h, minShift, maxShift):
    if maxShift == 0:
        return 0, 0

    dx = 0
    dy = 0

    # make dx
    if leftCrop != 0 and randint(0, 1) == 1:
        dx -= randint(minShift, maxShift)

    elif rightCrop != 0 and randint(0, 1) == 1:
        dx += randint(minShift, maxShift)

    # left crop outside image bounds
    if not leftCrop + dx > 0:
        dx = 0
    if not rightCrop + dx < w:
        dx = 0

    # make dy
    if topCrop != 0 and randint(0, 1) == 1:
        dy -= randint(minShift, maxShift)

    elif bottomCrop != 0 and randint(0, 1) == 1:
        dy += randint(minShift, maxShift)

    # left crop outside iomage bounds
    if topCrop + dy < 0:
        dy = 0
    if bottomCrop + dx > h:
        dy = 0

    return dx, dy

def write_label(file_name, label_file):
    with open(label_file, 'a') as file:
        file.write(file_name + "\n")



def negative_bounds(topCrop, bottomCrop, leftCrop, rightCrop, w, h, crop_size):
    # TODO find points screen quadrant take from another quadrant
    offset = 50
    mid_y = (bottomCrop - topCrop)/2 + topCrop
    mid_x = (rightCrop - leftCrop)/2 + leftCrop

    if mid_x > 800 or mid_y > 800 :
        # bottom left corner
        return h-crop_size, h, 0, crop_size
    else:
        # top right corner
        return 0, crop_size, h-crop_size, h

def getRectFromYolo(img, x, y, w, h):
    (imh, imw, imc) = img.shape
    x = int(x * imw)
    y = int(y * imh)
    w = int(w * imw)
    h = int(h * imh)
    return x - w / 2, y - h / 2, x + w / 2, y + h / 2  # x1, y1, x2, y2

def getYoloFromRect(imgh, imgw, x1, y1, x2, y2):
    w = x2 - x1
    h = y2 - y1
    cx = x1 + (w / 2.0)
    cy = y1 + (h / 2.0)
    yolox = float(cx) / float(imgw)
    yolow = float(w) / float(imgw)
    yoloy = float(cy) / float(imgh)
    yoloh = float(h) / float(imgh)
    return yolox, yoloy, yolow, yoloh


class UnknownImageFormat(Exception):
    pass

def get_image_size(file_path):
    """
    Return (width, height) for a given img file content - no external
    dependencies except the os and struct modules from core
    """
    if not os.path.isfile(file_path):
        return None, None

    size = os.path.getsize(file_path)

    with open(file_path) as input:
        height = -1
        width = -1
        data = input.read(25)

        if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
            # GIFs
            w, h = struct.unpack("<HH", data[6:10])
            width = int(w)
            height = int(h)
        elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
              and (data[12:16] == 'IHDR')):
            # PNGs
            w, h = struct.unpack(">LL", data[16:24])
            width = int(w)
            height = int(h)
        elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
            # older PNGs?
            w, h = struct.unpack(">LL", data[8:16])
            width = int(w)
            height = int(h)
        elif (size >= 2) and data.startswith('\377\330'):
            # JPEG
            msg = " raised while trying to decode as JPEG."
            input.seek(0)
            input.read(2)
            b = input.read(1)
            try:
                while (b and ord(b) != 0xDA):
                    while (ord(b) != 0xFF): b = input.read(1)
                    while (ord(b) == 0xFF): b = input.read(1)
                    if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                        input.read(3)
                        h, w = struct.unpack(">HH", input.read(4))
                        break
                    else:
                        input.read(int(struct.unpack(">H", input.read(2))[0])-2)
                    b = input.read(1)
                width = int(w)
                height = int(h)
            except struct.error:
                raise UnknownImageFormat("StructError" + msg)
            except ValueError:
                raise UnknownImageFormat("ValueError" + msg)
            except Exception as e:
                raise UnknownImageFormat(e.__class__.__name__ + msg)
        else:
            raise UnknownImageFormat(
                "Sorry, don't know how to get information from this file."
            )

    return width, height