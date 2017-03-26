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

