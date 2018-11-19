#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 10:29:33 2018

@author: zdhughes
"""

import target_driver
import target_io
import time
import subprocess
import sys
import cern_extract
import matplotlib.pyplot as plt
import numpy as np
import time

garbage, initialize = sys.argv

class mainLoop:
    
	def __init__(self, initialize):
		self.initialize = initialize

		self.valTrigEnable = 0b00000000000000001 #group 0
		self.valTrigDir = 1
		self.valThresh = 2380
		self.valVped = 1200
		self.valWbias = 985
		self.valPMTref4 = 2000
		self.valDeadtime = 250
		self.valDuration = 10
		self.valNBlocks = 14
		self.valTrigDelay = 485
		self.valFilename = 'file_r0.tio'
		self.valShowPlot = False
		self.valNAcquire = 10
	    
		self.defdir = "/home/pi/TargetC/TargetSuite/share/TargetDriver/config"
		self.my_ip = "192.168.0.1"
		self.board_ip = "192.168.0.123"
		self.board_def = self.defdir+"/TC_EB_FPGA_Firmware0xFEDA001C.def"
		self.asic_def = self.defdir+"/TC_ASIC.def"
		self.trigger_asic_def = self.defdir+"/T5TEA_ASIC.def"


		self.board = target_driver.TargetModule(self.board_def, self.asic_def, self.trigger_asic_def, 0)
		if self.initialize == 'True':
			self.board.EstablishSlowControlLink(self.my_ip, self.board_ip)
			self.board.Initialise()
			self.board.EnableDLLFeedback()
		elif self.initialize == 'False':
			self.board.ReconnectToServer(self.my_ip, 8201, self.board_ip, 8105)
		else:
			sys.exit("Did not understand initialize parameter: "+self.initialize+". It should be 'True' or 'False'")
		self. command = None
		
		self.mainloop()
		
		
		def mainloop(self):

			while self.command != 'x':
	
				print('__________________________________________________________________________________________')
				print('__________________________________________________________________________________________')
				print('g: Set Trig. Enable        y: Set Trig. Dir.        t: Set Thresh')
				print('v: Set Vped                w: Set Wbias             p: Set PMTref4')
				print('d: Set deadtime            c: Set Capture Time      n: Set nblocks')
				print('l: Set Trig Delay          f: Set filename          s: Show Plot')
				print('o: Seet Acquire Repeat')
				print('e: Echo params             r: Begin Capture         q: Begin Acq.')
				print('x: Exit')
				print('\n')
	
				command = input('Enter Command: ')
				print('')

				if command == 'g':
					self.valTrigEnable = int(input('Enter valTrigEnable: '))
				elif command == 'y':
					self.valTrigDir = int(input('Enter valTrigDir: '))
				elif command == 't':
					valThresh = int(input('Enter valThresh: '))
				elif command == 'v':
					valVped = int(input('Enter valVped: '))
				elif command == 'w':
					valWbias = int(input('Enter valWbias: '))
				elif command == 'p':
					valPMTref4 = int(input('Enter valPMTref4: '))
				elif command == 'd':
					valDeadtime = int(input('Enter valDeadtime: '))
				elif command == 'c':
					valDuration = int(input('Enter valDuration: '))
				elif command == 'n':
					valNBlocks = int(input('Enter valNBlocks: '))
				elif command == 'l':
					valTrigDelay = int(input('Enter valTrigDelay: '))
				elif command == 'f':
					valFilename = input('Enter valFilename: ')
				elif command == 's':
					valShowPlot = input('Enter valShowPlot [True/False]: ')
				elif command == 'e':
					print('valThresh: '+str(valThresh))
					print('valVped: '+str(valVped))
					print('valWbias: '+str(valWbias))
					print('valPMTref4: '+str(valPMTref4))
					print('valDeadtime: '+str(valDeadtime))
					print('valDuration: '+str(valDuration))
					print('valNBlocks: '+str(valNBlocks))
					print('valTrigDelay: '+str(valTrigDelay))
					print('valFilename: '+str(valFilename))
					print('valShowPlot: '+str(valShowPlot))
	
				elif command == 'r':
					self.acquire(self.valFilename)
				elif command == 'q':
					fileStem = '_'.join(self.valFilename.split('_')[:-1])
					
					for i in range(self.valNAcquire):
						start = time.time()
						self.acquire(fileStem+'_'+str(i)+'_r0.fits')
						end = time.time()
						elapsed = end - start
						time.sleep((elapsed//60)*60 - elapsed)
	
				elif command == 'x':
					sys.exit('Got exit command. Exiting.')
				else:
					print('Got unknown command')
				print('')
				
	def acquire(self, filename):
		self.board = target_driver.TargetModule(self.board_def, self.asic_def, self.trigger_asic_def, 0)
		self.board.ReconnectToServer(self.my_ip, 8201, self.board_ip, 8105)

		subprocess.call('rm ' + filename + ' ' + '_'.join(filename.split('_')[:-1])+'_r1.tio', shell = True)

		#Set Vped
		for channel in range(16):
			self.board.WriteTriggerASICSetting("Vped_{}".format(channel),0, self.valVped, True)

		for group in range(4):
			self.board.WriteTriggerASICSetting("PMTref4_{}".format(group), 0, self.valPMTref4, True) 
			self.board.WriteTriggerASICSetting("Thresh_{}".format(group), 0, self.valThresh, True)
			self.board.WriteTriggerASICSetting("Wbias_{}".format(group), 0, self.valWbias, True)

		self.board.WriteSetting("TriggerDelay", self.valTrigDelay)
		self.board.WriteSetting("TACK_TriggerType", 0x0)
		self.board.WriteSetting("TACK_TriggerMode", 0x0)

		#disable trigger at beginning
		self.board.WriteSetting("TACK_EnableTrigger", 0)

		#Enable all 16 channels and enable zero supression. Zero suppression needs to be always on. Suppresses disabled channels (in eval board case 16-63).
		self.board.WriteSetting("EnableChannelsASIC0", 0xFFFF)				
		self.board.WriteSetting("Zero_Enable", 0x1)

		#Enable done bit i(if enabled, undefined timing between ramps)
		self.board.WriteSetting("DoneSignalSpeedUp", 1);

		self.board.WriteSetting("NumberOfBlocks", valNBlocks-1)

		#deadtime settings
		#Dead time after trigger in x8ns
		deadtimenano = int(self.valDeadtime*1000/8)
		if (deadtimenano > 0xFFFF):
			print("deadtime to large!")
			exit()
		self.board.WriteSetting("DurationofDeadtime", deadtimenano)

		#disable triggers while serial readout of TC (needed for internal trigger due to bad layout)
		self.board.WriteSetting("SR_DisableTrigger", 1)
		self.board.WriteSetting("ExtTriggerDirection", self.trigdir) 

		#number of packets/events. 16 means one channel/packet
		kNPacketsPerEvent = 16 #reading only one channel

		#you can read it on wireshark, also a function is availiable to calculate this from nblocks and channels/packet
		kPacketSize = 278

		#Event buffer in PC memory
		kBufferDepth = 10000

		#start data listener
		listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
		listener.AddDAQListener(self.my_ip)
		listener.StartListening()

		#start writer
		writer = target_io.EventFileWriter(filename, kNPacketsPerEvent, kPacketSize)
		buf = listener.GetEventBuffer()
		writer.StartWatchingBuffer(buf)

		self.board.WriteSetting("TACK_EnableTrigger", self.trigenable)

		time.sleep(self.valDuration)

		writer.StopWatchingBuffer()

		self.board.CloseSockets()
		buf.Flush()
		writer.Close()
		print('Finished Capture.')
		print('Doing calibration...', end = '')
		#subprocess.call('apply_calibration -i ' + valFilename + ' pedestal.tcal', shell = True)
		print('done.')

		if self.valShowPlot == True:
			raw, cal, cmc = cern_extract.extractADCS(filename, '_'.join(filename.split('_')[:-1])+'_r1.tio', valNBlocks)
			f, axs = plt.subplots(nrows = 8, ncols = 3)
			axs[0].plot(np.sum(raw, (0,1)), color='black')
			axs[1].plot(np.sum(cal, (0,1)), color='black')
			for channel in range(16):
				axs[channel+3].plot(raw[0, channel, :], color='black', linestyle='--')
				axs[channel+3].plot(cal[0, channel, :], color='black')
			plt.show()


