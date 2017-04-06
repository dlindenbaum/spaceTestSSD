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



def deResRasterList(inputList, outputDirectory, deResPixelSize, finalPixelSize=-1, gausianBlur=-1):

    outputList = []
    if finalPixelSize == -1:
        finalPixelSize = deResPixelSize

    for inputImage in inputList:
        baseImageID = os.path.basename(inputImage)
        outputImage = os.path.join(outputDirectory, baseImageID)
        outputImage = deResRasterImage(inputImage, outputImage, deResPixelSize, finalPixelSize=finalPixelSize,
                                       gausianBlur=gausianBlur)

        outputList.append(outputImage)

    return outputList

def deResRasterImage(inputImage, outputImage, deResPixelSize, finalPixelSize=-1, gausianBlur=-1):

    if gausianBlur == -1:
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
    else:

        img = cv2.imread(inputImage)
        bluimg = cv2.GaussianBlur(img, (gausianBlur, gausianBlur), 0)
        imgNew = cv2.resize(bluimg, (deResPixelSize, deResPixelSize), interpolation=cv2.INTER_CUBIC)
        imgNew = cv2.resize(imgNew, (finalPixelSize, finalPixelSize), interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(outputImage, imgNew)

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
    for dataDirectory in dataDirectoryLocList:

        imgList = glob.glob(os.path.join(dataDirectoryBase, dataDirectory, '*.tif'))
        fullimgList.extend(imgList)

    outputRasterList = convertRasterListTo8BitJPEG(fullimgList)

    writeRasterListToFile(outputRasterList, outputRasterListFileLoc)

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
        outputRasterList0p5m = deResRasterList(outputRasterList, outputDirectory, 333, finalPixelSize=650, gausianBlur=1)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_0p6mblur.csv'
        writeRasterListToFile(outputRasterList0p5m, outputRasterListFileLoc)

        outputDirectory = '/data/spacenetV2_Test0p9gsdblur'
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        outputRasterList0p75m = deResRasterList(outputRasterList, outputDirectory, 222, finalPixelSize=650, gausianBlur=2)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_0p9mBlur.csv'
        writeRasterListToFile(outputRasterList0p75m, outputRasterListFileLoc)

        outputDirectory = '/data/spacenetV2_Test1p25gsdblur'
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        outputRasterList1p0m = deResRasterList(outputRasterList, outputDirectory, 166, finalPixelSize=650, gausianBlur=3)

        outputRasterListFileLoc = '/data/spacenetV2Test_All_1p2mblur.csv'
        writeRasterListToFile(outputRasterList1p0m, outputRasterListFileLoc)
