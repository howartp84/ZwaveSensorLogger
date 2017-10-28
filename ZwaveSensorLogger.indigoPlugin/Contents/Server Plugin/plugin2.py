#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2016, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

#Thanks to Krisstian for teaching me how to join() and use xrange() in one-liner commands!

import indigo

import os
import sys

import fnmatch

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

########################################
# Tiny function to convert a list of integers (bytes in this case) to a
# hexidecimal string for pretty logging.
def convertListToHexStr(byteList):
	return ' '.join(["%02X" % byte for byte in byteList])

def convertListToStr(byteList):
	return ' '.join(["%02X" % byte for byte in byteList])

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = pluginPrefs.get("showDebugInfo", True)

		self.powerIDs = list()
		self.tempIDs = list()

		self.zedFromDev = dict()
		self.zedFromNode = dict()
		self.devFromZed = dict()
		self.devFromNode = dict()
		self.nodeFromZed = dict()
		self.nodeFromDev = dict()

	########################################
	def startup(self):
		self.debugLog(u"startup called")
		indigo.zwave.subscribeToIncoming()
		#indigo.zwave.subscribeToOutgoing()

	def shutdown(self):
		self.debugLog(u"shutdown called")

	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		# Since the dialog closed we want to set the debug flag - if you don't directly use
		# a plugin's properties (and for debugLog we don't) you'll want to translate it to
		# the appropriate stuff here.
		if not userCancelled:
			self.debug = valuesDict.get("showDebugInfo", False)
			if self.debug:
				indigo.server.log("Debug logging enabled")
			else:
				indigo.server.log("Debug logging disabled")

	def deviceStartComm(self, dev):
		dev.stateListOrDisplayStateIdChanged()
		if (dev.deviceTypeId == "zpower"):
			devID = dev.id																							#devID is the Indigo ID of my dummy device
			zedID = dev.ownerProps['deviceId']													#zedID is the Indigo ID of the actual ZWave device
			nodeID = indigo.devices[int(zedID)].ownerProps['address']		#nodeID is the ZWave Node ID

			self.zedFromDev[int(devID)] = int(zedID)
			self.zedFromNode[int(nodeID)] = int(zedID)
			self.devFromZed[int(zedID)] = int(devID)
			self.devFromNode[int(nodeID)] = int(devID)
			self.nodeFromZed[int(zedID)] = int(nodeID)
			self.nodeFromDev[int(devID)] = int(nodeID)

			self.powerIDs.append(nodeID)

		if (dev.deviceTypeId == "ztemp"):
			devID = dev.id																							#devID is the Indigo ID of my dummy device
			zedID = dev.ownerProps['deviceId']													#zedID is the Indigo ID of the actual ZWave device
			nodeID = indigo.devices[int(zedID)].ownerProps['address']		#nodeID is the ZWave Node ID

			self.zedFromDev[int(devID)] = int(zedID)
			self.zedFromNode[int(nodeID)] = int(zedID)
			self.devFromZed[int(zedID)] = int(devID)
			self.devFromNode[int(nodeID)] = int(devID)
			self.nodeFromZed[int(zedID)] = int(nodeID)
			self.nodeFromDev[int(devID)] = int(nodeID)

			self.tempIDs.append(nodeID)

	def deviceStopComm(self, dev):
		if (dev.deviceTypeId == "zpower"):
			devID = dev.id
			zedID = dev.ownerProps['deviceId']
			nodeID = indigo.devices[int(zedID)].ownerProps['address']

			self.zedFromDev.pop(int(devID),None)
			self.zedFromNode.pop(int(nodeID),None)
			self.devFromZed.pop(int(zedID),None)
			self.devFromNode.pop(int(nodeID),None)
			self.nodeFromZed.pop(int(zedID),None)
			self.nodeFromDev.pop(int(devID),None)

			self.powerIDs.remove(nodeID)

		if (dev.deviceTypeId == "ztemp"):
			devID = dev.id
			zedID = dev.ownerProps['deviceId']
			nodeID = indigo.devices[int(zedID)].ownerProps['address']

			self.zedFromDev.pop(int(devID),None)
			self.zedFromNode.pop(int(nodeID),None)
			self.devFromZed.pop(int(zedID),None)
			self.devFromNode.pop(int(nodeID),None)
			self.nodeFromZed.pop(int(zedID),None)
			self.nodeFromDev.pop(int(devID),None)

			self.tempIDs.remove(nodeID)



