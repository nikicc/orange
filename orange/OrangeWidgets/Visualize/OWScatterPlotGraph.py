#
# OWScatterPlotGraph.py
#
# the base for scatterplot


from OWVisGraph import *
import time
from orngCI import FeatureByCartesianProduct

class QwtPlotCurvePieChart(QwtPlotCurve):
	def __init__(self, parent = None, text = None):
		QwtPlotCurve.__init__(self, parent, text)
		self.color = Qt.black
		self.penColor = Qt.black

	def draw(self, p, xMap, yMap, f, t):
		# save ex settings
		back = p.backgroundMode()
		pen = p.pen()
		brush = p.brush()
		colors = ColorPaletteHSV(self.dataSize())

		p.setBackgroundMode(Qt.OpaqueMode)
		#p.setBackgroundColor(self.color)
		for i in range(1, self.dataSize()):
			p.setBrush(QBrush(colors.getColor(i)))
			p.setPen(QPen(colors.getColor(i)))

			factor = self.percentOfTotalData * self.percentOfTotalData
			px1 = xMap.transform(self.x(0)-0.1 - 0.5*factor)
			py1 = yMap.transform(self.x(1)-0.1 - 0.5*factor)
			px2 = xMap.transform(self.x(0)+0.1 + 0.5*factor)
			py2 = yMap.transform(self.x(1)+0.1 + 0.5*factor)
			p.drawPie(px1, py1, px2-px1, py2-py1, self.y(i-1)*16*360, (self.y(i)-self.y(i-1))*16*360)

		# restore ex settings
		p.setBackgroundMode(back)
		p.setPen(pen)
		p.setBrush(brush)



