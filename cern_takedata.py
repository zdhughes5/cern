import target_driver
import target_io
import time
import subprocess
import sys
import cern_extract
import matplotlib.pyplot as plt

garbage, initialize = sys.argv

#trigenable = 0b10000000000000000 #external
trigenable = 0b01111111111111111 #group 0

#trigger direction (1=hardsync, 0=external)
trigdir = 1

valThresh = 2380
valVped = 1200
valWbias = 985
valPMTref4 = 2000
valDeadtime = 250
valDuration = 10
valNBlocks = 14
valFilename = 'file_r0.tio'
valShowPlot = False
valTrigDelay = 485

defdir = "/home/pi/TargetC/TargetSuite/share/TargetDriver/config"
my_ip = "192.168.0.1"
board_ip = "192.168.0.123"
board_def = defdir+"/TC_EB_FPGA_Firmware0xFEDA001C.def"
asic_def = defdir+"/TC_ASIC.def"
trigger_asic_def = defdir+"/T5TEA_ASIC.def"


board = target_driver.TargetModule(board_def, asic_def, trigger_asic_def, 0)
if initialize == 'True':
    board.EstablishSlowControlLink(my_ip, board_ip)
    board.Initialise()
    board.EnableDLLFeedback()
    #board.WriteSetting("SetDataPort", 8107)
    #board.WriteSetting("SetSlowControlPort", 8201)
elif initialize == 'False':
    board.ReconnectToServer(my_ip, 8201, board_ip, 8105)
else:
    sys.exit("Did not understand initialize parameter: "+initialize+". It should be 'True' or 'False'")

command = None

while command != 'x':
    
    print('__________________________________________________________________________________________')
    print('__________________________________________________________________________________________')
    print('t: Set Thresh       v: Set Vped          w: Set Wbias')
    print('p: Set PMTref4      d: Set deadtime      c: Set Capture Time')
    print('n: Set nblocks      l: Set Trig Delay    f: Set filename')
    print('s: Show Plot        e: Echo params       r: Begin Capture       ')
    print('q: Begin Acq.       x: Exit')
    print('\n')
    
    command = input('Enter Command: ')
    print('')
    
    if command == 't':
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
        board = target_driver.TargetModule(board_def, asic_def, trigger_asic_def, 0)
        board.ReconnectToServer(my_ip, 8201, board_ip, 8105)

        subprocess.call('rm ' + valFilename + ' ' + valFilename.split('_')[0]+'_r1.tio', shell = True)
        
        #Set Vped
        for channel in range(16):
            board.WriteTriggerASICSetting("Vped_{}".format(channel),0, valVped, True)

        for group in range(4):
            board.WriteTriggerASICSetting("PMTref4_{}".format(group), 0, valPMTref4, True) 
            board.WriteTriggerASICSetting("Thresh_{}".format(group), 0, valThresh, True)
            board.WriteTriggerASICSetting("Wbias_{}".format(group), 0, valWbias, True)
        
        board.WriteSetting("TriggerDelay", valTrigDelay)
        board.WriteSetting("TACK_TriggerType", 0x0)
        board.WriteSetting("TACK_TriggerMode", 0x0)
        
        #disable trigger at beginning
        board.WriteSetting("TACK_EnableTrigger", 0)
        
        #Enable all 16 channels and enable zero supression. Zero suppression needs to be always on. Suppresses disabled channels (in eval board case 16-63).
        board.WriteSetting("EnableChannelsASIC0", 0xFFFF)				
        board.WriteSetting("Zero_Enable", 0x1)
        
        #Enable done bit i(if enabled, undefined timing between ramps)
        board.WriteSetting("DoneSignalSpeedUp", 1);
        
        board.WriteSetting("NumberOfBlocks", valNBlocks-1)
        
        #deadtime settings
        #Dead time after trigger in x8ns
        deadtimenano=int(valDeadtime*1000/8)
        if (deadtimenano > 0xFFFF):
            print("deadtime to large!")
            exit()
        board.WriteSetting("DurationofDeadtime", deadtimenano)
        
        #disable triggers while serial readout of TC (needed for internal trigger due to bad layout)
        board.WriteSetting("SR_DisableTrigger", 1)
        board.WriteSetting("ExtTriggerDirection", trigdir) 
        
        #number of packets/events. 16 means one channel/packet
        kNPacketsPerEvent = 16 #reading only one channel
        
        #you can read it on wireshark, also a function is availiable to calculate this from nblocks and channels/packet
        kPacketSize = 278
        
        #Event buffer in PC memory
        kBufferDepth = 10000
        
        #start data listener
        listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
        listener.AddDAQListener(my_ip)
        listener.StartListening()
        
        #start writer
        writer = target_io.EventFileWriter(valFilename, kNPacketsPerEvent, kPacketSize)
        buf = listener.GetEventBuffer()
        writer.StartWatchingBuffer(buf)
        
        
        board.WriteSetting("TACK_EnableTrigger", trigenable)
        
        time.sleep(valDuration)

        writer.StopWatchingBuffer()
        
        board.CloseSockets()
        buf.Flush()
        writer.Close()
        print('Finished Capture.')
        print('Doing calibration...', end = '')
        #subprocess.call('apply_calibration -i ' + valFilename + ' pedestal.tcal', shell = True)
        print('done.')
        
        if valShowPlot == True:
            raw, cal, cmc = cern_extract.extractADCS(valFilename, valFilename.split('_')[0]+'_r1.tio', valNBlocks)
            f, axs = plt.subplots(nrows = 8, ncols = 3)
            axs[0].plot(np.sum(raw, (0,1)), color='black')
            axs[1].plot(np.sum(cal, (0,1)), color='black')
            for channel in range(16):
                axs[channel+3].plot(raw[0, channel, :], color='black', linestyle='--')
                axs[channel+3].plot(cal[0, channel, :], color='black')
            plt.show()
            
        
            
            


    elif command == 'x':
        sys.exit('Got exit command. Exiting.')
    else:
        print('Got unknown command')

    print('')


