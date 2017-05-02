import numpy as np
import os
from osgeo import ogr, osr, gdal
import glob
import subprocess
import cv2
import csv

def convertRasterListTo8BitJPEG(rasterImageList):

    outputPixType = 'Byte'
    outputFormat = 'JPEG'
    outputRasterList = []
    convertTo8Bit = True



    for rasterImageName in rasterImageList:
        srcRaster = gdal.Open(rasterImageName)
        outputRaster = rasterImageName

        if convertTo8Bit:
            cmd = ['gdal_translate', '-ot', outputPixType, '-of', outputFormat, '-co', '"PHOTOMETRIC=rgb"']
            scaleList = []
            for bandId in range(srcRaster.RasterCount):
                bandId = bandId + 1
                band = srcRaster.GetRasterBand(bandId)
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

    return outputRasterList


def writeRasterListToFile(outputRasterList, outputRasterListFileLoc):
    with open(outputRasterListFileLoc, 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')

        for outputRaster in outputRasterList:
            csvwriter.writerow([outputRaster])

def readRasterListToFile(outputRasterListFileLoc):
    with open(outputRasterListFileLoc, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        outputRasterList = []
        for line  in csvreader:
            print(line)
            outputRasterList.append(line[0])

    return outputRasterList


def deResRasterList(inputList, outputDirectory, deResPixelSize, finalPixelSize=-1, gausianBlur=-1):

    outputList = []
    if finalPixelSize == -1:
        finalPixelSize = deResPixelSize

    for inputImage in inputList:
        baseImageID = os.path.basename(inputImage)
        outputImage = os.path.join(outputDirectory, baseImageID)
        outputImage = deResRasterImage(inputImage, outputImage, deResPixelSize, finalPixelSize=finalPixelSize,
                                       gausianBlur=gausianBlur)
        print(outputImage)
        outputList.append(outputImage)

    return outputList

def deResRasterImage(inputImage, outputImage, deResPixelSize, finalPixelSize=-1, gausianBlur=-1):


    tmpImage = os.path.splitext(outputImage)[0]+ '.vrt'

    if finalPixelSize == -1:
       finalPixelSize = deResPixelSize

    cmd = ['gdal_translate', '-of', 'VRT', '-r', 'cubic', '-outsize', "{}".format(int(deResPixelSize)), '0']
    cmd.append(inputImage)
    cmd.append(tmpImage)
    subprocess.call(cmd)

    cmd = ['gdal_translate', '-of', 'JPEG', '-r', 'cubic', '-outsize', "{}".format(int(finalPixelSize)), '0']
    cmd.append(tmpImage)
    cmd.append(outputImage)
    subprocess.call(cmd)

def deResRasterListBlur(inputList, outputDirectory, outGSD, inGSD):

    outputList = []
    for inputImage in inputList:
        baseImageID = os.path.basename(inputImage)
        outputImage = os.path.join(outputDirectory, baseImageID)
        outputImage = deResRasterImageBlur(inputImage, outputImage, outGSD, inGSD)

        outputList.append(outputImage)

    return outputList

def deResRasterImageBlur(inputImage, outputImage, outGSD, inGSD):
    img_in = cv2.imread(inputImage, 1)

    # set kernel, if kernel = 1 blur will be non-zero, so mult by 0.5
    kernel = 0.5 * outGSD / inGSD  # int(round(blur_meters/GSD_in))
    img_out = cv2.GaussianBlur(img_in, (0, 0), kernel, kernel, 0)

    # may want to rescale?
    # reshape, assume that the pixel density is double the point spread
    # function sigma value
    # use INTER_AREA interpolation function
    rescale_frac = inGSD / outGSD
    rescale_shape = int(np.rint(img_in.shape[0] * rescale_frac))  # / kernel)# * 0.5)# * 2
    # print "rescale_shape:", rescale_shape
    # print "f", f, "kernel", kernel, "shape_in", img_in.shape[0], "shape_out", rescale_shape

    # resize to the appropriate number of pixels for the given GSD
    img_out = cv2.resize(img_out, (rescale_shape, rescale_shape), interpolation=cv2.INTER_AREA)
    resize_orig = True
    if resize_orig:
        # scale back up to original size (useful for length calculations, but
        #   keep pixelization)
        img_out = cv2.resize(img_out, img_in.shape[:2], interpolation=cv2.INTER_CUBIC)  # cv2.INTER_NEAREST)


    cv2.imwrite(outputImage, img_out)

    return outputImage






if __name__ == '__main__':


    outputRasterListFileLoc = '/data/spacenetV2_All.csv'
    dataDirectoryBase = '/data/spacenetV2_Test'
    dataDirectoryLocList = ['AOI_2_Vegas_Test/RGB-PanSharpen/',
                            'AOI_3_Paris_Test/RGB-PanSharpen/',
                            'AOI_4_Shanghai_Test/RGB-PanSharpen/',
                            'AOI_5_Khartoum_Test/RGB-PanSharpen']
    fullimgList = []
    gdalTranslate = False
    gausianBlur = True
    recreate8bitRasterList = False
    for dataDirectory in dataDirectoryLocList:

        imgList = glob.glob(os.path.join(dataDirectoryBase, dataDirectory, '*.tif'))
        fullimgList.extend(imgList)
    if recreate8bitRasterList:
        outputRasterList = convertRasterListTo8BitJPEG(fullimgList)
        writeRasterListToFile(outputRasterList, outputRasterListFileLoc)
    else:
        outputRasterList = readRasterListToFile(outputRasterListFileLoc)

    outputDirectory = '/data/spacenetV2_Test0p5gsd'
    if gdalTranslate:
        outputDirectory = '/data/spacenetV2_Test0p5gsd'
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        outputRasterList0p5m = deResRasterList(outputRasterList, outputDirectory, 400, finalPixelSize=650)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_0p5m.csv'
        writeRasterListToFile(outputRasterList0p5m, outputRasterListFileLoc)

        outputDirectory = '/data/spacenetV2_Test0p75gsd'
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        outputRasterList0p75m = deResRasterList(outputRasterList, outputDirectory, 300, finalPixelSize=650)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_0p75m.csv'
        writeRasterListToFile(outputRasterList0p75m, outputRasterListFileLoc)


        outputDirectory = '/data/spacenetV2_Test1p0gsd'
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        outputRasterList1p0m = deResRasterList(outputRasterList, outputDirectory, 200, finalPixelSize=650)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_1p0m.csv'
        writeRasterListToFile(outputRasterList1p0m, outputRasterListFileLoc)


    if gausianBlur:
        outputDirectory = '/data/spacenetV2_Test0p6gsdblur'
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)
        print ('blurTime)')
        outputRasterList0p5m = deResRasterListBlur(outputRasterList, outputDirectory, 0.6, 0.3)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_0p6mblur.csv'
        writeRasterListToFile(outputRasterList0p5m, outputRasterListFileLoc)

        outputDirectory = '/data/spacenetV2_Test0p9gsdblur'
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        outputRasterList0p75m = deResRasterListBlur(outputRasterList, outputDirectory, 0.9, 0.3)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_0p9mBlur.csv'
        writeRasterListToFile(outputRasterList0p75m, outputRasterListFileLoc)

        outputDirectory = '/data/spacenetV2_Test1p25gsdblur'
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        outputRasterList1p0m = deResRasterListBlur(outputRasterList, outputDirectory, 1.2, 0.3)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_1p2mblur.csv'
        writeRasterListToFile(outputRasterList1p0m, outputRasterListFileLoc)