########################################
	def zwaveCommandReceived(self, cmd):
		byteList = cmd['bytes']			# List of the raw bytes just received.
		byteListStr = convertListToHexStr(byteList)
		nodeId = cmd['nodeId']			# Can be None!
		endpoint = cmd['endpoint']		# Often will be None!

		bytes = byteListStr.split()
		nodeId = int(bytes[5],16)

		if (int(bytes[5],16)) in self.powerIDs: #Power Devices
			#self.debugLog(u"Raw command received (Node %s): %s" % ((int(bytes[5],16)),(byteListStr)))

			#socketMap = {1:3, 2:4, 3:5, 4:6, 5:1, 6:2} #socketMap[endPoint] = SocketNo
			socketMap = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6} #socketMap[endPoint] = SocketNo

			dev=indigo.devices[self.devFromNode[nodeId]]

			if (bytes[7] == "32") and (bytes[8] == "02") and (bytes[10] == "74"): #ENERGY REPORT (Base Device)
				self.debugLog(u"-----")
				self.debugLog(u"Energy report received:")
				self.debugLog(u"Raw command: %s" % (byteListStr))
				#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
				self.debugLog(u"Endpoint:  Total")
				#self.debugLog(u"Format:    %s" % (bytes[10]))
				stateid = "totalpowerrep"
				self.debugLog(u"State:     %s" % (stateid))
				if (bytes[10] == "74"): #3DP, Watts, 4bytes
					fullpower = int(bytes[11] + bytes[12] + bytes[13] + bytes[14],16)
					decpower = float(fullpower)/1000
					self.debugLog(u"Total Power Reported: " + str(fullpower) + " (" + str(decpower) + ") watts")
					dev.updateStateOnServer(stateid, decpower)
				elif (bytes[10] == "34"): #1DP, Watts, 4bytes
					fullpower = int(bytes[11] + bytes[12] + bytes[13] + bytes[14],16)
					decpower = float(fullpower)/10
					self.debugLog(u"Total Power Reported: " + str(fullpower) + " (" + str(decpower) + ") watts")
					dev.updateStateOnServer(stateid, decpower)


			if (bytes[7] == "60") and (bytes[8] == "0D") and (bytes[11] == "32") and (bytes[12] == "02") and (bytes[14] == "74"): #MULTI_CHANNEL ENERGY
				self.debugLog(u"-----")
				self.debugLog(u"Energy report received:")
				self.debugLog(u"Raw command: %s" % (byteListStr))
				#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
				self.debugLog(u"Endpoint:  %s" % (int(bytes[9],16)))
				self.debugLog(u"Socket:    %s" % (socketMap[int(bytes[9],16)]))
				#self.debugLog(u"Format:    %s" % (bytes[14]))
				#self.debugLog(u"Power (w): %s" % (socketMap[int(bytes[9],16)]))
				stateid = "socket" + str(socketMap[int(bytes[9],16)]) + "power"
				self.debugLog(u"State:     %s" % (stateid))

				if (bytes[14] == "74"): #3DP, Watts, 4bytes
					fullpower = int(bytes[15] + bytes[16] + bytes[17] + bytes[18],16)
					decpower = float(fullpower)/1000
					self.debugLog(u"Power: " + str(fullpower) + " (" + str(decpower) + ") watts")
					dev.updateStateOnServer(stateid, decpower)
				elif (bytes[14] == "34"): #1DP, Watts, 4bytes
					fullpower = int(bytes[15] + bytes[16] + bytes[17] + bytes[18],16)
					decpower = float(fullpower)/10
					self.debugLog(u"Power: " + str(fullpower) + " (" + str(decpower) + ") watts")
					dev.updateStateOnServer(stateid, decpower)

				tpower = float(dev.states["socket1power"]) + float(dev.states["socket2power"]) + float(dev.states["socket3power"]) + float(dev.states["socket4power"]) + float(dev.states["socket5power"]) + float(dev.states["socket6power"]) + float(dev.states["socket7power"]) + float(dev.states["socket8power"])
				self.debugLog(u"Total Power Calculated: " + str(tpower) + " watts")
				dev.updateStateOnServer("totalpower",tpower)

		if (int(bytes[5],16)) in self.tempIDs: #Temperature Devices
			#self.debugLog(u"Raw command received (Node %s): %s" % ((int(bytes[5],16)),(byteListStr)))

			socketMap = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6} #socketMap[endPoint] = SocketNo

			dev=indigo.devices[self.devFromNode[nodeId]]

			if (bytes[7] == "31") and (bytes[8] == "05") and (bytes[9] == "05") and (bytes[10] == "42"): #HUMIDITY SENSOR REPORT (Base Device)
				self.debugLog(u"-----")
				self.debugLog(u"Humidity report received:")
				self.debugLog(u"Raw command: %s" % (byteListStr))
				#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
				self.debugLog(u"Endpoint:  Base")
				#self.debugLog(u"Format:    %s" % (bytes[10]))
				stateid = "humidity"
				self.debugLog(u"State:     %s" % (stateid))
				if (bytes[10] == "42"): #2DP, %age, 2bytes
					humid = int(bytes[11] + bytes[12],16)
					dechumid = float(humid)/100
					self.debugLog(u"Humidity Reported: " + str(humid) + " (" + str(dechumid) + ") percent")
					dev.updateStateOnServer(stateid, dechumid)
			elif (bytes[7] == "31") and (bytes[8] == "05") and (bytes[9] == "01") and (bytes[10] == "42"): #TEMPERATURE SENSOR REPORT (Base Device)
				self.debugLog(u"-----")
				self.debugLog(u"Base temperature report received:")
				self.debugLog(u"Raw command: %s" % (byteListStr))
				#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
				self.debugLog(u"Endpoint:  Base")
				stateid = "temp0"
				self.debugLog(u"State:     %s" % (stateid))
				if (bytes[10] == "42"): #2DP, Celsius, 2bytes
					temp = int(bytes[11] + bytes[12],16)
					dectemp = float(temp)/100
					self.debugLog(u"Temperature Reported: " + str(temp) + " (" + str(dectemp) + ") celsius")
					dev.updateStateOnServer(stateid, dectemp)

			if (bytes[7] == "60") and (bytes[8] == "0D") and (bytes[11] == "31") and (bytes[12] == "05"): #MULTI_CHANNEL SENSOR
				self.debugLog(u"-----")
				self.debugLog(u"Endpoint Temperature report received:")
				self.debugLog(u"Raw command: %s" % (byteListStr))
				#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
				self.debugLog(u"Endpoint:  %s" % (int(bytes[9],16)))
				#self.debugLog(u"Device:    %s" % (socketMap[int(bytes[9],16)]))
				#self.debugLog(u"Format:    %s" % (bytes[14]))
				#self.debugLog(u"Power (w): %s" % (socketMap[int(bytes[9],16)]))
				stateid = "temp" + str(socketMap[int(bytes[9],16)])
				self.debugLog(u"State:     %s" % (stateid))
				if (bytes[14] == "42"): #2DP, Celsius, 2bytes
					temp = int(bytes[15] + bytes[16],16)
					dectemp = float(temp)/100
					self.debugLog(u"Temperature Reported: " + str(temp) + " (" + str(dectemp) + ") °c")
					dev.updateStateOnServer(stateid, dectemp)


########################################
	def zwaveCommandSent(self, cmd):
		byteList = cmd['bytes']         # List of the raw bytes just sent.
		byteListStr = convertListToHexStr(byteList)    # this method is defined in the example SDK plugin
		timeDelta = cmd['timeDelta']    # The time duration it took to receive an Z-Wave ACK for the command.
		cmdSuccess = cmd['cmdSuccess']  # True if an ACK was received (or no ACK expected), false if NAK.
		nodeId = cmd['nodeId']          # Can be None!
		endpoint = cmd['endpoint']      # Often will be None!

		bytes = byteListStr.split()

		bytes = byteListStr.split()
		#nodeId = int(bytes[5],16)

		if nodeId:
			if int(nodeId) in self.powerIDs:
				self.debugLog(u"Raw command sent (Node %s): %s (%s)" % (nodeId,byteListStr,cmdSuccess))
			if int(nodeId) in self.tempIDs:
				self.debugLog(u"Raw command sent (Node %s): %s (%s)" % (nodeId,byteListStr,cmdSuccess))


	def getPowerAll(self,pluginAction):
		myDev = pluginAction.deviceId
		node = self.nodeFromDev[int(myDev)]
		self.debugLog("Node: " + str(node))

		codeStr = [0x32, 0x01, 0x10] #32, 01, 10 = Meter_Get, PowerUsed, Wattage

		indigo.server.log("Requesting total power levels for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 1 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=1,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 2 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=2,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 3 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=3,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 4 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=4,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 5 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=5,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 6 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=6,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 7 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=7,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 8 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=8,cmdBytes=codeStr,sendMode=1)

	def resetPower(self,pluginAction):
		myDev = pluginAction.deviceId
		node = self.nodeFromDev[int(myDev)]
		self.debugLog("Node: " + str(node))
		indigo.server.log("Resetting power levels for node " + str(node))

		indigo.devices[myDev].updateStateOnServer("socket1power",0)
		indigo.devices[myDev].updateStateOnServer("socket2power",0)
		indigo.devices[myDev].updateStateOnServer("socket3power",0)
		indigo.devices[myDev].updateStateOnServer("socket4power",0)
		indigo.devices[myDev].updateStateOnServer("socket5power",0)
		indigo.devices[myDev].updateStateOnServer("socket6power",0)
		indigo.devices[myDev].updateStateOnServer("socket7power",0)
		indigo.devices[myDev].updateStateOnServer("socket8power",0)
		indigo.devices[myDev].updateStateOnServer("totalpower",0)
		indigo.devices[myDev].updateStateOnServer("totalpowerrep",0)


	def getTempAll(self,pluginAction):
		myDev = pluginAction.deviceId
		node = self.nodeFromDev[int(myDev)]
		self.debugLog("Node: " + str(node))

		codeStr = [0x31, 0x04, 0x05] #32, 01, 10 = Sensor_Get, Humidity

		indigo.server.log("Requesting humidity for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],cmdBytes=codeStr,sendMode=1)

		codeStr = [0x31, 0x04, 0x01] #32, 01, 10 = Sensor_Get, Temp

		indigo.server.log("Requesting temperature for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting temperature 1 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=1,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting temperature 2 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=2,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting temperature 3 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=3,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting temperature 4 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=4,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting temperature 5 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=5,cmdBytes=codeStr,sendMode=1)
