import os
import imgaug as ia

from src.arcticapi.model.BoundingBox import BoundingBox

SpeciesList = ["Ringed Seal", "Bearded Seal", "UNK Seal", "Polar Bear", "NA", "Walrus", "Caribou", "Fox", "Bird", "UNK Animal", "Cetacean"]
ColorsList = [(0, 255, 0), (243, 182, 31), (81, 13, 10), (256, 256, 256), (256, 256, 256)]


class HotSpot:
    def __init__(self, id, xpos, ypos, thumb_left, thumb_top, thumb_right, thumb_bottom, type, species_id, rgb
                 , ir, timestamp, project_name, aircraft,
                 updated_top=-1, updated_bot=-1, updated_left=-1, updated_right=-1,
                 updated=False, status="none", confidence="NA"):
        self.id = id  # id_hotspot
        self.thermal_loc = (xpos, ypos)  # location in thermal image
        # Bounding box
        self.rgb_bb_l = thumb_left
        self.rgb_bb_r = thumb_right
        self.rgb_bb_t = thumb_top
        self.rgb_bb_b = thumb_bottom
        # Center point
        self.center_x = thumb_left + ((thumb_right - thumb_left) / 2)
        self.center_y = thumb_bottom + ((thumb_top - thumb_bottom) / 2)
        self.type = type  # type of hotspot (Animal, Anomaly...)
        self.species = species_id  # species (Ringed, Bearded..)
        self.classIndex = SpeciesList.index(species_id)  # class index
        self.rgb = rgb  # RGB AerialImage
        self.ir = ir  # IR AerialImage
        self.timestamp = timestamp  # timestamp
        self.project_name = project_name  # name of the projects usually CHESS
        self.aircraft = aircraft  # aircraft tail number
        # New columns for re-labeled csv files
        self.updated_top = updated_top
        self.updated_bot = updated_bot
        self.updated_left = updated_left
        self.updated_right = updated_right
        self.updated = updated
        self.status = status
        self.confidence = confidence

        b, t, l, r = self.getBTLR()
        b = BoundingBox(l, t, r, b, self.classIndex, self.id)
        self.rgb_bb = b

    def getSpecies(self):
        return SpeciesList[self.classIndex]

    def load_all(self):
        if self.rgb.load_image() and self.ir.load_image():
            return True
        else:
            print("Skipped " + self.id)
            return False

    def free_all(self):
        self.rgb.free()
        self.ir.free()

    def toCSVRow(self, new=False):
        _, irpath = os.path.split(self.ir.path)
        _, rgbpath = os.path.split(self.rgb.path)
        if new: # new dataset
            cols = ["-1", rgbpath, irpath, str(self.id), str(self.type),
                    str(self.species), self.confidence, self.rgb.fog,
                    str(self.thermal_loc[0]), str(self.thermal_loc[1]),
                    str(self.rgb_bb_l), str(self.rgb_bb_t), str(self.rgb_bb_r), str(self.rgb_bb_b), str(self.updated_left), str(self.updated_top), str(self.updated_right),
                    str(self.updated_bot), str.lower(str(self.updated)), str(self.status)]
            return ",".join(cols) + "\n"
        else: # old dataset format
            cols = [str(self.id), str(self.timestamp), irpath, "none", rgbpath, str(self.thermal_loc[0]),
                    str(self.thermal_loc[1]),
                    str(self.rgb_bb_l), str(self.rgb_bb_t), str(self.rgb_bb_r), str(self.rgb_bb_b), str(self.type),
                    str(self.species), str(self.updated_bot), str(self.updated_top), str(self.updated_left),
                    str(self.updated_right), str.lower(str(self.updated)), str(self.status)]
            return ",".join(cols) + "\n"

    def getRGBCenterPt(self):
        b, t, l, r = self.getBTLR()
        x = l + ((r - l) / 2)
        y = t + ((b - t) / 2)
        return (x, y)

    def getIRCenterPt(self):
        return (self.center_x, self.center_y)

    # returns (x, y, w, h) in yolo format
    def getYoloBBox(self, img):
        l = self.rgb_bb_l
        r = self.rgb_bb_r
        t = self.rgb_bb_t
        b = self.rgb_bb_b
        if self.updated:
            l = self.updated_left
            r = self.updated_right
            t = self.updated_top
            b = self.updated_bot
        w = r - l
        h = b - t
        cx = l + (w / 2.0)
        cy = t + (h / 2.0)
        yolox = float(cx) / float(img.shape[1])
        yolow = float(w) / float(img.shape[1])
        yoloy = float(cy) / float(img.shape[0])
        yoloh = float(h) / float(img.shape[0])
        return yolox, yoloy, yolow, yoloh

    def getBTLR(self, forceOld = False):
        if not forceOld and (self.updated and not self.isStatusRemoved() and not self.updated_left == -1 and not self.updated_right == -1):
            return self.updated_bot, self.updated_top, self.updated_left, self.updated_right
        else:
            return self.rgb_bb_b, self.rgb_bb_t, self.rgb_bb_l, self.rgb_bb_r

    def isStatusRemoved(self):
        return 'removed' in self.status

    def filterClass(self, cfg):
        # don't make crops or labels for bears
        if not cfg.make_bear and self.classIndex == 3:
            return True
        # don't make crops or labels for anomalies
        if not cfg.make_anomaly and self.classIndex == 4:
            return True

    def update_bbox(self, x1, y1, x2, y2):
        self.updated_top = y1
        self.updated_bot = y2
        self.updated_left = x1
        self.updated_right = x2
        if self.updated_top > self.updated_bot:
            tmp = self.updated_top
            self.updated_top = self.updated_bot
            self.updated_bot = tmp

        if self.updated_left > self.updated_right:
            tmp = self.updated_right
            self.updated_left = self.updated_right
            self.updated_left = tmp

        b = ia.BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2, label=self.classIndex)
        b.hsId = self.id
        self.rgb_bb = b

