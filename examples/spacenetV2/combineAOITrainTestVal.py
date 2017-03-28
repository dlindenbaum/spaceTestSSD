import os
import random
if __name__ == '__main__':


    outputRasterListFileLoc = '/data/spacenetV2_All.csv'
    dataDirectoryBase = '/data/'#/data/spacenetV2_Test'
    dataDirectoryLocList = ['spacenet_Trainannotation',
                            'spacenet_TrainAOI3annotation',
                            'spacenet_TrainAOI4annotation',
                            'spacenet_TrainAOI5annotation']
    fileList = ['test_name_size.txt', 'test.txt', 'trainval.txt']

    fullimgList = []

    dataOutputDirectory = '/data/spacenet_TrainAOIALlannotation'
    test_name_sizeList = []
    testList = []
    trainValList = []
    testSize = 500
    trainSize = 1000
    for dataDirectory in dataDirectoryLocList:

        with open(os.path.join(dataDirectoryBase, dataDirectory, 'test.txt')) as ftest:
            testFileTmp = ftest.readlines()


        with open(os.path.join(dataDirectoryBase, dataDirectory, 'test_name_size.txt')) as ftestname:
            testNameFileTmp = ftestname.readlines()


        with open(os.path.join(dataDirectoryBase, dataDirectory, 'trainval.txt')) as ftestname:
            trainvalFileTmp = ftestname.readlines()


        testIndex = random.sample(xrange(len(testFileTmp)), testSize)
        trainIndex = random.sample(xrange(len(trainvalFileTmp)), trainSize)
        for idx in testIndex:
            test_name_sizeList.append(testNameFileTmp[idx])
            testList.append(testFileTmp[idx])
        for idx in trainIndex:
            trainValList.append(trainvalFileTmp[idx])

    with open(os.path.join(dataOutputDirectory, 'trainval.txt'), 'w') as f:
        for line in trainValList:
            f.write(line)

    with open(os.path.join(dataOutputDirectory, 'test.txt'), 'w') as f:
        for line in testList:
            f.write(line)

    with open(os.path.join(dataOutputDirectory, 'test_name_size.txt'), 'w') as f:
        for line in test_name_sizeList:
            f.write(line)
