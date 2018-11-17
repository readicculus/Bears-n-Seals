import os
import csv

from arcticapi import data_types, image_registration
from arcticapi.label_parser import parse_hotspot


class ArcticApi:
    def __init__(self, csv_path, im_path):
        rows = list()

        f = open(csv_path, 'r')
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
        f.close()
        del rows[0]  # remove col headers


        hsm = data_types.HotSpotMap()
        ringed_seal_ct = 0
        bearded_seal_ct = 0
        polar_bear_ct = 0
        na_seal_ct = 0
        for row in rows:
            hotspot = parse_hotspot(row, im_path)
            if hotspot.classIndex == 0:
                ringed_seal_ct += 1
            elif hotspot.classIndex == 1:
                bearded_seal_ct += 1
            elif hotspot.classIndex == 2:
                polar_bear_ct += 1
            elif hotspot.classIndex == 3:
                na_seal_ct += 1
            hsm.add(hotspot)

        self.hsm = hsm
        print("Ringed Seals: " + str(ringed_seal_ct))
        print("Bearded Seals: " + str(bearded_seal_ct))
        print("Polar Bears: " + str(polar_bear_ct))
        print("NA Seals: " + str(na_seal_ct))
        del rows

    def get_hotspots(self):
        return self.hsm

    def register(self, id=None, showFigures=False, showImgs=False):
        if id is None:
            for hs in self.hsm.hotspots:
                image_registration.register_images(hs, showFigures, showImgs)
        else:
            hs = self.hsm.get_hs(id)
            if hs is not None:
                image_registration.register_images(hs, showFigures, showImgs)


    def crop_label_hotspot(self, out_dir, hotspot, width_bb, minShift, maxShift, label):
        hotspot.genCropsAndLables(out_dir, width_bb, minShift, maxShift, label)

    def crop_label_all(self, out_dir, width_bb, minShift, maxShift, label = "training_list.txt"):
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        i = 0
        for hs in self.hsm.hotspots:
            if hs.classIndex > 1:
                print("Skipping, not a seal")
                continue
            hs.classIndex = 0
            print("Cropping hotspot:" + str(hs.id) + " -" + str(
                round((i + 0.0) / len(self.hsm.hotspots), 2))) + "% complete"
            i += 1
            self.crop_label_hotspot(out_dir, hs, width_bb, minShift, maxShift, label)
