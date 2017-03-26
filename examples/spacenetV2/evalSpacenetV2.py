import numpy as np
import os
from osgeo import ogr, osr, gdal
import glob
import subprocess
import csv
# Make sure that caffe is on the python path:
try:
    caffe_root = os.environ['CAFFE_ROOT']  # this file is expected to be in {caffe_root}/examples
except:
    caffe_root = '/opt/spaceSSD/caffe-ssd/'

import os
os.chdir(caffe_root)
import sys
sys.path.insert(0, 'python')

import caffe
caffe.set_device(0)
caffe.set_mode_gpu()

from google.protobuf import text_format
from caffe.proto import caffe_pb2

# load PASCAL VOC labels
model_def = '/data/models/VGGNet/VOC0712/SSD_500x500/deploy.prototxt'
model_weights = '/data/models/VGGNet/VOC0712/SSD_500x500/VGG_VOC0712_SSD_500x500_iter_18000.caffemodel'
labelmap_file = '/opt/spaceSSD/caffe-ssd/data/spacenetV2/labelmap_spacenet.prototxt'
outputRasterFileName = '/data/spacenetV2_All.csv'
solutionFileLocation = '/data/solutionFileAll.csv'
confidenceValue = 0.2

# read labelmap file
file = open(labelmap_file, 'r')
labelmap = caffe_pb2.LabelMap()
text_format.Merge(str(file.read()), labelmap)

def get_labelname(labelmap, labels):
    num_labels = len(labelmap.item)
    labelnames = []
    if type(labels) is not list:
        labels = [labels]
    for label in labels:
        found = False
        for i in xrange(0, num_labels):
            if label == labelmap.item[i].label:
                found = True
                labelnames.append(labelmap.item[i].display_name)
                break
        assert found == True
    return labelnames


## create network file

net = caffe.Net(model_def,      # defines the structure of the model
                model_weights,  # contains the trained weights
                caffe.TEST)     # use test mode (e.g., don't perform dropout)

# input preprocessing: 'data' is the name of the input blob == net.inputs[0]
transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
transformer.set_transpose('data', (2, 0, 1))
transformer.set_mean('data', np.array([104 ,117 ,123])) # mean pixel
transformer.set_raw_scale('data', 255)  # the reference model operates on images in [0,255] range instead of [0,1]
transformer.set_channel_swap('data', (2 ,1 ,0))  # the reference model has channels in BGR order instead of RGB

outputRasterList = []
with open(outputRasterFileName, 'r') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in csvreader:
        outputRasterList.append(row[0])


## load outputRasterList File
# load an image to evaluate

buildingEntryList = []
for outputRaster in outputRasterList:
    buildingId = 0
    exampleImage = outputRaster
    image = caffe.io.load_image(outputRaster)
    # plt.imshow(image)
    imageId = os.path.basename(outputRaster)
    imageId = imageId.replace('.jpg', '')

    imageId = imageId.replace('RGB-PanSharpen_', '')
    ## run Net
    transformed_image = transformer.preprocess('data', image)
    net.blobs['data'].data[...] = transformed_image

    # Forward pass.
    detections = net.forward()['detection_out']

    # Parse the outputs.
    det_label = detections[0 ,0 ,: ,1]
    det_conf = detections[0 ,0 ,: ,2]
    det_xmin = detections[0 ,0 ,: ,3]
    det_ymin = detections[0 ,0 ,: ,4]
    det_xmax = detections[0 ,0 ,: ,5]
    det_ymax = detections[0 ,0 ,: ,6]

    # Get detections with confidence higher than 0.6.
    top_indices = [i for i, conf in enumerate(det_conf) if conf >= confidenceValue]

    top_conf = det_conf[top_indices]
    top_label_indices = det_label[top_indices].tolist()
    top_labels = get_labelname(labelmap, top_label_indices)
    top_xmin = det_xmin[top_indices]
    top_ymin = det_ymin[top_indices]
    top_xmax = det_xmax[top_indices]
    top_ymax = det_ymax[top_indices]
    for i in xrange(top_conf.shape[0]):
        buildingId = buildingId+ 1
        xmin = ((top_xmin[i] * image.shape[1]))
        ymin = ((top_ymin[i] * image.shape[0]))
        xmax = ((top_xmax[i] * image.shape[1]))
        ymax = ((top_ymax[i] * image.shape[0]))

        # Create ring
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(xmin, ymin)
        ring.AddPoint(xmin, ymax)
        ring.AddPoint(xmax, ymax)
        ring.AddPoint(xmax, ymin)
        ring.AddPoint(xmin, ymin)

        # Create polygon
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        print poly.ExportToWkt()
        print(top_conf[i])
        buildingEntry = [imageId, buildingId, poly.ExportToWkt(), top_conf[i]]
        print(buildingEntry)
        buildingEntryList.append(buildingEntry)
        print("ImageId = {}, {},{},{},{}".format(imageId, xmin, ymin, xmax, ymax))
    if buildingId == 0:
        buildingEntry = [imageId, -1, "Polygon EMPTY", 1]
        buildingEntryList.append(buildingEntry)

with open(solutionFileLocation, 'wb') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=', ', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow(['ImageId', 'BuildingId', 'PolygonWKT', 'Confidence'])
    for buildingEntry in buildingEntryList:
        csvwriter.writerow(buildingEntry)