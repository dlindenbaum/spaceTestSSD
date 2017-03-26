
# coding: utf-8

# In[2]:

### 1. Setup
#* First, Load necessary libs and set up caffe and caffe_root


# In[8]:

import numpy as np
import matplotlib.pyplot as plt
import os
from osgeo import ogr, osr, gdal
import glob
import subprocess
get_ipython().magic(u'matplotlib inline')

plt.rcParams['figure.figsize'] = (10, 10)
plt.rcParams['image.interpolation'] = 'nearest'
plt.rcParams['image.cmap'] = 'gray'

# Make sure that caffe is on the python path:
caffe_root = os.environ['CAFFE_ROOT']  # this file is expected to be in {caffe_root}/examples
import os
os.chdir(caffe_root)
import sys
sys.path.insert(0, 'python')

import caffe
caffe.set_device(0)
caffe.set_mode_gpu()



# In[11]:

## Convert All images to 3band byte JPEG
import csv
outputRasterListFileLoc = '/data/spacenetV2_Test/testrasterList.csv'
outputPixType = 'Byte'
outputFormat = 'JPEG'
outputRasterList = []
convertTo8Bit=True

rasterImageLocation = '/data/spacenetV2_Test/AOI_2_Vegas_Test/RGB-PanSharpen/'
rasterImageList = glob.glob(os.path.join(rasterImageLocation, '*.tif'))

for rasterImageName in rasterImageList:
    srcRaster = gdal.Open(rasterImageName)
    outputRaster = rasterImageName
    
    if convertTo8Bit:
        cmd = ['gdal_translate', '-ot', outputPixType, '-of', outputFormat, '-co', '"PHOTOMETRIC=rgb"']
        scaleList = []
        for bandId in range(srcRaster.RasterCount):
            bandId = bandId+1
            band=srcRaster.GetRasterBand(bandId)
            min = band.GetMinimum()
            max = band.GetMaximum()

            # if not exist minimum and maximum values
            if min is None or max is None:
                (min, max) = band.ComputeRasterMinMax(1)
            cmd.append('-scale_{}'.format(bandId))
            cmd.append('{}'.format(0))
            cmd.append('{}'.format(max))
            cmd.append('{}'.format(0))
            cmd.append('{}'.format(255))

        cmd.append(rasterImageName)

        if outputFormat == 'JPEG':
            outputRaster = outputRaster.replace('.tif', '.jpg')
        else:
            outputRaster = outputRaster.replace('.xml', '.tif')

        outputRaster = outputRaster.replace('_img', '_img')
        outputRasterList.append(outputRaster)
        cmd.append(outputRaster)
        print(cmd)
        subprocess.call(cmd)
        
with open(outputRasterListFileLoc, 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    
    for outputRaster in outputRasterList:
        csvwriter.writerow([outputRaster])
        



# In[12]:

# setup Evaluator
from google.protobuf import text_format
from caffe.proto import caffe_pb2

# load PASCAL VOC labels
labelmap_file = '/opt/spaceSSD/caffe-ssd/data/spacenetV2/labelmap_spacenet.prototxt'
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


# In[13]:

model_def = '/data/models/VGGNet/VOC0712/SSD_500x500/deploy.prototxt'
model_weights = '/data/models/VGGNet/VOC0712/SSD_500x500/VGG_VOC0712_SSD_500x500_iter_18000.caffemodel'

net = caffe.Net(model_def,      # defines the structure of the model
                model_weights,  # contains the trained weights
                caffe.TEST)     # use test mode (e.g., don't perform dropout)

# input preprocessing: 'data' is the name of the input blob == net.inputs[0]
transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
transformer.set_transpose('data', (2, 0, 1))
transformer.set_mean('data', np.array([104,117,123])) # mean pixel
transformer.set_raw_scale('data', 255)  # the reference model operates on images in [0,255] range instead of [0,1]
transformer.set_channel_swap('data', (2,1,0))  # the reference model has channels in BGR order instead of RGB


# In[15]:

# load an image to evaluate
confidenceValue = 0.2
buildingEntryList = []
for outputRaster in outputRasterList:
    buildingId = 0
    exampleImage = outputRaster
    image = caffe.io.load_image(outputRaster)
    #plt.imshow(image)
    imageId = os.path.basename(outputRaster)
    imageId = imageId.replace('.jpg', '')
    
    imageId = imageId.replace('RGB-PanSharpen_', '')
    ## run Net
    transformed_image = transformer.preprocess('data', image)
    net.blobs['data'].data[...] = transformed_image
    
    # Forward pass.
    detections = net.forward()['detection_out']
    
    # Parse the outputs.
    det_label = detections[0,0,:,1]
    det_conf = detections[0,0,:,2]
    det_xmin = detections[0,0,:,3]
    det_ymin = detections[0,0,:,4]
    det_xmax = detections[0,0,:,5]
    det_ymax = detections[0,0,:,6]
    
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
        buildingId = buildingId+1
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
        buildingEntry = [imageId, buildingId, poly.ExportToWkt(), 1]
        print(buildingEntry)
        buildingEntryList.append(buildingEntry)
        print("ImageId = {}, {},{},{},{}".format(imageId,  xmin, ymin, xmax, ymax))
    if buildingId == 0:
        buildingEntry = [imageId, -1, "Polygon EMPTY", 1]
        buildingEntryList.append(buildingEntry)


# In[ ]:



