#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 09:56:18 2018

@author: zdhughes
"""

import target_io
import target_driver
import numpy as np

def extractADCS(filename_raw, filename_cal, nBlocks):
    
    nChannels = 16
    channels = list(range(16))
    nSamples = nBlocks*32
    SCALE=13.6
    OFFSET=700
    
    reader_raw = target_io.EventFileReader(filename_raw)
    reader_cal = target_io.EventFileReader(filename_cal)
    nEvents  = reader_cal.GetNEvents()
    
    print(nEvents, "events read")
    timestamp = 0
    
    ampl_raw = np.zeros([nEvents, nChannels, nSamples])
    ampl_cal = np.zeros([nEvents, nChannels, nSamples])
    ampl_cmc = np.zeros([nEvents, nChannels, nSamples])
    
    for this_event in range(1, nEvents):
                
        for this_channel in channels:
    
            if (this_event % 1000 == 0):
                print("Event {} of {} of channel {}".format(this_event, nEvents, this_channel))
                
            event_header = target_driver.EventHeader()
            rv = reader_cal.GetEventHeader(this_event, event_header)
            
            #get timestamp in ns from event header
            timestamp = event_header.GetTACK()
            
            #print("Event ",ievt, " Timestamp in ns",timestamp, " Time since last Event in us ",(timestamp-timestamp_prev)/1000.)
            #first get the right packet from event, if only one channel/packet, then packetnumber = channel
            
            rawdata_raw = reader_raw.GetEventPacket(this_event, this_channel)
            rawdata_cal = reader_cal.GetEventPacket(this_event, this_channel)
            packet_raw = target_driver.DataPacket()
            packet_cal = target_driver.DataPacket()
            packet_raw.Assign(rawdata_raw, reader_raw.GetPacketSize())
            packet_cal.Assign(rawdata_cal, reader_cal.GetPacketSize())
            
            #get the waveform, if only one channel/packet, only one waveform!
            wf_raw = packet_raw.GetWaveform(this_channel)
            wf_cal = packet_cal.GetWaveform(this_channel)
    
            raw_adc = np.zeros(nSamples, dtype = np.float)
            cal_adc = np.zeros(nSamples, dtype = np.float)
            raw_adc = wf_raw.GetADC16bitArray(nSamples)
            cal_adc = wf_cal.GetADC16bitArray(nSamples)
            
            ampl_raw[this_event, this_channel, :] = raw_adc[:]
            ampl_cal[this_event, this_channel, :] = (cal_adc[:]/SCALE) - OFFSET
    
            #common mode correction
            for this_notChannel in [x for x in channels if x != this_channel]:
                
                wf_cmc = packet_cal.GetWaveform(this_notChannel)
                #dircetly access the full array (faster)
                adc = np.zeros(nSamples, dtype=np.float)
                adc = wf_cmc.GetADC16bitArray(nSamples)
                ampl_cmc[this_event, this_channel, :] = ampl_cmc[this_event, this_channel, :]+ (((adc/SCALE)-OFFSET)*1/10)
                
                
    return (ampl_raw, ampl_cal, ampl_cmc)
    