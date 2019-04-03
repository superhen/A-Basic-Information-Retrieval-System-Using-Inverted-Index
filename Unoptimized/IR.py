import time
import os
import pickle
import re
from nltk.stem import PorterStemmer
import sys
from PyQt5.QtWidgets import (QPushButton, QWidget, QLabel, QScrollArea, QLineEdit, QGridLayout, QApplication)
from PyQt5.QtCore import (QCoreApplication,Qt)
from PyQt5.QtGui import *


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    # output: list of paths. e.g. [path1, path2]
    def getFilePath(self):
        textPath = os.getcwd() + '/HillaryEmails'
        if not os.path.exists(textPath):
            raise print('Please put HillaryEmails folder in work path')
        pathList = []
        for (dirpath, dirnames, filenames) in os.walk(textPath):
            for filename in filenames:
                pathList.append(os.path.join(dirpath, filename))
        pathList = sorted(pathList, key=lambda k: int(re.findall(r'(\d+)\.txt', k)[0]))
        return pathList

    # output: string content of one file. e.g. 'this is file content'
    def getFileContent(self, filePath):
        f = open(filePath, 'r')
        fileContent = f.read()
        f.close()
        return fileContent

    # output: list of token pair. e.g. [{token1: path1}, {token2: path1}]
    def tokenization(self, fileContent, filePath):
        tokenList = []
        tokens = fileContent.split()
        for token in tokens:
            if token != "":
                tokenPair = {token: filePath}
                tokenList.append(tokenPair)
        return tokenList

    # output: list of stemmed token pair
    def stemmer(self, tokenList):
        stemmer = PorterStemmer()
        newTokenList = []
        for tokenPair in tokenList:
            token = list(tokenPair.keys())[0]
            newToken = stemmer.stem(token.lower())
            tokenPair[newToken] = tokenPair.pop(token)
            newTokenList.append(tokenPair)
        return newTokenList

    # output: list of all sorted stemmed token pair. e.g. [{token1: path1}, {token1: path2}, {token2: path1}]
    def sortTokens(self):
        allTokenList = []
        pathList = self.getFilePath()
        for filePath in pathList:
            fileContent = self.getFileContent(filePath)
            tokenList = self.tokenization(fileContent, filePath)
            newTokenList = self.stemmer(tokenList)
            allTokenList += newTokenList
        sortedToken = sorted(allTokenList, key=lambda k: (list(k.keys())[0], list(k.values())[0]))
        return sortedToken

    # output: dictionary of inverted index. e.g. {token1: [path1, path2], token2: [path1]}
    def posting(self, sortedToken):
        invertedIndex = {}
        for tokenPair in sortedToken:
            token = list(tokenPair.keys())[0]
            if token not in invertedIndex:
                invertedIndex[token] = [(tokenPair[token])]
            elif (token in invertedIndex) & (tokenPair[token] not in set(invertedIndex[token])):
                invertedIndex[token].append(tokenPair[token])
        return invertedIndex

    # once dump invertedIndex, we can directly load it next time
    def dumpInvertedIndex(self, invertedIndex):
        outputFile = open("invertedIndex.txt", "wb")
        pickle.dump(invertedIndex, outputFile)
        outputFile.close()

    # load invertedIndex
    def loadInvertedIndex(self):
        inputFile = open("invertedIndex.txt", "rb")
        invertedIndex = pickle.load(inputFile)
        inputFile.close()
        return invertedIndex

    # output: list of stemmed query tokens. e.g. [queryToken1, queryToken2]
    def queryProcess(self, query):
        queries = []
        tokens = query.split()
        stemmer = PorterStemmer()
        for token in tokens:
            newToken = stemmer.stem(token.lower())
            if newToken != "":
                queries.append(newToken)
        return queries

    # output: list of matched pathList. e.g. if queryToken1=token1 & queryToken2=token2 then [[path1, path2],[path1]]
    def postingList(self, queries, invertedIndex):
        matchedPostings = []
        for query in queries:
            if query not in invertedIndex:
                matchedPostings = []
                break
            matchedPostings.append(invertedIndex[query])
        return matchedPostings

    # output: list of common matched path. e.g. [path1], which is the common path of two pathList
    def postingMerge(self, matchedPostings):
        if len(matchedPostings) == 0:
            return []
        result = matchedPostings[0]
        if len(matchedPostings) == 1:
            return result
        for posting in matchedPostings[1:]:
            resultTmp = []
            index1, index2 = 0, 0
            len1, len2 = len(result), len(posting)
            while ((index1 < len1) & (index2 < len2)):
                if result[index1] == posting[index2]:
                    resultTmp.append(result[index1])
                    index1 += 1
                    index2 += 1
                elif result[index1] < posting[index2]:
                    index1 += 1
                elif result[index1] > posting[index2]:
                    index2 += 1
            result = resultTmp
        #    result = sorted(list(set(result)), key=lambda k: int(re.findall(r'(\d+)\.txt', k)[0]))
        return result

    # output: string of combined path. e.g. 'path1 \n path2 \n'
    def getResult(self, query):
        if os.path.isfile('invertedIndex.txt'):
            invertedIndex = self.loadInvertedIndex()
        else:
            sortedToken = self.sortTokens()
            invertedIndex = self.posting(sortedToken)
            self.dumpInvertedIndex(invertedIndex)

        queryList = query.split(' OR ')
        result = []
        for query in queryList:
            queries = self.queryProcess(query)
            matchedPostings = self.postingList(queries, invertedIndex)
            result += self.postingMerge(matchedPostings)
        result = sorted(list(set(result)), key=lambda k: int(re.findall(r'(\d+)\.txt', k)[0]))
        finalResult = '<ol>'
        for path in result:
            finalResult = finalResult + "<li>Path:<a href='file://" + path + "'>" + path + '</a></li>'
        finalResult = finalResult + '</ol>'
        return finalResult

    # output: string to show paths
    def noResult(self, query):
        start = time.clock()
        result = self.getResult(query)
        elapsed = "Searching time: " + '%.4f' % (time.clock() - start) + " s"
        if result == "<ol></ol>":
            return 'No result',elapsed
        return result,elapsed

    def initUI(self):
        searchLabel = QLabel('Please input query:')
        searchLabel.setFont(QFont("Arial", 16))
        searchItem = QLineEdit()
        searchTime = QLineEdit()
        searchTime.setReadOnly(True)
        btn1 = QPushButton('Search', self)
        btn2 = QPushButton('Clear', self)
        btn3 = QPushButton('Exit', self)
        searchResult = QLabel()
        searchResult.setOpenExternalLinks(True)
        searchResult.setAlignment(Qt.AlignTop)
        resultScroll = QScrollArea()
        resultScroll.setWidget(searchResult)
        resultScroll.setWidgetResizable(True)
        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0.5)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 0.5)
        grid.setColumnStretch(5, 1)
        grid.setSpacing(5)
        grid.addWidget(searchLabel, 1, 0, 1, 6)
        grid.addWidget(searchItem, 2, 0, 1, 6)
        grid.addWidget(btn1, 3, 2, 1, 2)
        grid.addWidget(btn2, 3, 0, 1, 1)
        grid.addWidget(btn3, 3, 5, 1, 1)
        grid.addWidget(resultScroll, 4, 0, 5, 6)
        grid.addWidget(searchTime, 9, 0, 1, 6)
        self.setLayout(grid)

        def searching():
            result, elapsed = self.noResult(searchItem.text())
            searchResult.setText(result)
            searchTime.setText(elapsed)
            self.repaint()

        btn1.clicked.connect(searching)

        def clear():
            searchResult.setText('')
            searchItem.setText('')
            searchTime.setText('')
            self.repaint()

        btn2.clicked.connect(clear)
        btn3.clicked.connect(QCoreApplication.instance().quit)
        # btn3.clicked.connect(self.close)
        self.setGeometry(400, 150, 600, 500)
        self.setWindowTitle('Information Retrieval System')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())