###########################################################################################
##### CLASS : OWSCATTERPLOTGRAPH
###########################################################################################
class OWScatterPlotGraph(OWVisGraph):
	def __init__(self, scatterWidget, parent = None, name = None):
		"Constructs the graph"
		OWVisGraph.__init__(self, parent, name)

		self.jitterContinuous = 0
		self.enabledLegend = 0
		self.showAttributeValues = 1
		self.showDistributions = 1
		self.toolRects = []
		self.tooltipData = []
		self.showManualAxisScale = 0
		self.optimizedDrawing = 1
		self.scatterWidget = scatterWidget
		self.kNNOptimization = None

	#########################################################
	# update shown data. Set labels, coloring by className ....
	def updateData(self, xAttr, yAttr, colorAttr, shapeAttr = "", sizeShapeAttr = "", showColorLegend = 0, statusBar = None, **args):
		self.removeDrawingCurves()  # my function, that doesn't delete selection curves
		self.removeMarkers()
		self.tips.removeAll()
		self.enableLegend(0)
		self.removeTooltips()

		if len(self.scaledData) == 0:
			self.setAxisScale(QwtPlot.xBottom, 0, 1, 1)
			self.setAxisScale(QwtPlot.yLeft, 0, 1, 1)
			self.setXaxisTitle(""); self.setYLaxisTitle("")
			return
		
		self.statusBar = statusBar
		toolTipList = [xAttr, yAttr]
		if shapeAttr != "" and shapeAttr != "(One shape)": toolTipList.append(shapeAttr)
		if sizeShapeAttr != "" and sizeShapeAttr != "(One size)": toolTipList.append(sizeShapeAttr)

		# initial var values
		self.showKNNModel = 0
		self.showCorrect = 1
		self.__dict__.update(args)

		(xVarMin, xVarMax) = self.attrValues[xAttr]
		(yVarMin, yVarMax) = self.attrValues[yAttr]
		xVar = xVarMax - xVarMin
		yVar = yVarMax - yVarMin
		
		MIN_SHAPE_SIZE = 6
		MAX_SHAPE_DIFF = self.pointWidth

		if self.rawdata.domain[xAttr].varType == orange.VarTypes.Continuous:
			self.setXlabels(None)
			if self.showManualAxisScale: self.setAxisScale(QwtPlot.xBottom, xVarMin - (self.jitterSize * xVar / 80.0), xVarMax + (self.jitterSize * xVar / 80.0) + showColorLegend * xVar/20, 1)			
		else:
			self.setXlabels(getVariableValuesSorted(self.rawdata, xAttr))
			if self.showDistributions == 1: self.setAxisScale(QwtPlot.xBottom, xVarMin - 0.4, xVarMax + 0.4, 1)
			else: self.setAxisScale(QwtPlot.xBottom, xVarMin - 0.5, xVarMax + 0.5 + showColorLegend * xVar/20, 1)			

		if self.rawdata.domain[yAttr].varType == orange.VarTypes.Continuous:
			self.setYLlabels(None)
			if self.showManualAxisScale: self.setAxisScale(QwtPlot.yLeft, yVarMin - (self.jitterSize * yVar / 80.0), yVarMax + (self.jitterSize * yVar / 80.0), 1)			
		else:
			self.setYLlabels(getVariableValuesSorted(self.rawdata, yAttr))
			if self.showDistributions == 1: self.setAxisScale(QwtPlot.yLeft, yVarMin - 0.4, yVarMax + 0.4, 1)
			else: self.setAxisScale(QwtPlot.yLeft, yVarMin - 0.5, yVarMax + 0.5, 1)

		if self.showXaxisTitle == 1: self.setXaxisTitle(xAttr)
		if self.showYLaxisTitle == 1: self.setYLaxisTitle(yAttr)

		if self.showAttributeValues == 0:
			self.setAxisScaleDraw(QwtPlot.xBottom, HiddenScaleDraw())
			self.setAxisScaleDraw(QwtPlot.yLeft, HiddenScaleDraw())
			scaleDraw = self.axisScaleDraw(QwtPlot.xBottom)
			scaleDraw.setTickLength(1, 1, 0)
			scaleDraw = self.axisScaleDraw(QwtPlot.yLeft)
			scaleDraw.setTickLength(1, 1, 0)
		else:
			scaleDraw = self.axisScaleDraw(QwtPlot.xBottom)
			scaleDraw.setTickLength(1, 1, 3)
			scaleDraw = self.axisScaleDraw(QwtPlot.yLeft)
			scaleDraw.setTickLength(1, 1, 3)
			
		
		colorIndex = -1
		if colorAttr != "" and colorAttr != "(One color)":
			colorIndex = self.attributeNames.index(colorAttr)
			
		shapeIndex = -1
		shapeIndices = {}
		if shapeAttr != "" and shapeAttr != "(One shape)" and len(self.rawdata.domain[shapeAttr].values) < 11:
			shapeIndex = self.attributeNames.index(shapeAttr)
			shapeIndices = getVariableValueIndices(self.rawdata, shapeAttr)

		sizeShapeIndex = -1
		if sizeShapeAttr != "" and sizeShapeAttr != "(One size)":
			sizeShapeIndex = self.attributeNames.index(sizeShapeAttr)

		# create hash tables in case of discrete X axis attribute
		attrXIndices = {}
		discreteX = 0
		if self.rawdata.domain[xAttr].varType == orange.VarTypes.Discrete:
			discreteX = 1
			attrXIndices = getVariableValueIndices(self.rawdata, xAttr)

		# create hash tables in case of discrete Y axis attribute
		attrYIndices = {}
		discreteY = 0
		if self.rawdata.domain[yAttr].varType == orange.VarTypes.Discrete:
			discreteY = 1
			attrYIndices = getVariableValueIndices(self.rawdata, yAttr)

		#######
		# show the distributions
		if self.showDistributions == 1 and colorIndex != -1 and self.rawdata.domain[colorIndex].varType == orange.VarTypes.Discrete and self.rawdata.domain[xAttr].varType == orange.VarTypes.Discrete and self.rawdata.domain[yAttr].varType == orange.VarTypes.Discrete and not self.showKNNModel:
			(cart, profit) = FeatureByCartesianProduct(self.rawdata, [self.rawdata.domain[xAttr], self.rawdata.domain[yAttr]])
			tempData = self.rawdata.select(list(self.rawdata.domain) + [cart])
			contXY = orange.ContingencyAttrClass(cart, tempData)   # distribution of X attribute
			xValues = getVariableValuesSorted(self.rawdata, xAttr)
			yValues = getVariableValuesSorted(self.rawdata, yAttr)
			classValuesSorted = getVariableValuesSorted(self.rawdata, colorIndex)
			classValues = list(self.rawdata.domain[colorIndex].values)

			sum = 0
			for table in contXY:
				for val in table: sum += val

			for i in range(len(xValues)):
				for j in range(len(yValues)):
					try: distribution = contXY[str(xValues[i])+'-'+str(yValues[j])]
					except: continue
					tempSum = 0
					for val in distribution: tempSum += val
					if tempSum == 0: continue

					tooltipText = "Nr. of examples: <b>%d</b> (%.2f%%) <br>Distribution:" % (tempSum, 100.0*float(tempSum)/float(sum))
					out = [0.0]
					key = self.addCurve(QwtPlotCurvePieChart(self), QColor(), QColor(), 0, style = QwtCurve.UserCurve, symbol = QwtSymbol.None)
					for classVal in classValuesSorted:
						val = classValues.index(classVal)
						out += [out[-1] + float(distribution[val])/float(tempSum)]
						tooltipText += "<br>%s : <b>%d</b> (%.2f%%)" % (classVal, distribution[val], 100.0*distribution[val]/float(tempSum))
					self.setCurveData(key, [i, j] + [0]*(len(out)-2), out)
					self.curve(key).percentOfTotalData = float(tempSum) / float(sum)
					self.tooltipData.append((tooltipText, i, j))

		# show normal scatterplot with dots
		else:
			# show quality of knn model with only 2 selected attributes
			if self.showKNNModel == 1:
				# variables and domain for the table
				classValueIndices = getVariableValueIndices(self.rawdata, self.rawdata.domain.classVar.name)
				shortData = self.rawdata.select([self.rawdata.domain[xAttr], self.rawdata.domain[yAttr], self.rawdata.domain.classVar])
				shortData = orange.Preprocessor_dropMissing(shortData)
				kNNValues = self.kNNOptimization.kNNClassifyData(shortData)
				bwColors = ColorPaletteBW(-1, 55, 255)
				if self.rawdata.domain.classVar.varType == orange.VarTypes.Continuous:  classColors = ColorPaletteHSV(-1)
				else:																   classColors = ColorPaletteHSV(len(classValueIndices))
				if self.showCorrect == 1: kNNValues = [1.0 - val for val in kNNValues]
				qualityMeasure = self.kNNOptimization.getQualityMeasureStr()

				for j in range(len(kNNValues)):
					fillColor = bwColors.getColor(kNNValues[j])
					edgeColor = classColors.getColor(classValueIndices[shortData[j].getclass().value])
					x=0; y=0
					if discreteX == 1: x = attrXIndices[shortData[j][0].value] + self.rndCorrection(float(self.jitterSize * xVar) / 100.0)
					else:			  x = shortData[j][0].value + self.jitterContinuous * self.rndCorrection(float(self.jitterSize * xVar) / 100.0)
					if discreteY == 1: y = attrYIndices[shortData[j][1].value] + self.rndCorrection(float(self.jitterSize * yVar) / 100.0)
					else:			  y = shortData[j][1].value + self.jitterContinuous * self.rndCorrection(float(self.jitterSize * yVar) / 100.0)
					key = self.addCurve(str(j), fillColor, edgeColor, self.pointWidth, xData = [x], yData = [y])

					# we add a tooltip for this point
					text= self.getShortExampleText(self.rawdata, self.rawdata[j], toolTipList)
					self.addTip(x,y,xVar,yVar, toolTipList, self.rawdata[j], text + "; " + qualityMeasure + " : " + "%.2f"%(kNNValues[j]))

			# create a small number of curves which will make drawing much faster
			elif self.optimizedDrawing and (colorIndex == -1 or self.rawdata.domain[colorIndex].varType == orange.VarTypes.Discrete) and shapeIndex == -1 and sizeShapeIndex == -1:
				if colorIndex != -1:
					classIndices = getVariableValueIndices(self.rawdata, colorAttr)
					classCount = len(classIndices)
					classColors = ColorPaletteHSV(classCount)
				else: classCount = 1
					
				pos = [[ [] , [], [] ] for i in range(classCount)]
				for i in range(len(self.rawdata)):
					if self.rawdata[i][xAttr].isSpecial() == 1: continue
					if self.rawdata[i][yAttr].isSpecial() == 1: continue
					if colorIndex != -1 and self.rawdata[i][colorIndex].isSpecial() == 1: continue

					if discreteX == 1: x = attrXIndices[self.rawdata[i][xAttr].value] + self.rndCorrection(float(self.jitterSize * xVar) / 100.0)
					else:			  x = self.rawdata[i][xAttr].value + self.jitterContinuous * self.rndCorrection(float(self.jitterSize * xVar) / 100.0)

					if discreteY == 1: y = attrYIndices[self.rawdata[i][yAttr].value] + self.rndCorrection(float(self.jitterSize * yVar) / 100.0)
					else:			  y = self.rawdata[i][yAttr].value + self.jitterContinuous * self.rndCorrection(float(self.jitterSize * yVar) / 100.0)

					if colorIndex != -1: index = classIndices[self.rawdata[i].getclass().value]
					else: index = 0
					pos[index][0].append(x)
					pos[index][1].append(y)
					pos[index][2].append(i)

					# we add a tooltip for this point
					self.addTip(x, y, xVar, yVar, toolTipList, self.rawdata[i])
				
				for i in range(classCount):
					newColor = QColor(0,0,0)
					if colorIndex != -1: newColor = classColors.getColor(i)
					key = self.addCurve(str(i), newColor, newColor, self.pointWidth, symbol = self.curveSymbols[0], xData = pos[i][0], yData = pos[i][1])

			# slow, unoptimized drawing because we use different symbols and/or different sizes of symbols
			else:
				if colorIndex != -1 and self.rawdata.domain[colorIndex].varType == orange.VarTypes.Continuous:  classColors = ColorPaletteHSV(-1)
				elif colorIndex != -1:																		  classColors = ColorPaletteHSV(len(self.rawdata.domain[colorIndex].values))

				for i in range(len(self.rawdata)):
					if self.rawdata[i][xAttr].isSpecial() == 1: continue
					if self.rawdata[i][yAttr].isSpecial() == 1: continue
					if colorIndex != -1 and self.rawdata[i][colorIndex].isSpecial() == 1: continue
					if shapeIndex != -1 and self.rawdata[i][shapeIndex].isSpecial() == 1: continue
					if sizeShapeIndex != -1 and self.rawdata[i][sizeShapeIndex].isSpecial() == 1: continue
					
					if discreteX == 1: x = attrXIndices[self.rawdata[i][xAttr].value] + self.rndCorrection(float(self.jitterSize * xVar) / 100.0)
					else:			  x = self.rawdata[i][xAttr].value + self.jitterContinuous * self.rndCorrection(float(self.jitterSize * xVar) / 100.0)

					if discreteY == 1: y = attrYIndices[self.rawdata[i][yAttr].value] + self.rndCorrection(float(self.jitterSize * yVar) / 100.0)
					else:			  y = self.rawdata[i][yAttr].value + self.jitterContinuous * self.rndCorrection(float(self.jitterSize * yVar) / 100.0)

					newColor = QColor(0,0,0)
					if colorIndex != -1: newColor.setHsv(self.coloringScaledData[colorIndex][i], 255, 255)
						
					Symbol = self.curveSymbols[0]
					if shapeIndex != -1: Symbol = self.curveSymbols[shapeIndices[self.rawdata[i][shapeIndex].value]]

					size = self.pointWidth
					if sizeShapeIndex != -1: size = MIN_SHAPE_SIZE + round(self.noJitteringScaledData[sizeShapeIndex][i] * MAX_SHAPE_DIFF)

					self.addCurve(str(i), newColor, newColor, size, symbol = Symbol, xData = [x], yData = [y])

					# we add a tooltip for this point
					self.addTip(x, y, xVar, yVar, toolTipList, self.rawdata[i])

				

		# show legend if necessary
		if self.enabledLegend == 1:
			legendKeys = {}
			if colorIndex != -1 and self.rawdata.domain[colorIndex].varType == orange.VarTypes.Discrete:
				num = len(self.rawdata.domain[colorIndex].values)
				val = [[], [], [self.pointWidth]*num, [QwtSymbol.Ellipse]*num]
				varValues = getVariableValuesSorted(self.rawdata, colorIndex)
				colors = ColorPaletteHSV(num)
				for ind in range(num):
					val[0].append(self.rawdata.domain[colorIndex].name + "=" + varValues[ind])
					val[1].append(colors.getColor(ind))
				legendKeys[colorIndex] = val

			if shapeIndex != -1 and self.rawdata.domain[shapeIndex].varType == orange.VarTypes.Discrete:
				num = len(self.rawdata.domain[shapeIndex].values)
				if legendKeys.has_key(shapeIndex):  val = legendKeys[shapeIndex]
				else:							   val = [[], [QColor(0,0,0)]*num, [self.pointWidth]*num, []]
				varValues = getVariableValuesSorted(self.rawdata, shapeIndex)
				val[3] = []; val[0] = []
				for ind in range(num):
					val[3].append(self.curveSymbols[ind])
					val[0].append(self.rawdata.domain[shapeIndex].name + "=" + varValues[ind])
				legendKeys[shapeIndex] = val

			if sizeShapeIndex != -1 and self.rawdata.domain[sizeShapeIndex].varType == orange.VarTypes.Discrete:
				num = len(self.rawdata.domain[sizeShapeIndex ].values)
				if legendKeys.has_key(sizeShapeIndex):  val = legendKeys[sizeShapeIndex]
				else:							   val = [[], [QColor(0,0,0)]*num, [], [QwtSymbol.Ellipse]*num]
				val[2] = []; val[0] = []
				varValues = getVariableValuesSorted(self.rawdata, sizeShapeIndex)
				for ind in range(num):
					val[0].append(self.rawdata.domain[sizeShapeIndex].name + "=" + varValues[ind])
					val[2].append(MIN_SHAPE_SIZE + round(ind*MAX_SHAPE_DIFF/len(varValues)))
				legendKeys[sizeShapeIndex] = val

			for key in legendKeys.keys()  :
				val = legendKeys[key]
				for i in range(len(val[1])):
					self.addCurve(val[0][i], val[1][i], val[1][i], val[2][i], symbol = val[3][i], enableLegend = 1)
			

		# draw color scale for continuous coloring attribute
		if colorAttr != "" and colorAttr != "(One color)" and showColorLegend == 1 and self.showDistributions == 0 and self.rawdata.domain[colorAttr].varType == orange.VarTypes.Continuous:
			x0 = xVarMax + xVar/100
			x1 = x0 + xVar/20
			colors = ColorPaletteHSV()
			for i in range(1000):
				y = yVarMin + i*yVar/1000
				newCurveKey = self.insertCurve(str(i))
				self.setCurvePen(newCurveKey, QPen(colors.getColor(float(i)/1000.0)))
				self.setCurveData(newCurveKey, [x0,x1], [y,y])

			# add markers for min and max value of color attribute
			(colorVarMin, colorVarMax) = self.attrValues[colorAttr]
			self.addMarker("%s = %.3f" % (colorAttr, colorVarMin), x1 + xVar/50, yVarMin + yVar*0.04, Qt.AlignRight)
			self.addMarker("%s = %.3f" % (colorAttr, colorVarMax), x1 + xVar/50, yVarMin + yVar*0.96, Qt.AlignRight)

		
		self.addTooltips()

	# -----------------------------------------------------------
	# -----------------------------------------------------------
	def addTip(self, x, y, xVar, yVar, toolTipList, dataitem, text = None):
		r = QRectFloat(x-xVar/150.0, y-yVar/150.0, xVar/75.0, yVar/75.0)
		if not text: text= self.getShortExampleText(self.rawdata, dataitem, toolTipList)
		self.tips.addToolTip(r, text)


	# compute how good is a specific projection with given xAttr and yAttr
	def getProjectionQuality(self, xAttr, yAttr, className):
		xArray = self.noJitteringScaledData[self.attributeNames.index(xAttr)]
		yArray = self.noJitteringScaledData[self.attributeNames.index(yAttr)]

		xVar = orange.FloatVariable("xVar")
		yVar = orange.FloatVariable("yVar")
		domain = orange.Domain([xVar, yVar, self.rawdata.domain.classVar])
		table = orange.ExampleTable(domain)
				 
		for i in range(len(self.rawdata)):
			if xArray[i] == "?" or yArray[i] == "?": continue
			example = orange.Example(domain, [xArray[i], yArray[i], self.rawdata[i].getclass()])
			table.append(example)
		accuracy = self.kNNOptimization.kNNComputeAccuracy(table)
		print "kNeighbours = %3.d - Accuracy: %2.2f" % (self.kNNOptimization.kValue, accuracy)
		return accuracy


	# ####################################
	# create x-y projection of attributes in attrList
	def createProjection(self, xAttr, yAttr):
		xIsDiscrete = (self.rawdata.domain[xAttr].varType == orange.VarTypes.Discrete)
		yIsDiscrete = (self.rawdata.domain[yAttr].varType == orange.VarTypes.Discrete)
		if xIsDiscrete:
			xVar = len(self.rawdata.domain[xAttr].values)
		if yIsDiscrete:
			yVar = len(self.rawdata.domain[yAttr].values)
		xAttrIndex = self.attributeNames.index(xAttr)
		yAttrIndex = self.attributeNames.index(yAttr)

		xData = self.noJitteringScaledData[xAttrIndex]
		yData = self.noJitteringScaledData[yAttrIndex]

		xArray = []; yArray = []
		for i in range(len(self.rawdata)):
			if xData[i] == "?" or yData[i] == "?": xArray.append("?"); yArray.append("?"); continue

			if xIsDiscrete: xArray.append(xVar * xData[i])
			else:		   xArray.append(self.rawdata[i][xAttrIndex].value)
			if yIsDiscrete: yArray.append(yVar * xData[i])
			else:		   yArray.append(self.rawdata[i][yAttrIndex].value)
						   
		return (xArray, yArray)

	# ####################################
	# send 2 example tables. in first is the data that is inside selected rects (polygons), in the second is unselected data
	def getSelectionsAsExampleTables(self, xAttr, yAttr):
		if not self.rawdata: return (None, None, None)
		selected = orange.ExampleTable(self.rawdata.domain)
		unselected = orange.ExampleTable(self.rawdata.domain)

		(xArray, yArray) = self.createProjection(xAttr, yAttr)
				 
		for i in range(len(self.rawdata)):
			if xArray[i] == "?": continue
			
			if self.isPointSelected(xArray[i], yArray[i]): selected.append(self.rawdata[i])
			else:										  unselected.append(self.rawdata[i])
		if len(selected) == 0: selected = None
		if len(unselected) == 0: unselected = None
		merged = self.changeClassAttr(selected, unselected)
		return (selected, unselected, merged)
		
	def getOptimalSeparation(self, attrCount, className, addResultFunct = None):
		# define lenghts and variables
		dataSize = len(self.rawdata)
		attrCount = len(self.rawdata.domain.attributes)

		fullList = []
		testIndex = 0
		totalTestCount = attrCount * (attrCount-1) / 2
		print "---------------------"
		print "Total number of possible projections: ", str(totalTestCount)

		t = time.time()

		# create a dataset with scaled data
		fullData = orange.ExampleTable(self.rawdata.domain)
		for i in range(dataSize):
			fullData.append([self.noJitteringScaledData[ind][i] for ind in range(attrCount)] + [self.rawdata[i][className]])

		for x in range(attrCount):
			for y in range(x+1, attrCount):
				testIndex += 1
				self.scatterWidget.progressBarSet(100.0*testIndex/float(totalTestCount))
				
				table = fullData.select([x,y, className])
				table = orange.Preprocessor_dropMissing(table)
				if len(table) < self.kNNOptimization.minExamples: print "possibility %6d / %d. Not enough examples (%d)" % (testIndex, totalTestCount, len(table)); continue

				accuracy = self.kNNOptimization.kNNComputeAccuracy(table)
				if table.domain.classVar.varType == orange.VarTypes.Discrete:
					print "permutation %6d / %d. Accuracy: %2.2f%%" % (testIndex, totalTestCount, accuracy)
				else:
					print "permutation %6d / %d. MSE: %2.2f" % (testIndex, totalTestCount, accuracy) 

				# save the permutation
				fullList.append((accuracy, len(table), [self.attributeNames[x], self.attributeNames[y]]))
				if addResultFunct: addResultFunct(self.rawdata, accuracy, len(table), [self.attributeNames[x], self.attributeNames[y]])

		print "------------------------------"
		secs = time.time() - t
		print "Used time: %d min, %d sec" %(secs/60, secs%60)

		return fullList


	def addTooltips(self):
		for (text, i, j) in self.tooltipData:
			x_1 = self.transform(QwtPlot.xBottom, i-0.5)
			x_2 = self.transform(QwtPlot.xBottom, i+0.5)
			y_1 = self.transform(QwtPlot.yLeft, j+0.5)
			y_2 = self.transform(QwtPlot.yLeft, j-0.5)
			rect = QRect(x_1, y_1, x_2-x_1, y_2-y_1)
			self.toolRects.append(rect)			
			QToolTip.add(self, rect, text)
			

	def removeTooltips(self):
		for rect in self.toolRects:
			QToolTip.remove(self, rect)
		self.toolRects = []

	def updateLayout(self):
		OWVisGraph.updateLayout(self)
		self.removeTooltips()
		self.addTooltips()

	def onMouseReleased(self, e):
		OWVisGraph.onMouseReleased(self, e)
		self.updateLayout()

		
if __name__== "__main__":
	#Draw a simple graph
	a = QApplication(sys.argv)		
	c = OWScatterPlotGraph(None)
		
	a.setMainWidget(c)
	c.show()
	a.exec_loop()
