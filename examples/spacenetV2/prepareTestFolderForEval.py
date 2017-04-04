import numpy as np
import os
from osgeo import ogr, osr, gdal
import glob
import subprocess

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



def deResRasterList(inputList, outputDirectory, finalPixelSize):

    outputList = []

    for inputImage in inputList:
        baseImageID = os.path.basename(inputImage)
        outputImage = os.path.join(outputDirectory, baseImageID)
        outputImage = deResRasterImage(inputImage, outputImage, finalPixelSize)

        outputList.append(outputImage)

    return outputList

def deResRasterImage(inputImage, outputImage, finalPixelSize):


    cmd = ['gdal_translate', '-of', 'JPEG', '-r', 'cubic', '-outsize', "{}".format(int(finalPixelSize)), '0']
    cmd.append(inputImage)
    cmd.append(outputImage)
    subprocess.call(cmd)

    return outputImage






if __name__ == '__main__':


    outputRasterListFileLoc = '/data/spacenetV2_All.csv'
    dataDirectoryBase = '/data/spacenetV2_Test'
    dataDirectoryLocList = ['AOI_2_Vegas_Test/RGB-PanSharpen/',
                            'AOI_3_Paris_Test/RGB-PanSharpen/',
                            'AOI_4_Shanghai_Test/RGB-PanSharpen/',
                            'AOI_5_Khartoum_Test/RGB-PanSharpen']
    fullimgList = []
    for dataDirectory in dataDirectoryLocList:

        imgList = glob.glob(os.path.join(dataDirectoryBase, dataDirectory, '*.tif'))
        fullimgList.extend(imgList)

    outputRasterList = convertRasterListTo8BitJPEG(fullimgList)

    writeRasterListToFile(outputRasterList, outputRasterListFileLoc)

    outputDirectory = '/data/spacenetV2_Test0p5gsd'
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    outputRasterList0p5m = deResRasterList(outputRasterList, outputDirectory, 400)

    outputRasterListFileLoc = '/data/spacenetV2Test_All_0p5m.csv'
    writeRasterListToFile(outputRasterList0p5m, outputRasterListFileLoc)

    outputDirectory = '/data/spacenetV2_Test0p75gsd'
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    outputRasterList0p75m = deResRasterList(outputRasterList, outputDirectory, 300)

    outputRasterListFileLoc = '/data/spacenetV2Test_All_0p75m.csv'
    writeRasterListToFile(outputRasterList0p75m, outputRasterListFileLoc)


    outputDirectory = '/data/spacenetV2_Test1p0gsd'
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    outputRasterList1p0m = deResRasterList(outputRasterList, outputDirectory, 200)

    outputRasterListFileLoc = '/data/spacenetV2Test_All_1p0m.csv'
    writeRasterListToFile(outputRasterList1p0m, outputRasterListFileLoc)



