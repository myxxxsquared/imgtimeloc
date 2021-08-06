import argparse
import datetime
import hashlib
import imghdr
import json
import os
import shutil

import tqdm
from PIL import Image


def get_date_taken(path):
    try:
        if os.path.exists(path + ".json"):
            j = json.load(open(path + ".json", "rt"))
            if "photoTakenTime" in j:
                t = datetime.datetime.fromtimestamp(j["photoTakenTime"]["timestamp"])
                return t.year, t.month
            if "creationTime" in j:
                t = datetime.datetime.fromtimestamp(j["creationTime"]["timestamp"])
                return t.year, t.month
    except:
        pass
    try:
        timeinfo = Image.open(path)._getexif()[36867]
        return list(map(int, timeinfo.split(" ")[0].split(":")[0:2]))
    except:
        pass
    t = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return t.year, t.month


parser = argparse.ArgumentParser("imgtimeloc")
parser.add_argument("src_dir", type=str)
parser.add_argument("dst_dir", type=str)
args = parser.parse_args()

srcdir, dstdir = args.src_dir, args.dst_dir

picfiles = []

samefilecount = 0

os.makedirs(os.path.join(dstdir, "samefile"), exist_ok=True)

for root, dirs, files in os.walk(srcdir):
    for f in files:
        picfiles.append(os.path.join(root, f))


def md5hash(filename):
    with open(filename, "rb") as f:
        return hashlib.sha512(f.read()).hexdigest()


def renamefile(filename):
    rename_idx = 0
    filenames = list(os.path.split(filename))

    while True:
        basename = list(filenames[-1].split("."))
        if len(basename) > 1:
            basename[-2] = basename[-2] + str(rename_idx)
        else:
            basename[-1] = basename[-1] + str(rename_idx)
        basename = ".".join(basename)
        filenames_dup = list(filenames)
        filenames_dup[-1] = basename
        new_name = os.path.join(*filenames_dup)
        if not os.path.exists(new_name):
            return new_name
        rename_idx += 1


for srcpath in tqdm.tqdm(picfiles):
    assert not os.path.isdir(srcpath)

    if imghdr.what(srcpath) or srcpath.endswith(".MOV") or srcpath.endswith(".3gp") or srcpath.endswith(".mp4") or srcpath.endswith(".MPG"):
        t = get_date_taken(srcpath)
        dstpath = os.path.join(dstdir, str(t[0]), "{:02d}".format(t[1]))
    else:
        dstpath = os.path.join(dstdir, "nonimage")

    os.makedirs(dstpath, exist_ok=True)
    dstpath = os.path.join(dstpath, os.path.basename(srcpath))

    domove = True

    while domove and os.path.exists(dstpath):
        if dstpath == srcpath:
            domove = False
            break
        srchash = md5hash(srcpath)
        dsthash = md5hash(dstpath)
        if srchash == dsthash:
            dstpath = os.path.join(dstdir, "samefile", str(samefilecount) + "_" + os.path.basename(srcpath))
            samefilecount += 1
        else:
            dstpath = renamefile(dstpath)

    if domove:
        shutil.move(srcpath, dstpath)
