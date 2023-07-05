import sys, os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import *
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.uic import loadUi
from datetime import datetime
import csv
import time
from string import *
import configparser
from numpy.core.defchararray import *


class Dialog(QDialog):
    def __init__(self):
        super(Dialog, self).__init__()

        self.auto_transmit_slot_no = 0
        self.lost_packet_count = 0
        self.t1 = datetime.now()
        self.t2 = None
        self.delta = None
        self.period = None

        loadUi('Dialog.ui', self)
        self.LookUp = []
        self.load_lookup()
        self.extract_message("40F", "30", "28", "7D", "4E", "00", "00", "00", "00")
        self.bind_controls()
        self.counter = 0
        self.messages = []

        self.leWheelSpeed.setText(str(self.dialWheelSpeed.value()))
        self.leEngineSpeed.setText(str(self.dialEngineSpeed.value()))
        self.leTCO.setText(str(self.dialTCO.value()))
        self.leVehicleSpeed.setText(str(self.dialVehicleSpeed.value()))

        # Connections tab ==============================================================================================
        self.rxSerialPort = None
        self.rxSerialDeviceIsConnected = False
        self.rxBuffer = None

        self.txSerialPort = None
        self.txSerialDeviceIsConnected = False
        self.txBuffer = None

        self.config = configparser.ConfigParser()

        self.init_serial_ports()

        # Bus traffic tab ==============================================================================================
        self.tblRx.setColumnWidth(0, 60)
        self.tblRx.setColumnWidth(1, 20)
        self.tblRx.setColumnWidth(2, 20)
        self.tblRx.setColumnWidth(3, 20)
        self.tblRx.setColumnWidth(4, 20)
        self.tblRx.setColumnWidth(5, 20)
        self.tblRx.setColumnWidth(6, 20)
        self.tblRx.setColumnWidth(7, 20)
        self.tblRx.setColumnWidth(8, 20)
        self.tblRx.setColumnWidth(9, 20)
        self.tblRx.setColumnWidth(10, 100)
        self.tblRx.setColumnWidth(11, 100)
        self.tblRx.setColumnWidth(12, 100)
        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_table)
        self.timer.start()

        self.tmrAutoTransmit = QTimer()
        self.tmrAutoTransmit.setInterval(50)
        self.tmrAutoTransmit.timeout.connect(self.auto_transmit)
        self.tmrAutoTransmit.start()

        # Trace Packets Tab ============================================================================================
        self.blnTraceSlot01 = False
        self.blnTraceSlot02 = False
        self.blnTraceSlot03 = False
        self.blnTraceSlot04 = False
        self.blnTraceSlot05 = False
        self.blnTraceSlot06 = False
        self.blnTraceSlot07 = False
        self.blnTraceSlot08 = False
        self.blnTraceSlot09 = False
        self.blnTraceSlot10 = False
        self.blnTraceSlot11 = False
        self.blnTraceSlot12 = False
        self.blnTraceSlot13 = False
        self.blnTraceSlot14 = False
        self.blnTraceSlot15 = False
        self.blnTraceSlot16 = False
        self.blnTraceSlot17 = False
        self.blnTraceSlot18 = False
        self.blnTraceSlot19 = False
        self.blnTraceSlot20 = False

        self.btnOff01.setEnabled(False)
        self.btnOff02.setEnabled(False)
        self.btnOff03.setEnabled(False)
        self.btnOff04.setEnabled(False)
        self.btnOff05.setEnabled(False)
        self.btnOff06.setEnabled(False)
        self.btnOff07.setEnabled(False)
        self.btnOff08.setEnabled(False)
        self.btnOff09.setEnabled(False)
        self.btnOff10.setEnabled(False)
        self.btnOff11.setEnabled(False)
        self.btnOff12.setEnabled(False)
        self.btnOff13.setEnabled(False)
        self.btnOff14.setEnabled(False)
        self.btnOff15.setEnabled(False)
        self.btnOff16.setEnabled(False)
        self.btnOff17.setEnabled(False)
        self.btnOff18.setEnabled(False)
        self.btnOff19.setEnabled(False)
        self.btnOff20.setEnabled(False)

        # Trace Packets Tab

        self.tmrUpdateTracedPackets = QTimer()
        self.tmrUpdateTracedPackets.setInterval(500)
        self.timer.timeout.connect(self.update_traced_ids)
        self.timer.start()

        # Logger Tab ===================================================================================================
        self.maxLogCount = 100
        self.logsCount = 0
        self.startLogging = False
        self.logs = []
        self.pbLog.setMinimum = 0
        self.btnStopLog.setEnabled(False)
        self.tblLogs.setColumnWidth(0, 100)
        self.tblLogs.setColumnWidth(1, 100)
        self.tblLogs.setColumnWidth(2, 20)
        self.tblLogs.setColumnWidth(3, 20)
        self.tblLogs.setColumnWidth(4, 20)
        self.tblLogs.setColumnWidth(5, 20)
        self.tblLogs.setColumnWidth(6, 20)
        self.tblLogs.setColumnWidth(7, 20)
        self.tblLogs.setColumnWidth(8, 20)
        self.tblLogs.setColumnWidth(9, 20)
        self.tblLogs.setColumnWidth(10, 100)

        self.btnExportData.setEnabled(False)

        # Transmitter Tab ==============================================================================================

    def find_index(self, messages, id):
        j = 0
        has_index = False
        for row in messages:
            if str(row[0]) == id:
                has_index = True
                break
            else:
                j = j + 1

        if has_index:
            return j
        else:
            return -1

    def init_serial_ports(self):
        self.rxSerialPort = QSerialPort()
        self.cmbRxPortNames.addItems([serialPort.portName() for serialPort in QSerialPortInfo().availablePorts()])
        self.rxSerialDeviceIsConnected = False
        self.rxSerialPort.readyRead.connect(self.on_rx_serial_data_available)
        self.btnRxDisconnect.setEnabled(False)
        self.rxBuffer = ""

        self.txSerialPort = QSerialPort()
        self.cmbTxPortNames.addItems([serialPort.portName() for serialPort in QSerialPortInfo().availablePorts()])
        self.txSerialDeviceIsConnected = False
        self.txSerialPort.readyRead.connect(self.on_tx_serial_data_available)
        self.btnTxDisconnect.setEnabled(False)
        self.txBuffer = ""

    def bind_controls(self):
        # Serial Port Tab
        self.btnRxConnect.clicked.connect(self.open_rx_serial_port)
        self.btnRxDisconnect.clicked.connect(self.close_rx_serial_port)

        self.btnTxConnect.clicked.connect(self.open_tx_serial_port)
        self.btnTxDisconnect.clicked.connect(self.close_tx_serial_port)
        # Trace Packets Tab
        self.btnOn01.clicked.connect(self.trace_slot_on_01)
        self.btnOn02.clicked.connect(self.trace_slot_on_02)
        self.btnOn03.clicked.connect(self.trace_slot_on_03)
        self.btnOn04.clicked.connect(self.trace_slot_on_04)
        self.btnOn05.clicked.connect(self.trace_slot_on_05)
        self.btnOn06.clicked.connect(self.trace_slot_on_06)
        self.btnOn07.clicked.connect(self.trace_slot_on_07)
        self.btnOn08.clicked.connect(self.trace_slot_on_08)
        self.btnOn09.clicked.connect(self.trace_slot_on_09)
        self.btnOn10.clicked.connect(self.trace_slot_on_10)
        self.btnOn11.clicked.connect(self.trace_slot_on_11)
        self.btnOn12.clicked.connect(self.trace_slot_on_12)
        self.btnOn13.clicked.connect(self.trace_slot_on_13)
        self.btnOn14.clicked.connect(self.trace_slot_on_14)
        self.btnOn15.clicked.connect(self.trace_slot_on_15)
        self.btnOn16.clicked.connect(self.trace_slot_on_16)
        self.btnOn17.clicked.connect(self.trace_slot_on_17)
        self.btnOn18.clicked.connect(self.trace_slot_on_18)
        self.btnOn19.clicked.connect(self.trace_slot_on_19)
        self.btnOn20.clicked.connect(self.trace_slot_on_20)

        self.btnOff01.clicked.connect(self.trace_slot_off_01)
        self.btnOff02.clicked.connect(self.trace_slot_off_02)
        self.btnOff03.clicked.connect(self.trace_slot_off_03)
        self.btnOff04.clicked.connect(self.trace_slot_off_04)
        self.btnOff05.clicked.connect(self.trace_slot_off_05)
        self.btnOff06.clicked.connect(self.trace_slot_off_06)
        self.btnOff07.clicked.connect(self.trace_slot_off_07)
        self.btnOff08.clicked.connect(self.trace_slot_off_08)
        self.btnOff09.clicked.connect(self.trace_slot_off_09)
        self.btnOff10.clicked.connect(self.trace_slot_off_10)
        self.btnOff11.clicked.connect(self.trace_slot_off_11)
        self.btnOff12.clicked.connect(self.trace_slot_off_12)
        self.btnOff13.clicked.connect(self.trace_slot_off_13)
        self.btnOff14.clicked.connect(self.trace_slot_off_14)
        self.btnOff15.clicked.connect(self.trace_slot_off_15)
        self.btnOff16.clicked.connect(self.trace_slot_off_16)
        self.btnOff17.clicked.connect(self.trace_slot_off_17)
        self.btnOff18.clicked.connect(self.trace_slot_off_18)
        self.btnOff19.clicked.connect(self.trace_slot_off_19)
        self.btnOff20.clicked.connect(self.trace_slot_off_20)

        # Logger Tab
        self.btnStartLog.clicked.connect(self.start_logging)
        self.btnStopLog.clicked.connect(self.stop_logging)
        self.btnExportData.clicked.connect(self.export_data)

        # Transmitter Tab
        self.leTxId01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxId19.textChanged.connect(self.qlineedit_hex_handler)
        # self.leTxId20.textChanged.connect(lambda: self.qlineedit_handler(self.leTxId20)) # lamda method
        self.leTxId20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxDlc01.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc02.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc03.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc04.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc05.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc06.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc07.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc08.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc09.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc10.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc11.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc12.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc13.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc14.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc15.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc16.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc17.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc18.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc19.textChanged.connect(self.qlineedit_valid_dlc_handler)
        self.leTxDlc20.textChanged.connect(self.qlineedit_valid_dlc_handler)
        # -------------------------------------------------------------------
        self.leTxD0_01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_19.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD0_20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxD1_01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_19.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD1_20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxD2_01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_19.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD2_20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxD3_01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_19.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD3_20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxD4_01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_19.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD4_20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxD5_01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_19.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD5_20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxD6_01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_19.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD6_20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxD7_01.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_02.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_03.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_04.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_05.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_06.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_07.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_08.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_09.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_10.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_11.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_12.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_13.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_14.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_15.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_16.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_17.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_18.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_19.textChanged.connect(self.qlineedit_hex_handler)
        self.leTxD7_20.textChanged.connect(self.qlineedit_hex_handler)
        # ------------------------------------------------------------------
        self.leTxPeriod01.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod02.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod03.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod04.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod05.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod06.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod07.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod08.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod09.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod10.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod11.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod12.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod13.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod14.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod15.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod16.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod17.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod18.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod19.textChanged.connect(self.qlineedit_valid_period_handler)
        self.leTxPeriod20.textChanged.connect(self.qlineedit_valid_period_handler)
        # -------------------------------------------------------------------------
        self.btnTxMsg01.clicked.connect(self.send_slot_01)
        self.btnTxMsg02.clicked.connect(self.send_slot_02)
        self.btnTxMsg03.clicked.connect(self.send_slot_03)
        self.btnTxMsg04.clicked.connect(self.send_slot_04)
        self.btnTxMsg05.clicked.connect(self.send_slot_05)
        self.btnTxMsg06.clicked.connect(self.send_slot_06)
        self.btnTxMsg07.clicked.connect(self.send_slot_07)
        self.btnTxMsg08.clicked.connect(self.send_slot_08)
        self.btnTxMsg09.clicked.connect(self.send_slot_09)
        self.btnTxMsg10.clicked.connect(self.send_slot_10)
        self.btnTxMsg11.clicked.connect(self.send_slot_11)
        self.btnTxMsg12.clicked.connect(self.send_slot_12)
        self.btnTxMsg13.clicked.connect(self.send_slot_13)
        self.btnTxMsg14.clicked.connect(self.send_slot_14)
        self.btnTxMsg15.clicked.connect(self.send_slot_15)
        self.btnTxMsg16.clicked.connect(self.send_slot_16)
        self.btnTxMsg17.clicked.connect(self.send_slot_17)
        self.btnTxMsg18.clicked.connect(self.send_slot_18)
        self.btnTxMsg19.clicked.connect(self.send_slot_19)
        self.btnTxMsg20.clicked.connect(self.send_slot_20)

        self.btnClear.clicked.connect(self.btn_clear_click_handler)
        self.btnReload.clicked.connect(self.btn_reload_click_handler)
        self.btnSave.clicked.connect(self.btn_save_click_handler)
        # ICN 8232
        self.btnSetTpmsSlot.clicked.connect(self.btn_set_tpms_slot_handler)
        self.btnCbmEmsInfo8Slot.clicked.connect(self.btn_cbm_ems_info8_click_handler)
        self.btnHighSpeedInfo3Slot.clicked.connect(self.btn_high_speed_info3_click_handler)
        self.btnSetBodyNetworkManagementSlot.clicked.connect(self.btn_cbm_body_network_click_handler)
        self.btnSetFAMInformationSlot.clicked.connect(self.btn_fam_info_click_handler)
        self.dialWheelSpeed.valueChanged.connect(self.dial_speed_wheel_value_change_handler)
        self.btnSetABSInformationSlot.clicked.connect(self.btn_ABS_information_click_handler)
        self.btnSetCBMEngineInfoSlot.clicked.connect(self.btn_cbm_engine_info6_click_handler)
        self.dialEngineSpeed.valueChanged.connect(self.dial_engine_speed_value_changed_handler)
        self.dialTCO.valueChanged.connect(self.dial_tco_value_changed_handler)
        self.dialVehicleSpeed.valueChanged.connect(self.dial_vehicle_speed_value_changed_handler)

    def open_rx_serial_port(self):
        if not self.rxSerialDeviceIsConnected:
            self.rxSerialPort.setPortName(self.cmbRxPortNames.currentText())
            print("Connecting to: " + self.rxSerialPort.portName())
            if self.rxSerialPort.open(QIODevice.ReadWrite):

                if not self.rxSerialPort.setBaudRate(QSerialPort.BaudRate.Baud115200):
                    print(self.rxSerialPort.errorString())

                if not self.rxSerialPort.setDataBits(QSerialPort.DataBits.Data8):
                    print(self.rxSerialPort.errorString())

                if not self.rxSerialPort.setParity(QSerialPort.Parity.NoParity):
                    print(self.rxSerialPort.errorString())

                if not self.rxSerialPort.setFlowControl(QSerialPort.FlowControl.NoFlowControl):
                    print(self.rxSerialPort.errorString())

                print(self.rxSerialPort.portName() + " receiver serial port is connected")
                self.rxSerialDeviceIsConnected = True
                self.btnRxConnect.setEnabled(False)
                self.btnRxDisconnect.setEnabled(True)
                self.cmbRxPortNames.setEnabled(False)

            else:
                qDebug(self.rxSerialPort.portName() + " not connected")
                qDebug("Error: " + self.rxSerialPort.errorString())
                self.rxSerialDeviceIsConnected = False
                self.btnRxConnect.setEnabled(True)
                self.btnRxDisconnect.setEnabled(False)

        else:
            qDebug("Error: Can not connect, another device is connected")

    def open_tx_serial_port(self):
        if not self.txSerialDeviceIsConnected:
            self.txSerialPort.setPortName(self.cmbTxPortNames.currentText())
            print("Connecting to: " + self.txSerialPort.portName())
            if self.txSerialPort.open(QIODevice.ReadWrite):

                if not self.txSerialPort.setBaudRate(QSerialPort.BaudRate.Baud115200):
                    print(self.txSerialPort.errorString())

                if not self.txSerialPort.setDataBits(QSerialPort.DataBits.Data8):
                    print(self.txSerialPort.errorString())

                if not self.txSerialPort.setParity(QSerialPort.Parity.NoParity):
                    print(self.txSerialPort.errorString())

                if not self.txSerialPort.setFlowControl(QSerialPort.FlowControl.NoFlowControl):
                    print(self.txSerialPort.errorString())

                print(self.txSerialPort.portName() + " receiver serial port is connected")
                self.txSerialDeviceIsConnected = True
                self.btnTxConnect.setEnabled(False)
                self.btnTxDisconnect.setEnabled(True)
                self.cmbTxPortNames.setEnabled(False)

            else:
                qDebug(self.txSerialPort.portName() + " not connected")
                qDebug("Error: " + self.txSerialPort.errorString())
                self.txSerialDeviceIsConnected = False
                self.btnTxConnect.setEnabled(True)
                self.btnTxDisconnect.setEnabled(False)

        else:
            qDebug("Error: Can not connect, another device is connected")

    def close_rx_serial_port(self):
        if self.rxSerialDeviceIsConnected:
            self.rxSerialPort.close()
            self.rxSerialDeviceIsConnected = False
            print("rx connection closed")
            self.btnRxConnect.setEnabled(True)
            self.btnRxDisconnect.setEnabled(False)
            self.cmbRxPortNames.setEnabled(True)
            self.messages = []
            self.update_table()

        else:
            print("Error: Can not disconnect, no device is connected")

    def close_tx_serial_port(self):
        if self.txSerialDeviceIsConnected:
            self.txSerialPort.close()
            self.txSerialDeviceIsConnected = False
            print("tx connection closed")
            self.btnTxConnect.setEnabled(True)
            self.btnTxDisconnect.setEnabled(False)
            self.cmbTxPortNames.setEnabled(True)

        else:
            print("Error: Can not disconnect, no device is connected")

    def on_rx_serial_data_available(self):
        # print("Serial Data Available")
        if self.rxSerialDeviceIsConnected:
            try:
                self.rxBuffer += str(self.rxSerialPort.readLine(), "utf-8")
                # self.rxBuffer.encode("utf-8")
                # print(self.rxBuffer)
                start_sign_position = self.rxBuffer.find("#")
                end_sign_pos = self.rxBuffer.find("|", start_sign_position)

                if "#" in self.rxBuffer and "|" in self.rxBuffer and start_sign_position < end_sign_pos:
                    self.update_message_list(self.rxBuffer)
                    self.rxBuffer = ""
                    self.rxSerialPort.flush()

            except Exception as e:
                pass
                # exc_type, exc_obj, exc_tb = sys.exc_info()
                # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                # print(exc_type, fname, exc_tb.tb_lineno)
                # print(str(e))

    def on_tx_serial_data_available(self):
        print("Tx Serial port Data Available")

    def update_message_list(self, buffer):
        try:
            start = buffer.find("#")
            end = buffer.find("|", start)
            clean = buffer[start:end]
            data = clean.split(",")

            can_id = str(data[0][1:])
            dlc = str(data[1])
            d0 = "0" + str(data[2]) if len(str(data[2])) < 2 else str(data[2])
            d1 = "0" + str(data[3]) if len(str(data[3])) < 2 else str(data[3])
            d2 = "0" + str(data[4]) if len(str(data[4])) < 2 else str(data[4])
            d3 = "0" + str(data[5]) if len(str(data[5])) < 2 else str(data[5])
            d4 = "0" + str(data[6]) if len(str(data[6])) < 2 else str(data[6])
            d5 = "0" + str(data[7]) if len(str(data[7])) < 2 else str(data[7])
            d6 = "0" + str(data[8]) if len(str(data[8])) < 2 else str(data[8])
            d7 = "0" + str(data[9]) if len(str(data[9])) < 2 else str(data[9])
            micros = str(data[10])

            message = [can_id, dlc, d0, d1, d2, d3, d4, d5, d6, d7, "0", "0", micros]

            if self.startLogging == True and self.logsCount <= int(str(self.leLogCount.text())):
                self.logsCount = self.logsCount + 1
                self.logs.append(message)
                self.pbLog.setValue(self.logsCount)

            else:
                self.stop_logging()
                self.update_log_table()

            # print("Serial data: ", can_id, dlc, d0, d1, d2, d3, d4, d5, d6, d7, micros)

            # print("Message index is: ", self.find_index(self.messages, can_id))

            idx = self.find_index(self.messages, can_id)

            # if idx > -1:
            #     print("The Message is: ", self.messages[idx])

            if idx > -1:
                # If message ID exists before so update the message by its index
                # print("Col[11]: ", self.messages[idx][11])
                self.counter = int(self.messages[idx][11]) + 1

                if self.counter >= 1000:
                    self.counter = 0

                self.t1 = self.messages[idx][12]
                self.t2 = micros

                # print("T1: ", str(self.messages[idx][12]), "-T2: ", str(micros))

                self.delta = int(self.t2) - int(self.t1)
                self.period = str(round(self.delta / 1000))
                # print("Period: ", self.period, "mS")

                # print("counter: ", str(self.counter))

                self.messages[idx] = [can_id, dlc, d0, d1, d2, d3, d4, d5, d6, d7, self.period, self.counter, micros]

                # print(self.messages[idx])

            else:
                # The messageID is new so add the message to the list
                self.t1 = datetime.now()
                # message = [can_id, dlc, d0, d1, d2, d3, d4, d5, d6, d7, "0", "0", micros]
                self.messages.append(message)

            # For Debugging Purpose =======================================================
            # for row in self.messages:
            #     for col in row:
            #         print(col, end=" ")
            #     print()
            # print()
            # =============================================================================
            # self.update_table()

        except Exception as e:
            pass
            # exc_type, exc_obj, exc_tb = sys.exc_info()
            # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            # print(exc_type, fname, exc_tb.tb_lineno)
            # print(str(e))

    def update_table(self):
        message_count = len(self.messages)
        if message_count > 0:
            self.tblRx.setRowCount(message_count)
            table_row = 0
            for row in self.messages:
                # print("Table Row:", row)
                self.tblRx.setItem(table_row, 0, QtWidgets.QTableWidgetItem(str(row[0])))  # Can ID
                self.tblRx.setItem(table_row, 1, QtWidgets.QTableWidgetItem(str(row[1])))  # DLC
                self.tblRx.setItem(table_row, 2, QtWidgets.QTableWidgetItem(str(row[2])))  # D0
                self.tblRx.setItem(table_row, 3, QtWidgets.QTableWidgetItem(str(row[3])))  # D1
                self.tblRx.setItem(table_row, 4, QtWidgets.QTableWidgetItem(str(row[4])))  # D2
                self.tblRx.setItem(table_row, 5, QtWidgets.QTableWidgetItem(str(row[5])))  # D3
                self.tblRx.setItem(table_row, 6, QtWidgets.QTableWidgetItem(str(row[6])))  # D4
                self.tblRx.setItem(table_row, 7, QtWidgets.QTableWidgetItem(str(row[7])))  # D5
                self.tblRx.setItem(table_row, 8, QtWidgets.QTableWidgetItem(str(row[8])))  # D6
                self.tblRx.setItem(table_row, 9, QtWidgets.QTableWidgetItem(str(row[9])))  # D7
                self.tblRx.setItem(table_row, 10, QtWidgets.QTableWidgetItem(str(row[10])))  # Period
                self.tblRx.setItem(table_row, 11, QtWidgets.QTableWidgetItem(str(row[11])))  # Counter
                self.tblRx.setItem(table_row, 12, QtWidgets.QTableWidgetItem(str(row[12])))  # Last Update
                # print(row[0], row[1])
                table_row += 1

    def auto_transmit(self):
        if self.auto_transmit_slot_no == 1:
            self.send_slot_01()
        elif self.auto_transmit_slot_no == 2:
            self.send_slot_02()
        elif self.auto_transmit_slot_no == 3:
            self.send_slot_03()
        elif self.auto_transmit_slot_no == 4:
            self.send_slot_04()
        elif self.auto_transmit_slot_no == 5:
            self.send_slot_05()
        elif self.auto_transmit_slot_no == 6:
            self.send_slot_06()
        elif self.auto_transmit_slot_no == 7:
            self.send_slot_07()
        elif self.auto_transmit_slot_no == 8:
            self.send_slot_08()
        elif self.auto_transmit_slot_no == 9:
            self.send_slot_09()
        elif self.auto_transmit_slot_no == 10:
            self.send_slot_10()
        elif self.auto_transmit_slot_no == 11:
            self.send_slot_11()
        elif self.auto_transmit_slot_no == 12:
            self.send_slot_12()
        elif self.auto_transmit_slot_no == 13:
            self.send_slot_13()
        elif self.auto_transmit_slot_no == 14:
            self.send_slot_14()
        elif self.auto_transmit_slot_no == 15:
            self.send_slot_15()
        elif self.auto_transmit_slot_no == 16:
            self.send_slot_16()
        elif self.auto_transmit_slot_no == 17:
            self.send_slot_17()
        elif self.auto_transmit_slot_no == 18:
            self.send_slot_18()
        elif self.auto_transmit_slot_no == 19:
            self.send_slot_19()
        elif self.auto_transmit_slot_no == 20:
            self.send_slot_20()

        self.auto_transmit_slot_no = 0

    def start_logging(self):
        if int(self.leLogCount.text()) > 0:
            self.logs = []
            self.pbLog.setMaximum(int(self.leLogCount.text()))
            self.leLogCount.setReadOnly(True)
            self.btnStartLog.setEnabled(False)
            self.btnStopLog.setEnabled(True)
            self.logsCount = 0
            self.startLogging = True

    def stop_logging(self):
        self.startLogging = False
        self.leLogCount.setReadOnly(False)
        self.btnStartLog.setEnabled(True)
        self.btnStopLog.setEnabled(False)
        if len(self.logs) > 0:
            self.btnExportData.setEnabled(True)

    def update_log_table(self):
        logCount = len(self.logs)
        if logCount > 0:
            self.tblLogs.setRowCount(logCount)
            table_row = 0
            for row in self.logs:
                # print("Table Row:", row)
                self.tblLogs.setItem(table_row, 0, QtWidgets.QTableWidgetItem(str(row[0])))  # ID
                self.tblLogs.setItem(table_row, 1, QtWidgets.QTableWidgetItem(str(row[1])))  # DLC
                self.tblLogs.setItem(table_row, 2, QtWidgets.QTableWidgetItem(str(row[2])))  # D0
                self.tblLogs.setItem(table_row, 3, QtWidgets.QTableWidgetItem(str(row[3])))  # D1
                self.tblLogs.setItem(table_row, 4, QtWidgets.QTableWidgetItem(str(row[4])))  # D2
                self.tblLogs.setItem(table_row, 5, QtWidgets.QTableWidgetItem(str(row[5])))  # D3
                self.tblLogs.setItem(table_row, 6, QtWidgets.QTableWidgetItem(str(row[6])))  # D4
                self.tblLogs.setItem(table_row, 7, QtWidgets.QTableWidgetItem(str(row[7])))  # D5
                self.tblLogs.setItem(table_row, 8, QtWidgets.QTableWidgetItem(str(row[8])))  # D6
                self.tblLogs.setItem(table_row, 9, QtWidgets.QTableWidgetItem(str(row[9])))  # D7
                self.tblLogs.setItem(table_row, 10, QtWidgets.QTableWidgetItem(str(row[12])))  # Time Stamp
                # print(row[0], row[1])
                table_row += 1

    def send_slot_01(self):
        print("SLOT 01 Sent")
        self.send_packet("0",
                         str(self.leTxId01.text()),
                         str(self.leTxDlc01.text()),
                         str(self.leTxD0_01.text()),
                         str(self.leTxD1_01.text()),
                         str(self.leTxD2_01.text()),
                         str(self.leTxD3_01.text()),
                         str(self.leTxD4_01.text()),
                         str(self.leTxD5_01.text()),
                         str(self.leTxD6_01.text()),
                         str(self.leTxD7_01.text()),
                         str(self.leTxPeriod01.text()))

    def send_slot_02(self):
        print("SLOT 02 Sent")
        self.send_packet("1",
                         str(self.leTxId02.text()),
                         str(self.leTxDlc02.text()),
                         str(self.leTxD0_02.text()),
                         str(self.leTxD1_02.text()),
                         str(self.leTxD2_02.text()),
                         str(self.leTxD3_02.text()),
                         str(self.leTxD4_02.text()),
                         str(self.leTxD5_02.text()),
                         str(self.leTxD6_02.text()),
                         str(self.leTxD7_02.text()),
                         str(self.leTxPeriod02.text()))

    def send_slot_03(self):
        print("SLOT 03 Sent")
        self.send_packet("2",
                         str(self.leTxId03.text()),
                         str(self.leTxDlc03.text()),
                         str(self.leTxD0_03.text()),
                         str(self.leTxD1_03.text()),
                         str(self.leTxD2_03.text()),
                         str(self.leTxD3_03.text()),
                         str(self.leTxD4_03.text()),
                         str(self.leTxD5_03.text()),
                         str(self.leTxD6_03.text()),
                         str(self.leTxD7_03.text()),
                         str(self.leTxPeriod03.text()))

    def send_slot_04(self):
        print("SLOT 04 Sent")
        self.send_packet("3",
                         str(self.leTxId04.text()),
                         str(self.leTxDlc04.text()),
                         str(self.leTxD0_04.text()),
                         str(self.leTxD1_04.text()),
                         str(self.leTxD2_04.text()),
                         str(self.leTxD3_04.text()),
                         str(self.leTxD4_04.text()),
                         str(self.leTxD5_04.text()),
                         str(self.leTxD6_04.text()),
                         str(self.leTxD7_04.text()),
                         str(self.leTxPeriod04.text()))

    def send_slot_05(self):
        print("SLOT 05 Sent")
        self.send_packet("4",
                         str(self.leTxId05.text()),
                         str(self.leTxDlc05.text()),
                         str(self.leTxD0_05.text()),
                         str(self.leTxD1_05.text()),
                         str(self.leTxD2_05.text()),
                         str(self.leTxD3_05.text()),
                         str(self.leTxD4_05.text()),
                         str(self.leTxD5_05.text()),
                         str(self.leTxD6_05.text()),
                         str(self.leTxD7_05.text()),
                         str(self.leTxPeriod05.text()))

    def send_slot_06(self):
        print("SLOT 06 Sent")
        self.send_packet("5",
                         str(self.leTxId06.text()),
                         str(self.leTxDlc06.text()),
                         str(self.leTxD0_06.text()),
                         str(self.leTxD1_06.text()),
                         str(self.leTxD2_06.text()),
                         str(self.leTxD3_06.text()),
                         str(self.leTxD4_06.text()),
                         str(self.leTxD5_06.text()),
                         str(self.leTxD6_06.text()),
                         str(self.leTxD7_06.text()),
                         str(self.leTxPeriod06.text()))

    def send_slot_07(self):
        print("SLOT 07 Sent")
        self.send_packet("6",
                         str(self.leTxId07.text()),
                         str(self.leTxDlc07.text()),
                         str(self.leTxD0_07.text()),
                         str(self.leTxD1_07.text()),
                         str(self.leTxD2_07.text()),
                         str(self.leTxD3_07.text()),
                         str(self.leTxD4_07.text()),
                         str(self.leTxD5_07.text()),
                         str(self.leTxD6_07.text()),
                         str(self.leTxD7_07.text()),
                         str(self.leTxPeriod07.text()))

    def send_slot_08(self):
        print("SLOT 08 Sent")
        self.send_packet("7",
                         str(self.leTxId08.text()),
                         str(self.leTxDlc08.text()),
                         str(self.leTxD0_08.text()),
                         str(self.leTxD1_08.text()),
                         str(self.leTxD2_08.text()),
                         str(self.leTxD3_08.text()),
                         str(self.leTxD4_08.text()),
                         str(self.leTxD5_08.text()),
                         str(self.leTxD6_08.text()),
                         str(self.leTxD7_08.text()),
                         str(self.leTxPeriod08.text()))

    def send_slot_09(self):
        print("SLOT 09 Sent")
        self.send_packet("8",
                         str(self.leTxId09.text()),
                         str(self.leTxDlc09.text()),
                         str(self.leTxD0_09.text()),
                         str(self.leTxD1_09.text()),
                         str(self.leTxD2_09.text()),
                         str(self.leTxD3_09.text()),
                         str(self.leTxD4_09.text()),
                         str(self.leTxD5_09.text()),
                         str(self.leTxD6_09.text()),
                         str(self.leTxD7_09.text()),
                         str(self.leTxPeriod09.text()))

    def send_slot_10(self):
        print("SLOT 10 Sent")
        self.send_packet("9",
                         str(self.leTxId10.text()),
                         str(self.leTxDlc10.text()),
                         str(self.leTxD0_10.text()),
                         str(self.leTxD1_10.text()),
                         str(self.leTxD2_10.text()),
                         str(self.leTxD3_10.text()),
                         str(self.leTxD4_10.text()),
                         str(self.leTxD5_10.text()),
                         str(self.leTxD6_10.text()),
                         str(self.leTxD7_10.text()),
                         str(self.leTxPeriod10.text()))

    def send_slot_11(self):
        print("SLOT 11 Sent")
        self.send_packet("10",
                         str(self.leTxId11.text()),
                         str(self.leTxDlc11.text()),
                         str(self.leTxD0_11.text()),
                         str(self.leTxD1_11.text()),
                         str(self.leTxD2_11.text()),
                         str(self.leTxD3_11.text()),
                         str(self.leTxD4_11.text()),
                         str(self.leTxD5_11.text()),
                         str(self.leTxD6_11.text()),
                         str(self.leTxD7_11.text()),
                         str(self.leTxPeriod11.text()))

    def send_slot_12(self):
        print("SLOT 12 Sent")
        self.send_packet("11",
                         str(self.leTxId12.text()),
                         str(self.leTxDlc12.text()),
                         str(self.leTxD0_12.text()),
                         str(self.leTxD1_12.text()),
                         str(self.leTxD2_12.text()),
                         str(self.leTxD3_12.text()),
                         str(self.leTxD4_12.text()),
                         str(self.leTxD5_12.text()),
                         str(self.leTxD6_12.text()),
                         str(self.leTxD7_12.text()),
                         str(self.leTxPeriod12.text()))

    def send_slot_13(self):
        print("SLOT 13 Sent")
        self.send_packet("12",
                         str(self.leTxId13.text()),
                         str(self.leTxDlc13.text()),
                         str(self.leTxD0_13.text()),
                         str(self.leTxD1_13.text()),
                         str(self.leTxD2_13.text()),
                         str(self.leTxD3_13.text()),
                         str(self.leTxD4_13.text()),
                         str(self.leTxD5_13.text()),
                         str(self.leTxD6_13.text()),
                         str(self.leTxD7_13.text()),
                         str(self.leTxPeriod13.text()))

    def send_slot_14(self):
        print("SLOT 14 Sent")
        self.send_packet("13",
                         str(self.leTxId14.text()),
                         str(self.leTxDlc14.text()),
                         str(self.leTxD0_14.text()),
                         str(self.leTxD1_14.text()),
                         str(self.leTxD2_14.text()),
                         str(self.leTxD3_14.text()),
                         str(self.leTxD4_14.text()),
                         str(self.leTxD5_14.text()),
                         str(self.leTxD6_14.text()),
                         str(self.leTxD7_14.text()),
                         str(self.leTxPeriod14.text()))

    def send_slot_15(self):
        print("SLOT 15 Sent")
        self.send_packet("14",
                         str(self.leTxId15.text()),
                         str(self.leTxDlc15.text()),
                         str(self.leTxD0_15.text()),
                         str(self.leTxD1_15.text()),
                         str(self.leTxD2_15.text()),
                         str(self.leTxD3_15.text()),
                         str(self.leTxD4_15.text()),
                         str(self.leTxD5_15.text()),
                         str(self.leTxD6_15.text()),
                         str(self.leTxD7_15.text()),
                         str(self.leTxPeriod15.text()))

    def send_slot_16(self):
        print("SLOT 16 Sent")
        self.send_packet("15",
                         str(self.leTxId16.text()),
                         str(self.leTxDlc16.text()),
                         str(self.leTxD0_16.text()),
                         str(self.leTxD1_16.text()),
                         str(self.leTxD2_16.text()),
                         str(self.leTxD3_16.text()),
                         str(self.leTxD4_16.text()),
                         str(self.leTxD5_16.text()),
                         str(self.leTxD6_16.text()),
                         str(self.leTxD7_16.text()),
                         str(self.leTxPeriod16.text()))

    def send_slot_17(self):
        print("SLOT 17 Sent")
        self.send_packet("16",
                         str(self.leTxId17.text()),
                         str(self.leTxDlc17.text()),
                         str(self.leTxD0_17.text()),
                         str(self.leTxD1_17.text()),
                         str(self.leTxD2_17.text()),
                         str(self.leTxD3_17.text()),
                         str(self.leTxD4_17.text()),
                         str(self.leTxD5_17.text()),
                         str(self.leTxD6_17.text()),
                         str(self.leTxD7_17.text()),
                         str(self.leTxPeriod17.text()))

    def send_slot_18(self):
        print("SLOT 18 Sent")
        self.send_packet("17",
                         str(self.leTxId18.text()),
                         str(self.leTxDlc18.text()),
                         str(self.leTxD0_18.text()),
                         str(self.leTxD1_18.text()),
                         str(self.leTxD2_18.text()),
                         str(self.leTxD3_18.text()),
                         str(self.leTxD4_18.text()),
                         str(self.leTxD5_18.text()),
                         str(self.leTxD6_18.text()),
                         str(self.leTxD7_18.text()),
                         str(self.leTxPeriod18.text()))

    def send_slot_19(self):
        print("SLOT 19 Sent")
        self.send_packet("18",
                         str(self.leTxId19.text()),
                         str(self.leTxDlc19.text()),
                         str(self.leTxD0_19.text()),
                         str(self.leTxD1_19.text()),
                         str(self.leTxD2_19.text()),
                         str(self.leTxD3_19.text()),
                         str(self.leTxD4_19.text()),
                         str(self.leTxD5_19.text()),
                         str(self.leTxD6_19.text()),
                         str(self.leTxD7_19.text()),
                         str(self.leTxPeriod19.text()))

    def send_slot_20(self):
        print("SLOT 20 Sent")
        self.send_packet("19",
                         str(self.leTxId20.text()),
                         str(self.leTxDlc20.text()),
                         str(self.leTxD0_20.text()),
                         str(self.leTxD1_20.text()),
                         str(self.leTxD2_20.text()),
                         str(self.leTxD3_20.text()),
                         str(self.leTxD4_20.text()),
                         str(self.leTxD5_20.text()),
                         str(self.leTxD6_20.text()),
                         str(self.leTxD7_20.text()),
                         str(self.leTxPeriod20.text()))

    def send_packet(self, strSlot, strID, strDlc, strD0, strD1, strD2, strD3, strD4, strD5, strD6, strD7, strPeriod):
        if self.txSerialDeviceIsConnected == True:
            try:
                sId = str(int(strID, 16))
                print("ID: ", sId)
                if str(int(strD0, 16)) != "":
                    sD0 = str(int(strD0, 16))
                else:
                    sD0 = str(int(0, 16))

                if str(int(strD1, 16)) != "":
                    sD1 = str(int(strD1, 16))
                else:
                    sD1 = str(int(0, 16))

                if str(int(strD2, 16)) != "":
                    sD2 = str(int(strD2, 16))
                else:
                    sD2 = str(int(0, 16))

                if str(int(strD3, 16)) != "":
                    sD3 = str(int(strD3, 16))
                else:
                    sD3 = str(int(0, 16))

                if str(int(strD4, 16)) != "":
                    sD4 = str(int(strD4, 16))
                else:
                    sD4 = str(int(0, 16))

                if str(int(strD5, 16)) != "":
                    sD5 = str(int(strD5, 16))
                else:
                    sD5 = str(int(0, 16))

                if str(int(strD6, 16)) != "":
                    sD6 = str(int(strD6, 16))
                else:
                    sD6 = str(int(0, 16))

                if str(int(strD7, 16)) != "":
                    sD7 = str(int(strD7, 16))
                else:
                    sD7 = str(int(0, 16))

                strPacket = strSlot + "," + sId + "," + strDlc + "," + sD0 + "," + sD1 + "," + sD2 + "," + sD3 + "," + sD4 + "," + sD5 + "," + sD6 + "," + sD7 + "," + strPeriod + "\n"

                print("Tx Packet: ", strPacket)
                self.txSerialPort.write(strPacket.encode())

            except:
                pass

    # ===============================================================================================================
    def trace_slot_on_01(self):
        print("Slot 01 Trace On")
        self.blnTraceSlot01 = True
        self.btnOn01.setEnabled(False)
        self.btnOff01.setEnabled(True)

    def trace_slot_on_02(self):
        print("Slot 02 Trace On")
        self.blnTraceSlot02 = True
        self.btnOn02.setEnabled(False)
        self.btnOff02.setEnabled(True)

    def trace_slot_on_03(self):
        print("Slot 03 Trace On")
        self.blnTraceSlot03 = True
        self.btnOn03.setEnabled(False)
        self.btnOff03.setEnabled(True)

    def trace_slot_on_04(self):
        print("Slot 04 Trace On")
        self.blnTraceSlot04 = True
        self.btnOn04.setEnabled(False)
        self.btnOff04.setEnabled(True)

    def trace_slot_on_05(self):
        print("Slot 05 Trace On")
        self.blnTraceSlot05 = True
        self.btnOn05.setEnabled(False)
        self.btnOff05.setEnabled(True)

    def trace_slot_on_06(self):
        print("Slot 06 Trace On")
        self.blnTraceSlot06 = True
        self.btnOn06.setEnabled(False)
        self.btnOff06.setEnabled(True)

    def trace_slot_on_07(self):
        print("Slot 07 Trace On")
        self.blnTraceSlot07 = True
        self.btnOn07.setEnabled(False)
        self.btnOff07.setEnabled(True)

    def trace_slot_on_08(self):
        print("Slot 08 Trace On")
        self.blnTraceSlot08 = True
        self.btnOn08.setEnabled(False)
        self.btnOff08.setEnabled(True)

    def trace_slot_on_09(self):
        print("Slot 09 Trace On")
        self.blnTraceSlot09 = True
        self.btnOn09.setEnabled(False)
        self.btnOff09.setEnabled(True)

    def trace_slot_on_10(self):
        print("Slot 10 Trace On")
        self.blnTraceSlot10 = True
        self.btnOn10.setEnabled(False)
        self.btnOff10.setEnabled(True)

    def trace_slot_on_11(self):
        print("Slot 11 Trace On")
        self.blnTraceSlot11 = True
        self.btnOn11.setEnabled(False)
        self.btnOff11.setEnabled(True)

    def trace_slot_on_12(self):
        print("Slot 12 Trace On")
        self.blnTraceSlot12 = True
        self.btnOn12.setEnabled(False)
        self.btnOff12.setEnabled(True)

    def trace_slot_on_13(self):
        print("Slot 13 Trace On")
        self.blnTraceSlot13 = True
        self.btnOn13.setEnabled(False)
        self.btnOff13.setEnabled(True)

    def trace_slot_on_14(self):
        print("Slot 14 Trace On")
        self.blnTraceSlot14 = True
        self.btnOn14.setEnabled(False)
        self.btnOff14.setEnabled(True)

    def trace_slot_on_15(self):
        print("Slot 15 Trace On")
        self.blnTraceSlot15 = True
        self.btnOn15.setEnabled(False)
        self.btnOff15.setEnabled(True)

    def trace_slot_on_16(self):
        print("Slot 16 Trace On")
        self.blnTraceSlot16 = True
        self.btnOn16.setEnabled(False)
        self.btnOff16.setEnabled(True)

    def trace_slot_on_17(self):
        print("Slot 17 Trace On")
        self.blnTraceSlot17 = True
        self.btnOn17.setEnabled(False)
        self.btnOff17.setEnabled(True)

    def trace_slot_on_18(self):
        print("Slot 18 Trace On")
        self.blnTraceSlot18 = True
        self.btnOn18.setEnabled(False)
        self.btnOff18.setEnabled(True)

    def trace_slot_on_19(self):
        print("Slot 19 Trace On")
        self.blnTraceSlot19 = True
        self.btnOn19.setEnabled(False)
        self.btnOff19.setEnabled(True)

    def trace_slot_on_20(self):
        print("Slot 20 Trace On")
        self.blnTraceSlot20 = True
        self.btnOn20.setEnabled(False)
        self.btnOff20.setEnabled(True)

    # ===============================================================================================================
    def trace_slot_off_01(self):
        print("Slot 01 Trace Off")
        self.blnTraceSlot01 = False
        self.btnOn01.setEnabled(True)
        self.btnOff01.setEnabled(False)

    def trace_slot_off_02(self):
        print("Slot 02 Trace Off")
        self.blnTraceSlot02 = False
        self.btnOn02.setEnabled(True)
        self.btnOff02.setEnabled(False)

    def trace_slot_off_03(self):
        print("Slot 03 Trace Off")
        self.blnTraceSlot03 = False
        self.btnOn03.setEnabled(True)
        self.btnOff03.setEnabled(False)

    def trace_slot_off_04(self):
        print("Slot 04 Trace Off")
        self.blnTraceSlot04 = False
        self.btnOn04.setEnabled(True)
        self.btnOff04.setEnabled(False)

    def trace_slot_off_05(self):
        print("Slot 05 Trace Off")
        self.blnTraceSlot05 = False
        self.btnOn05.setEnabled(True)
        self.btnOff05.setEnabled(False)

    def trace_slot_off_06(self):
        print("Slot 06 Trace Off")
        self.blnTraceSlot06 = False
        self.btnOn06.setEnabled(True)
        self.btnOff06.setEnabled(False)

    def trace_slot_off_07(self):
        print("Slot 07 Trace Off")
        self.blnTraceSlot07 = False
        self.btnOn07.setEnabled(True)
        self.btnOff07.setEnabled(False)

    def trace_slot_off_08(self):
        print("Slot 08 Trace Off")
        self.blnTraceSlot08 = False
        self.btnOn08.setEnabled(True)
        self.btnOff08.setEnabled(False)

    def trace_slot_off_09(self):
        print("Slot 09 Trace Off")
        self.blnTraceSlot09 = False
        self.btnOn09.setEnabled(True)
        self.btnOff09.setEnabled(False)

    def trace_slot_off_10(self):
        print("Slot 10 Trace Off")
        self.blnTraceSlot10 = False
        self.btnOn10.setEnabled(True)
        self.btnOff10.setEnabled(False)

    def trace_slot_off_11(self):
        print("Slot 11 Trace Off")
        self.blnTraceSlot11 = False
        self.btnOn11.setEnabled(True)
        self.btnOff11.setEnabled(False)

    def trace_slot_off_12(self):
        print("Slot 12 Trace Off")
        self.blnTraceSlot12 = False
        self.btnOn12.setEnabled(True)
        self.btnOff12.setEnabled(False)

    def trace_slot_off_13(self):
        print("Slot 13 Trace Off")
        self.blnTraceSlot13 = False
        self.btnOn13.setEnabled(True)
        self.btnOff13.setEnabled(False)

    def trace_slot_off_14(self):
        print("Slot 14 Trace Off")
        self.blnTraceSlot14 = False
        self.btnOn14.setEnabled(True)
        self.btnOff14.setEnabled(False)

    def trace_slot_off_15(self):
        print("Slot 15 Trace Off")
        self.blnTraceSlot15 = False
        self.btnOn15.setEnabled(True)
        self.btnOff15.setEnabled(False)

    def trace_slot_off_16(self):
        print("Slot 16 Trace Off")
        self.blnTraceSlot16 = False
        self.btnOn16.setEnabled(True)
        self.btnOff16.setEnabled(False)

    def trace_slot_off_17(self):
        print("Slot 17 Trace Off")
        self.blnTraceSlot17 = False
        self.btnOn17.setEnabled(True)
        self.btnOff17.setEnabled(False)

    def trace_slot_off_18(self):
        print("Slot 18 Trace Off")
        self.blnTraceSlot18 = False
        self.btnOn18.setEnabled(True)
        self.btnOff18.setEnabled(False)

    def trace_slot_off_19(self):
        print("Slot 19 Trace Off")
        self.blnTraceSlot19 = False
        self.btnOn19.setEnabled(True)
        self.btnOff19.setEnabled(False)

    def trace_slot_off_20(self):
        print("Slot 20 Trace Off")
        self.blnTraceSlot20 = False
        self.btnOn20.setEnabled(True)
        self.btnOff20.setEnabled(False)

    def export_data(self):
        if len(self.logs) > 0:
            fields = ['Can Id', 'Dlc', 'D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'Period', 'Counter', 'Timestamp']
            timestr = time.strftime("%Y%m%d-%H%M%S")
            filename = timestr + '.csv'
            with open(filename, 'w') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(fields)
                csv_writer.writerows(self.logs)

    def update_traced_ids(self):
        idx01 = self.find_index(self.messages, str(self.leRxId01.text()))
        if self.leRxId01.text() != "" and idx01 != -1 and len(self.messages) > 0 and self.blnTraceSlot01 == True:
            self.leRxDlc01.setText(str(self.messages[idx01][1]))
            self.leRxD0_01.setText(str(self.messages[idx01][2]))
            self.leRxD1_01.setText(str(self.messages[idx01][3]))
            self.leRxD2_01.setText(str(self.messages[idx01][4]))
            self.leRxD3_01.setText(str(self.messages[idx01][5]))
            self.leRxD4_01.setText(str(self.messages[idx01][6]))
            self.leRxD5_01.setText(str(self.messages[idx01][7]))
            self.leRxD6_01.setText(str(self.messages[idx01][8]))
            self.leRxD7_01.setText(str(self.messages[idx01][9]))
            self.leRxPeriod01.setText(str(self.messages[idx01][10]))
            self.leRxCounter01.setText(str(self.messages[idx01][11]))
        # -----------------------------------------------------------------------
        idx02 = self.find_index(self.messages, str(self.leRxId02.text()))
        if self.leRxId02.text() != "" and idx02 != -1 and len(self.messages) > 0 and self.blnTraceSlot02 == True:
            self.leRxDlc02.setText(str(self.messages[idx02][1]))
            self.leRxD0_02.setText(str(self.messages[idx02][2]))
            self.leRxD1_02.setText(str(self.messages[idx02][3]))
            self.leRxD2_02.setText(str(self.messages[idx02][4]))
            self.leRxD3_02.setText(str(self.messages[idx02][5]))
            self.leRxD4_02.setText(str(self.messages[idx02][6]))
            self.leRxD5_02.setText(str(self.messages[idx02][7]))
            self.leRxD6_02.setText(str(self.messages[idx02][8]))
            self.leRxD7_02.setText(str(self.messages[idx02][9]))
            self.leRxPeriod02.setText(str(self.messages[idx02][10]))
            self.leRxCounter02.setText(str(self.messages[idx02][11]))
        # -----------------------------------------------------------------------
        idx03 = self.find_index(self.messages, str(self.leRxId03.text()))
        if self.leRxId03.text() != "" and idx03 != -1 and len(self.messages) > 0 and self.blnTraceSlot03 == True:
            self.leRxDlc03.setText(str(self.messages[idx03][1]))
            self.leRxD0_03.setText(str(self.messages[idx03][2]))
            self.leRxD1_03.setText(str(self.messages[idx03][3]))
            self.leRxD2_03.setText(str(self.messages[idx03][4]))
            self.leRxD3_03.setText(str(self.messages[idx03][5]))
            self.leRxD4_03.setText(str(self.messages[idx03][6]))
            self.leRxD5_03.setText(str(self.messages[idx03][7]))
            self.leRxD6_03.setText(str(self.messages[idx03][8]))
            self.leRxD7_03.setText(str(self.messages[idx03][9]))
            self.leRxPeriod03.setText(str(self.messages[idx03][10]))
            self.leRxCounter03.setText(str(self.messages[idx03][11]))
        # -----------------------------------------------------------------------
        idx04 = self.find_index(self.messages, str(self.leRxId04.text()))
        if self.leRxId04.text() != "" and idx04 != -1 and len(self.messages) > 0 and self.blnTraceSlot04 == True:
            self.leRxDlc04.setText(str(self.messages[idx04][1]))
            self.leRxD0_04.setText(str(self.messages[idx04][2]))
            self.leRxD1_04.setText(str(self.messages[idx04][3]))
            self.leRxD2_04.setText(str(self.messages[idx04][4]))
            self.leRxD3_04.setText(str(self.messages[idx04][5]))
            self.leRxD4_04.setText(str(self.messages[idx04][6]))
            self.leRxD5_04.setText(str(self.messages[idx04][7]))
            self.leRxD6_04.setText(str(self.messages[idx04][8]))
            self.leRxD7_04.setText(str(self.messages[idx04][9]))
            self.leRxPeriod04.setText(str(self.messages[idx04][10]))
            self.leRxCounter04.setText(str(self.messages[idx04][11]))
        # -----------------------------------------------------------------------
        idx05 = self.find_index(self.messages, str(self.leRxId05.text()))
        if self.leRxId05.text() != "" and idx05 != -1 and len(self.messages) > 0 and self.blnTraceSlot05 == True:
            self.leRxDlc05.setText(str(self.messages[idx05][1]))
            self.leRxD0_05.setText(str(self.messages[idx05][2]))
            self.leRxD1_05.setText(str(self.messages[idx05][3]))
            self.leRxD2_05.setText(str(self.messages[idx05][4]))
            self.leRxD3_05.setText(str(self.messages[idx05][5]))
            self.leRxD4_05.setText(str(self.messages[idx05][6]))
            self.leRxD5_05.setText(str(self.messages[idx05][7]))
            self.leRxD6_05.setText(str(self.messages[idx05][8]))
            self.leRxD7_05.setText(str(self.messages[idx05][9]))
            self.leRxPeriod05.setText(str(self.messages[idx05][10]))
            self.leRxCounter05.setText(str(self.messages[idx05][11]))
            # -----------------------------------------------------------------------
        idx06 = self.find_index(self.messages, str(self.leRxId06.text()))
        if self.leRxId06.text() != "" and idx06 != -1 and len(self.messages) > 0 and self.blnTraceSlot06 == True:
            self.leRxDlc06.setText(str(self.messages[idx06][1]))
            self.leRxD0_06.setText(str(self.messages[idx06][2]))
            self.leRxD1_06.setText(str(self.messages[idx06][3]))
            self.leRxD2_06.setText(str(self.messages[idx06][4]))
            self.leRxD3_06.setText(str(self.messages[idx06][5]))
            self.leRxD4_06.setText(str(self.messages[idx06][6]))
            self.leRxD5_06.setText(str(self.messages[idx06][7]))
            self.leRxD6_06.setText(str(self.messages[idx06][8]))
            self.leRxD7_06.setText(str(self.messages[idx06][9]))
            self.leRxPeriod06.setText(str(self.messages[idx06][10]))
            self.leRxCounter06.setText(str(self.messages[idx06][11]))
            # -----------------------------------------------------------------------
        idx07 = self.find_index(self.messages, str(self.leRxId07.text()))
        if self.leRxId07.text() != "" and idx07 != -1 and len(self.messages) > 0 and self.blnTraceSlot07 == True:
            self.leRxDlc07.setText(str(self.messages[idx07][1]))
            self.leRxD0_07.setText(str(self.messages[idx07][2]))
            self.leRxD1_07.setText(str(self.messages[idx07][3]))
            self.leRxD2_07.setText(str(self.messages[idx07][4]))
            self.leRxD3_07.setText(str(self.messages[idx07][5]))
            self.leRxD4_07.setText(str(self.messages[idx07][6]))
            self.leRxD5_07.setText(str(self.messages[idx07][7]))
            self.leRxD6_07.setText(str(self.messages[idx07][8]))
            self.leRxD7_07.setText(str(self.messages[idx07][9]))
            self.leRxPeriod07.setText(str(self.messages[idx07][10]))
            self.leRxCounter07.setText(str(self.messages[idx07][11]))
            # -----------------------------------------------------------------------
        idx08 = self.find_index(self.messages, str(self.leRxId08.text()))
        if self.leRxId08.text() != "" and idx08 != -1 and len(self.messages) > 0 and self.blnTraceSlot08 == True:
            self.leRxDlc08.setText(str(self.messages[idx08][1]))
            self.leRxD0_08.setText(str(self.messages[idx08][2]))
            self.leRxD1_08.setText(str(self.messages[idx08][3]))
            self.leRxD2_08.setText(str(self.messages[idx08][4]))
            self.leRxD3_08.setText(str(self.messages[idx08][5]))
            self.leRxD4_08.setText(str(self.messages[idx08][6]))
            self.leRxD5_08.setText(str(self.messages[idx08][7]))
            self.leRxD6_08.setText(str(self.messages[idx08][8]))
            self.leRxD7_08.setText(str(self.messages[idx08][9]))
            self.leRxPeriod08.setText(str(self.messages[idx08][10]))
            self.leRxCounter08.setText(str(self.messages[idx08][11]))
            # -----------------------------------------------------------------------
        idx09 = self.find_index(self.messages, str(self.leRxId09.text()))
        if self.leRxId09.text() != "" and idx09 != -1 and len(self.messages) > 0 and self.blnTraceSlot09 == True:
            self.leRxDlc09.setText(str(self.messages[idx09][1]))
            self.leRxD0_09.setText(str(self.messages[idx09][2]))
            self.leRxD1_09.setText(str(self.messages[idx09][3]))
            self.leRxD2_09.setText(str(self.messages[idx09][4]))
            self.leRxD3_09.setText(str(self.messages[idx09][5]))
            self.leRxD4_09.setText(str(self.messages[idx09][6]))
            self.leRxD5_09.setText(str(self.messages[idx09][7]))
            self.leRxD6_09.setText(str(self.messages[idx09][8]))
            self.leRxD7_09.setText(str(self.messages[idx09][9]))
            self.leRxPeriod09.setText(str(self.messages[idx09][10]))
            self.leRxCounter09.setText(str(self.messages[idx09][11]))
            # -----------------------------------------------------------------------
        idx10 = self.find_index(self.messages, str(self.leRxId10.text()))
        if self.leRxId10.text() != "" and idx10 != -1 and len(self.messages) > 0 and self.blnTraceSlot10 == True:
            self.leRxDlc10.setText(str(self.messages[idx10][1]))
            self.leRxD0_10.setText(str(self.messages[idx10][2]))
            self.leRxD1_10.setText(str(self.messages[idx10][3]))
            self.leRxD2_10.setText(str(self.messages[idx10][4]))
            self.leRxD3_10.setText(str(self.messages[idx10][5]))
            self.leRxD4_10.setText(str(self.messages[idx10][6]))
            self.leRxD5_10.setText(str(self.messages[idx10][7]))
            self.leRxD6_10.setText(str(self.messages[idx10][8]))
            self.leRxD7_10.setText(str(self.messages[idx10][9]))
            self.leRxPeriod10.setText(str(self.messages[idx10][10]))
            self.leRxCounter10.setText(str(self.messages[idx10][11]))
            # -----------------------------------------------------------------------
        idx11 = self.find_index(self.messages, str(self.leRxId11.text()))
        if self.leRxId11.text() != "" and idx11 != -1 and len(self.messages) > 0 and self.blnTraceSlot11 == True:
            self.leRxDlc11.setText(str(self.messages[idx11][1]))
            self.leRxD0_11.setText(str(self.messages[idx11][2]))
            self.leRxD1_11.setText(str(self.messages[idx11][3]))
            self.leRxD2_11.setText(str(self.messages[idx11][4]))
            self.leRxD3_11.setText(str(self.messages[idx11][5]))
            self.leRxD4_11.setText(str(self.messages[idx11][6]))
            self.leRxD5_11.setText(str(self.messages[idx11][7]))
            self.leRxD6_11.setText(str(self.messages[idx11][8]))
            self.leRxD7_11.setText(str(self.messages[idx11][9]))
            self.leRxPeriod11.setText(str(self.messages[idx11][10]))
            self.leRxCounter11.setText(str(self.messages[idx11][11]))
            # -----------------------------------------------------------------------
        idx12 = self.find_index(self.messages, str(self.leRxId12.text()))
        if self.leRxId12.text() != "" and idx12 != -1 and len(self.messages) > 0 and self.blnTraceSlot12 == True:
            self.leRxDlc12.setText(str(self.messages[idx12][1]))
            self.leRxD0_12.setText(str(self.messages[idx12][2]))
            self.leRxD1_12.setText(str(self.messages[idx12][3]))
            self.leRxD2_12.setText(str(self.messages[idx12][4]))
            self.leRxD3_12.setText(str(self.messages[idx12][5]))
            self.leRxD4_12.setText(str(self.messages[idx12][6]))
            self.leRxD5_12.setText(str(self.messages[idx12][7]))
            self.leRxD6_12.setText(str(self.messages[idx12][8]))
            self.leRxD7_12.setText(str(self.messages[idx12][9]))
            self.leRxPeriod12.setText(str(self.messages[idx12][10]))
            self.leRxCounter12.setText(str(self.messages[idx12][11]))
            # -----------------------------------------------------------------------
        idx13 = self.find_index(self.messages, str(self.leRxId13.text()))
        if self.leRxId13.text() != "" and idx13 != -1 and len(self.messages) > 0 and self.blnTraceSlot13 == True:
            self.leRxDlc13.setText(str(self.messages[idx13][1]))
            self.leRxD0_13.setText(str(self.messages[idx13][2]))
            self.leRxD1_13.setText(str(self.messages[idx13][3]))
            self.leRxD2_13.setText(str(self.messages[idx13][4]))
            self.leRxD3_13.setText(str(self.messages[idx13][5]))
            self.leRxD4_13.setText(str(self.messages[idx13][6]))
            self.leRxD5_13.setText(str(self.messages[idx13][7]))
            self.leRxD6_13.setText(str(self.messages[idx13][8]))
            self.leRxD7_13.setText(str(self.messages[idx13][9]))
            self.leRxPeriod13.setText(str(self.messages[idx13][10]))
            self.leRxCounter13.setText(str(self.messages[idx13][11]))
            # -----------------------------------------------------------------------
        idx14 = self.find_index(self.messages, str(self.leRxId14.text()))
        if self.leRxId14.text() != "" and idx14 != -1 and len(self.messages) > 0 and self.blnTraceSlot14 == True:
            self.leRxDlc14.setText(str(self.messages[idx14][1]))
            self.leRxD0_14.setText(str(self.messages[idx14][2]))
            self.leRxD1_14.setText(str(self.messages[idx14][3]))
            self.leRxD2_14.setText(str(self.messages[idx14][4]))
            self.leRxD3_14.setText(str(self.messages[idx14][5]))
            self.leRxD4_14.setText(str(self.messages[idx14][6]))
            self.leRxD5_14.setText(str(self.messages[idx14][7]))
            self.leRxD6_14.setText(str(self.messages[idx14][8]))
            self.leRxD7_14.setText(str(self.messages[idx14][9]))
            self.leRxPeriod14.setText(str(self.messages[idx14][10]))
            self.leRxCounter14.setText(str(self.messages[idx14][11]))
            # -----------------------------------------------------------------------
        idx15 = self.find_index(self.messages, str(self.leRxId15.text()))
        if self.leRxId15.text() != "" and idx15 != -1 and len(self.messages) > 0 and self.blnTraceSlot15 == True:
            self.leRxDlc15.setText(str(self.messages[idx15][1]))
            self.leRxD0_15.setText(str(self.messages[idx15][2]))
            self.leRxD1_15.setText(str(self.messages[idx15][3]))
            self.leRxD2_15.setText(str(self.messages[idx15][4]))
            self.leRxD3_15.setText(str(self.messages[idx15][5]))
            self.leRxD4_15.setText(str(self.messages[idx15][6]))
            self.leRxD5_15.setText(str(self.messages[idx15][7]))
            self.leRxD6_15.setText(str(self.messages[idx15][8]))
            self.leRxD7_15.setText(str(self.messages[idx15][9]))
            self.leRxPeriod15.setText(str(self.messages[idx15][10]))
            self.leRxCounter15.setText(str(self.messages[idx15][11]))
            # -----------------------------------------------------------------------
        idx16 = self.find_index(self.messages, str(self.leRxId16.text()))
        if self.leRxId16.text() != "" and idx16 != -1 and len(self.messages) > 0 and self.blnTraceSlot16 == True:
            self.leRxDlc16.setText(str(self.messages[idx16][1]))
            self.leRxD0_16.setText(str(self.messages[idx16][2]))
            self.leRxD1_16.setText(str(self.messages[idx16][3]))
            self.leRxD2_16.setText(str(self.messages[idx16][4]))
            self.leRxD3_16.setText(str(self.messages[idx16][5]))
            self.leRxD4_16.setText(str(self.messages[idx16][6]))
            self.leRxD5_16.setText(str(self.messages[idx16][7]))
            self.leRxD6_16.setText(str(self.messages[idx16][8]))
            self.leRxD7_16.setText(str(self.messages[idx16][9]))
            self.leRxPeriod16.setText(str(self.messages[idx16][10]))
            self.leRxCounter16.setText(str(self.messages[idx16][11]))
            # -----------------------------------------------------------------------
        idx17 = self.find_index(self.messages, str(self.leRxId17.text()))
        if self.leRxId17.text() != "" and idx16 != -1 and len(self.messages) > 0 and self.blnTraceSlot17 == True:
            self.leRxDlc17.setText(str(self.messages[idx17][1]))
            self.leRxD0_17.setText(str(self.messages[idx17][2]))
            self.leRxD1_17.setText(str(self.messages[idx17][3]))
            self.leRxD2_17.setText(str(self.messages[idx17][4]))
            self.leRxD3_17.setText(str(self.messages[idx17][5]))
            self.leRxD4_17.setText(str(self.messages[idx17][6]))
            self.leRxD5_17.setText(str(self.messages[idx17][7]))
            self.leRxD6_17.setText(str(self.messages[idx17][8]))
            self.leRxD7_17.setText(str(self.messages[idx17][9]))
            self.leRxPeriod17.setText(str(self.messages[idx17][10]))
            self.leRxCounter17.setText(str(self.messages[idx17][11]))
            # -----------------------------------------------------------------------
        idx18 = self.find_index(self.messages, str(self.leRxId18.text()))
        if self.leRxId18.text() != "" and idx18 != -1 and len(self.messages) > 0 and self.blnTraceSlot18 == True:
            self.leRxDlc18.setText(str(self.messages[idx18][1]))
            self.leRxD0_18.setText(str(self.messages[idx18][2]))
            self.leRxD1_18.setText(str(self.messages[idx18][3]))
            self.leRxD2_18.setText(str(self.messages[idx18][4]))
            self.leRxD3_18.setText(str(self.messages[idx18][5]))
            self.leRxD4_18.setText(str(self.messages[idx18][6]))
            self.leRxD5_18.setText(str(self.messages[idx18][7]))
            self.leRxD6_18.setText(str(self.messages[idx18][8]))
            self.leRxD7_18.setText(str(self.messages[idx18][9]))
            self.leRxPeriod18.setText(str(self.messages[idx18][10]))
            self.leRxCounter18.setText(str(self.messages[idx18][11]))
            # -----------------------------------------------------------------------
        idx19 = self.find_index(self.messages, str(self.leRxId19.text()))
        if self.leRxId19.text() != "" and idx19 != -1 and len(self.messages) > 0 and self.blnTraceSlot19 == True:
            self.leRxDlc19.setText(str(self.messages[idx19][1]))
            self.leRxD0_19.setText(str(self.messages[idx19][2]))
            self.leRxD1_19.setText(str(self.messages[idx19][3]))
            self.leRxD2_19.setText(str(self.messages[idx19][4]))
            self.leRxD3_19.setText(str(self.messages[idx19][5]))
            self.leRxD4_19.setText(str(self.messages[idx19][6]))
            self.leRxD5_19.setText(str(self.messages[idx19][7]))
            self.leRxD6_19.setText(str(self.messages[idx19][8]))
            self.leRxD7_19.setText(str(self.messages[idx19][9]))
            self.leRxPeriod19.setText(str(self.messages[idx19][10]))
            self.leRxCounter19.setText(str(self.messages[idx19][11]))
            # -----------------------------------------------------------------------
        idx20 = self.find_index(self.messages, str(self.leRxId20.text()))
        if self.leRxId20.text() != "" and idx20 != -1 and len(self.messages) > 0 and self.blnTraceSlot20 == True:
            self.leRxDlc20.setText(str(self.messages[idx20][1]))
            self.leRxD0_20.setText(str(self.messages[idx20][2]))
            self.leRxD1_20.setText(str(self.messages[idx20][3]))
            self.leRxD2_20.setText(str(self.messages[idx20][4]))
            self.leRxD3_20.setText(str(self.messages[idx20][5]))
            self.leRxD4_20.setText(str(self.messages[idx20][6]))
            self.leRxD5_20.setText(str(self.messages[idx20][7]))
            self.leRxD6_20.setText(str(self.messages[idx20][8]))
            self.leRxD7_20.setText(str(self.messages[idx20][9]))
            self.leRxPeriod20.setText(str(self.messages[idx20][10]))
            self.leRxCounter20.setText(str(self.messages[idx20][11]))

    def is_hex(self, s):
        try:
            int(s, 16)
            return True
        except ValueError:
            return False

    # ============================================================================================================
    # def qlineedit_hex_handler(self, qlineedit): # lambda method
    def qlineedit_hex_handler(self):
        # if self.is_hex(qlineedit.text()) == False:
        #     qlineedit.setStyleSheet("color: red;  background-color: white")
        # else:
        #     qlineedit.setStyleSheet("color: black;  background-color: white")

        sender = self.sender()
        print(sender)
        if self.is_hex(sender.text()) == False:
            sender.setStyleSheet("color: red;  background-color: white; font-weight: bold")
        else:
            sender.setStyleSheet("color: black;  background-color: white")

    def qlineedit_valid_dlc_handler(self):
        sender = self.sender()
        print(sender)
        qlineedit_text = str(sender.text())
        try:
            if float(qlineedit_text) > 8 or float(qlineedit_text) == 0 or qlineedit_text.isnumeric == True:
                sender.setStyleSheet("color: red;  background-color: white; font-weight: bold")
            else:
                sender.setStyleSheet("color: black;  background-color: white")
        except:
            sender.setStyleSheet("color: red;  background-color: white; font-weight: bold")

    def qlineedit_valid_period_handler(self):
        sender = self.sender()
        print(sender)
        qlineedit_text = str(sender.text())
        try:
            if float(qlineedit_text) > 99999 or float(qlineedit_text) < 0 or qlineedit_text.isnumeric == True:
                sender.setStyleSheet("color: red;  background-color: white; font-weight: bold")
            else:
                sender.setStyleSheet("color: black;  background-color: white")
        except:
            sender.setStyleSheet("color: red;  background-color: white; font-weight: bold")

    def set_tx_slot(self, strSlot, strID, strDlc, strD0, strD1, strD2, strD3, strD4, strD5, strD6, strD7, strPeriod):
        if strSlot == "1":
            self.leTxId01.setText(strID)
            self.leTxDlc01.setText(strDlc)
            self.leTxD0_01.setText(strD0)
            self.leTxD1_01.setText(strD1)
            self.leTxD2_01.setText(strD2)
            self.leTxD3_01.setText(strD3)
            self.leTxD4_01.setText(strD4)
            self.leTxD5_01.setText(strD5)
            self.leTxD6_01.setText(strD6)
            self.leTxD7_01.setText(strD7)
            self.leTxPeriod01.setText(strPeriod)

        elif strSlot == "2":
            self.leTxId02.setText(strID)
            self.leTxDlc02.setText(strDlc)
            self.leTxD0_02.setText(strD0)
            self.leTxD1_02.setText(strD1)
            self.leTxD2_02.setText(strD2)
            self.leTxD3_02.setText(strD3)
            self.leTxD4_02.setText(strD4)
            self.leTxD5_02.setText(strD5)
            self.leTxD6_02.setText(strD6)
            self.leTxD7_02.setText(strD7)
            self.leTxPeriod02.setText(strPeriod)

        elif strSlot == "3":
            self.leTxId03.setText(strID)
            self.leTxDlc03.setText(strDlc)
            self.leTxD0_03.setText(strD0)
            self.leTxD1_03.setText(strD1)
            self.leTxD2_03.setText(strD2)
            self.leTxD3_03.setText(strD3)
            self.leTxD4_03.setText(strD4)
            self.leTxD5_03.setText(strD5)
            self.leTxD6_03.setText(strD6)
            self.leTxD7_03.setText(strD7)
            self.leTxPeriod03.setText(strPeriod)

        elif strSlot == "4":
            self.leTxId04.setText(strID)
            self.leTxDlc04.setText(strDlc)
            self.leTxD0_04.setText(strD0)
            self.leTxD1_04.setText(strD1)
            self.leTxD2_04.setText(strD2)
            self.leTxD3_04.setText(strD3)
            self.leTxD4_04.setText(strD4)
            self.leTxD5_04.setText(strD5)
            self.leTxD6_04.setText(strD6)
            self.leTxD7_04.setText(strD7)
            self.leTxPeriod04.setText(strPeriod)

        elif strSlot == "5":
            self.leTxId05.setText(strID)
            self.leTxDlc05.setText(strDlc)
            self.leTxD0_05.setText(strD0)
            self.leTxD1_05.setText(strD1)
            self.leTxD2_05.setText(strD2)
            self.leTxD3_05.setText(strD3)
            self.leTxD4_05.setText(strD4)
            self.leTxD5_05.setText(strD5)
            self.leTxD6_05.setText(strD6)
            self.leTxD7_05.setText(strD7)
            self.leTxPeriod05.setText(strPeriod)

        elif strSlot == "6":
            self.leTxId06.setText(strID)
            self.leTxDlc06.setText(strDlc)
            self.leTxD0_06.setText(strD0)
            self.leTxD1_06.setText(strD1)
            self.leTxD2_06.setText(strD2)
            self.leTxD3_06.setText(strD3)
            self.leTxD4_06.setText(strD4)
            self.leTxD5_06.setText(strD5)
            self.leTxD6_06.setText(strD6)
            self.leTxD7_06.setText(strD7)
            self.leTxPeriod06.setText(strPeriod)

        elif strSlot == "7":
            self.leTxId07.setText(strID)
            self.leTxDlc07.setText(strDlc)
            self.leTxD0_07.setText(strD0)
            self.leTxD1_07.setText(strD1)
            self.leTxD2_07.setText(strD2)
            self.leTxD3_07.setText(strD3)
            self.leTxD4_07.setText(strD4)
            self.leTxD5_07.setText(strD5)
            self.leTxD6_07.setText(strD6)
            self.leTxD7_07.setText(strD7)
            self.leTxPeriod07.setText(strPeriod)

        elif strSlot == "8":
            self.leTxId08.setText(strID)
            self.leTxDlc08.setText(strDlc)
            self.leTxD0_08.setText(strD0)
            self.leTxD1_08.setText(strD1)
            self.leTxD2_08.setText(strD2)
            self.leTxD3_08.setText(strD3)
            self.leTxD4_08.setText(strD4)
            self.leTxD5_08.setText(strD5)
            self.leTxD6_08.setText(strD6)
            self.leTxD7_08.setText(strD7)
            self.leTxPeriod08.setText(strPeriod)

        elif strSlot == "9":
            self.leTxId09.setText(strID)
            self.leTxDlc09.setText(strDlc)
            self.leTxD0_09.setText(strD0)
            self.leTxD1_09.setText(strD1)
            self.leTxD2_09.setText(strD2)
            self.leTxD3_09.setText(strD3)
            self.leTxD4_09.setText(strD4)
            self.leTxD5_09.setText(strD5)
            self.leTxD6_09.setText(strD6)
            self.leTxD7_09.setText(strD7)
            self.leTxPeriod09.setText(strPeriod)

        elif strSlot == "10":
            self.leTxId10.setText(strID)
            self.leTxDlc10.setText(strDlc)
            self.leTxD0_10.setText(strD0)
            self.leTxD1_10.setText(strD1)
            self.leTxD2_10.setText(strD2)
            self.leTxD3_10.setText(strD3)
            self.leTxD4_10.setText(strD4)
            self.leTxD5_10.setText(strD5)
            self.leTxD6_10.setText(strD6)
            self.leTxD7_10.setText(strD7)
            self.leTxPeriod10.setText(strPeriod)

        elif strSlot == "11":
            self.leTxId11.setText(strID)
            self.leTxDlc11.setText(strDlc)
            self.leTxD0_11.setText(strD0)
            self.leTxD1_11.setText(strD1)
            self.leTxD2_11.setText(strD2)
            self.leTxD3_11.setText(strD3)
            self.leTxD4_11.setText(strD4)
            self.leTxD5_11.setText(strD5)
            self.leTxD6_11.setText(strD6)
            self.leTxD7_11.setText(strD7)
            self.leTxPeriod11.setText(strPeriod)

        elif strSlot == "12":
            self.leTxId12.setText(strID)
            self.leTxDlc12.setText(strDlc)
            self.leTxD0_12.setText(strD0)
            self.leTxD1_12.setText(strD1)
            self.leTxD2_12.setText(strD2)
            self.leTxD3_12.setText(strD3)
            self.leTxD4_12.setText(strD4)
            self.leTxD5_12.setText(strD5)
            self.leTxD6_12.setText(strD6)
            self.leTxD7_12.setText(strD7)
            self.leTxPeriod12.setText(strPeriod)

        elif strSlot == "13":
            self.leTxId13.setText(strID)
            self.leTxDlc13.setText(strDlc)
            self.leTxD0_13.setText(strD0)
            self.leTxD1_13.setText(strD1)
            self.leTxD2_13.setText(strD2)
            self.leTxD3_13.setText(strD3)
            self.leTxD4_13.setText(strD4)
            self.leTxD5_13.setText(strD5)
            self.leTxD6_13.setText(strD6)
            self.leTxD7_13.setText(strD7)
            self.leTxPeriod13.setText(strPeriod)

        elif strSlot == "14":
            self.leTxId14.setText(strID)
            self.leTxDlc14.setText(strDlc)
            self.leTxD0_14.setText(strD0)
            self.leTxD1_14.setText(strD1)
            self.leTxD2_14.setText(strD2)
            self.leTxD3_14.setText(strD3)
            self.leTxD4_14.setText(strD4)
            self.leTxD5_14.setText(strD5)
            self.leTxD6_14.setText(strD6)
            self.leTxD7_14.setText(strD7)
            self.leTxPeriod14.setText(strPeriod)

        elif strSlot == "15":
            self.leTxId15.setText(strID)
            self.leTxDlc15.setText(strDlc)
            self.leTxD0_15.setText(strD0)
            self.leTxD1_15.setText(strD1)
            self.leTxD2_15.setText(strD2)
            self.leTxD3_15.setText(strD3)
            self.leTxD4_15.setText(strD4)
            self.leTxD5_15.setText(strD5)
            self.leTxD6_15.setText(strD6)
            self.leTxD7_15.setText(strD7)
            self.leTxPeriod15.setText(strPeriod)

        elif strSlot == "16":
            self.leTxId16.setText(strID)
            self.leTxDlc16.setText(strDlc)
            self.leTxD0_16.setText(strD0)
            self.leTxD1_16.setText(strD1)
            self.leTxD2_16.setText(strD2)
            self.leTxD3_16.setText(strD3)
            self.leTxD4_16.setText(strD4)
            self.leTxD5_16.setText(strD5)
            self.leTxD6_16.setText(strD6)
            self.leTxD7_16.setText(strD7)
            self.leTxPeriod16.setText(strPeriod)

        elif strSlot == "17":
            self.leTxId17.setText(strID)
            self.leTxDlc17.setText(strDlc)
            self.leTxD0_17.setText(strD0)
            self.leTxD1_17.setText(strD1)
            self.leTxD2_17.setText(strD2)
            self.leTxD3_17.setText(strD3)
            self.leTxD4_17.setText(strD4)
            self.leTxD5_17.setText(strD5)
            self.leTxD6_17.setText(strD6)
            self.leTxD7_17.setText(strD7)
            self.leTxPeriod17.setText(strPeriod)

        elif strSlot == "18":
            self.leTxId18.setText(strID)
            self.leTxDlc18.setText(strDlc)
            self.leTxD0_18.setText(strD0)
            self.leTxD1_18.setText(strD1)
            self.leTxD2_18.setText(strD2)
            self.leTxD3_18.setText(strD3)
            self.leTxD4_18.setText(strD4)
            self.leTxD5_18.setText(strD5)
            self.leTxD6_18.setText(strD6)
            self.leTxD7_18.setText(strD7)
            self.leTxPeriod18.setText(strPeriod)

        elif strSlot == "19":
            self.leTxId19.setText(strID)
            self.leTxDlc19.setText(strDlc)
            self.leTxD0_19.setText(strD0)
            self.leTxD1_19.setText(strD1)
            self.leTxD2_19.setText(strD2)
            self.leTxD3_19.setText(strD3)
            self.leTxD4_19.setText(strD4)
            self.leTxD5_19.setText(strD5)
            self.leTxD6_19.setText(strD6)
            self.leTxD7_19.setText(strD7)
            self.leTxPeriod19.setText(strPeriod)

        elif strSlot == "20":
            self.leTxId20.setText(strID)
            self.leTxDlc20.setText(strDlc)
            self.leTxD0_20.setText(strD0)
            self.leTxD1_20.setText(strD1)
            self.leTxD2_20.setText(strD2)
            self.leTxD3_20.setText(strD3)
            self.leTxD4_20.setText(strD4)
            self.leTxD5_20.setText(strD5)
            self.leTxD6_20.setText(strD6)
            self.leTxD7_20.setText(strD7)
            self.leTxPeriod20.setText(strPeriod)

    def btn_clear_click_handler(self):
        self.leTxId01.setText("")
        self.leTxId02.setText("")
        self.leTxId03.setText("")
        self.leTxId04.setText("")
        self.leTxId05.setText("")
        self.leTxId06.setText("")
        self.leTxId07.setText("")
        self.leTxId08.setText("")
        self.leTxId09.setText("")
        self.leTxId10.setText("")
        self.leTxId11.setText("")
        self.leTxId12.setText("")
        self.leTxId13.setText("")
        self.leTxId14.setText("")
        self.leTxId15.setText("")
        self.leTxId16.setText("")
        self.leTxId17.setText("")
        self.leTxId18.setText("")
        self.leTxId19.setText("")
        self.leTxId20.setText("")
        # -----------------------
        self.leTxDlc01.setText("")
        self.leTxDlc02.setText("")
        self.leTxDlc03.setText("")
        self.leTxDlc04.setText("")
        self.leTxDlc05.setText("")
        self.leTxDlc06.setText("")
        self.leTxDlc07.setText("")
        self.leTxDlc08.setText("")
        self.leTxDlc09.setText("")
        self.leTxDlc10.setText("")
        self.leTxDlc11.setText("")
        self.leTxDlc12.setText("")
        self.leTxDlc13.setText("")
        self.leTxDlc14.setText("")
        self.leTxDlc15.setText("")
        self.leTxDlc16.setText("")
        self.leTxDlc17.setText("")
        self.leTxDlc18.setText("")
        self.leTxDlc19.setText("")
        self.leTxDlc20.setText("")
        # ------------------------
        self.leTxD0_01.setText("")
        self.leTxD0_02.setText("")
        self.leTxD0_03.setText("")
        self.leTxD0_04.setText("")
        self.leTxD0_05.setText("")
        self.leTxD0_06.setText("")
        self.leTxD0_07.setText("")
        self.leTxD0_08.setText("")
        self.leTxD0_09.setText("")
        self.leTxD0_10.setText("")
        self.leTxD0_11.setText("")
        self.leTxD0_12.setText("")
        self.leTxD0_13.setText("")
        self.leTxD0_14.setText("")
        self.leTxD0_15.setText("")
        self.leTxD0_16.setText("")
        self.leTxD0_17.setText("")
        self.leTxD0_18.setText("")
        self.leTxD0_19.setText("")
        self.leTxD0_20.setText("")
        # ------------------------
        self.leTxD1_01.setText("")
        self.leTxD1_02.setText("")
        self.leTxD1_03.setText("")
        self.leTxD1_04.setText("")
        self.leTxD1_05.setText("")
        self.leTxD1_06.setText("")
        self.leTxD1_07.setText("")
        self.leTxD1_08.setText("")
        self.leTxD1_09.setText("")
        self.leTxD1_10.setText("")
        self.leTxD1_11.setText("")
        self.leTxD1_12.setText("")
        self.leTxD1_13.setText("")
        self.leTxD1_14.setText("")
        self.leTxD1_15.setText("")
        self.leTxD1_16.setText("")
        self.leTxD1_17.setText("")
        self.leTxD1_18.setText("")
        self.leTxD1_19.setText("")
        self.leTxD1_20.setText("")
        # ------------------------
        self.leTxD2_01.setText("")
        self.leTxD2_02.setText("")
        self.leTxD2_03.setText("")
        self.leTxD2_04.setText("")
        self.leTxD2_05.setText("")
        self.leTxD2_06.setText("")
        self.leTxD2_07.setText("")
        self.leTxD2_08.setText("")
        self.leTxD2_09.setText("")
        self.leTxD2_10.setText("")
        self.leTxD2_11.setText("")
        self.leTxD2_12.setText("")
        self.leTxD2_13.setText("")
        self.leTxD2_14.setText("")
        self.leTxD2_15.setText("")
        self.leTxD2_16.setText("")
        self.leTxD2_17.setText("")
        self.leTxD2_18.setText("")
        self.leTxD2_19.setText("")
        self.leTxD2_20.setText("")
        # ------------------------
        self.leTxD3_01.setText("")
        self.leTxD3_02.setText("")
        self.leTxD3_03.setText("")
        self.leTxD3_04.setText("")
        self.leTxD3_05.setText("")
        self.leTxD3_06.setText("")
        self.leTxD3_07.setText("")
        self.leTxD3_08.setText("")
        self.leTxD3_09.setText("")
        self.leTxD3_10.setText("")
        self.leTxD3_11.setText("")
        self.leTxD3_12.setText("")
        self.leTxD3_13.setText("")
        self.leTxD3_14.setText("")
        self.leTxD3_15.setText("")
        self.leTxD3_16.setText("")
        self.leTxD3_17.setText("")
        self.leTxD3_18.setText("")
        self.leTxD3_19.setText("")
        self.leTxD3_20.setText("")
        # ------------------------
        self.leTxD4_01.setText("")
        self.leTxD4_02.setText("")
        self.leTxD4_03.setText("")
        self.leTxD4_04.setText("")
        self.leTxD4_05.setText("")
        self.leTxD4_06.setText("")
        self.leTxD4_07.setText("")
        self.leTxD4_08.setText("")
        self.leTxD4_09.setText("")
        self.leTxD4_10.setText("")
        self.leTxD4_11.setText("")
        self.leTxD4_12.setText("")
        self.leTxD4_13.setText("")
        self.leTxD4_14.setText("")
        self.leTxD4_15.setText("")
        self.leTxD4_16.setText("")
        self.leTxD4_17.setText("")
        self.leTxD4_18.setText("")
        self.leTxD4_19.setText("")
        self.leTxD4_20.setText("")
        # ------------------------
        self.leTxD5_01.setText("")
        self.leTxD5_02.setText("")
        self.leTxD5_03.setText("")
        self.leTxD5_04.setText("")
        self.leTxD5_05.setText("")
        self.leTxD5_06.setText("")
        self.leTxD5_07.setText("")
        self.leTxD5_08.setText("")
        self.leTxD5_09.setText("")
        self.leTxD5_10.setText("")
        self.leTxD5_11.setText("")
        self.leTxD5_12.setText("")
        self.leTxD5_13.setText("")
        self.leTxD5_14.setText("")
        self.leTxD5_15.setText("")
        self.leTxD5_16.setText("")
        self.leTxD5_17.setText("")
        self.leTxD5_18.setText("")
        self.leTxD5_19.setText("")
        self.leTxD5_20.setText("")
        # ------------------------
        self.leTxD6_01.setText("")
        self.leTxD6_02.setText("")
        self.leTxD6_03.setText("")
        self.leTxD6_04.setText("")
        self.leTxD6_05.setText("")
        self.leTxD6_06.setText("")
        self.leTxD6_07.setText("")
        self.leTxD6_08.setText("")
        self.leTxD6_09.setText("")
        self.leTxD6_10.setText("")
        self.leTxD6_11.setText("")
        self.leTxD6_12.setText("")
        self.leTxD6_13.setText("")
        self.leTxD6_14.setText("")
        self.leTxD6_15.setText("")
        self.leTxD6_16.setText("")
        self.leTxD6_17.setText("")
        self.leTxD6_18.setText("")
        self.leTxD6_19.setText("")
        self.leTxD6_20.setText("")
        # ------------------------
        self.leTxD7_01.setText("")
        self.leTxD7_02.setText("")
        self.leTxD7_03.setText("")
        self.leTxD7_04.setText("")
        self.leTxD7_05.setText("")
        self.leTxD7_06.setText("")
        self.leTxD7_07.setText("")
        self.leTxD7_08.setText("")
        self.leTxD7_09.setText("")
        self.leTxD7_10.setText("")
        self.leTxD7_11.setText("")
        self.leTxD7_12.setText("")
        self.leTxD7_13.setText("")
        self.leTxD7_14.setText("")
        self.leTxD7_15.setText("")
        self.leTxD7_16.setText("")
        self.leTxD7_17.setText("")
        self.leTxD7_18.setText("")
        self.leTxD7_19.setText("")
        self.leTxD7_20.setText("")
        # ------------------------
        self.leTxPeriod01.setText("")
        self.leTxPeriod02.setText("")
        self.leTxPeriod03.setText("")
        self.leTxPeriod04.setText("")
        self.leTxPeriod05.setText("")
        self.leTxPeriod06.setText("")
        self.leTxPeriod07.setText("")
        self.leTxPeriod08.setText("")
        self.leTxPeriod09.setText("")
        self.leTxPeriod10.setText("")
        self.leTxPeriod11.setText("")
        self.leTxPeriod12.setText("")
        self.leTxPeriod13.setText("")
        self.leTxPeriod14.setText("")
        self.leTxPeriod15.setText("")
        self.leTxPeriod16.setText("")
        self.leTxPeriod17.setText("")
        self.leTxPeriod18.setText("")
        self.leTxPeriod19.setText("")
        self.leTxPeriod20.setText("")

    def btn_set_tpms_slot_handler(self):
        sD0 = ""
        sD1 = ""
        sD2 = ""
        sD3 = ""
        sD4 = ""
        sD5 = ""
        sD6 = ""
        sD7 = ""

        sHexD0 = ""
        sHexD1 = ""
        sHexD2 = ""
        sHexD3 = ""
        sHexD4 = ""
        sHexD5 = ""
        sHexD6 = ""
        sHexD7 = ""

        TpmsSystemStatus = ""
        TpmsTireId = ""
        TpmsTireInfo = ""

        TpmsTireLeakage = ""
        TpmsLearningStatus = ""
        TpmsTirePressureStatus = ""
        TpmsTireTempratureStatus = ""
        TpmsTirePressure = "00000000"
        TpmsTireTemprature = "00000000"
        TpmsTireBatteryPowerStatus = ""

        print("current Index: ", str(self.cmbTpmsSystemStatus.currentIndex()))

        # TPMS System Status
        if self.cmbTpmsSystemStatus.currentIndex() == 0:
            print("TPMS System Normal")
            TpmsSystemStatus = "000"
        elif self.cmbTpmsSystemStatus.currentIndex() == 1:
            print("TPMS System Error")
            TpmsSystemStatus = "010"
        # --------------------------------------------------------
        # TPMS Tire ID
        TpmsTireId = "000"  # Default Rear Right Tire
        # --------------------------------------------------------
        # TPMS valid/invalid Info
        if self.cmbTireInformationSignal.currentIndex() == 0:
            print("Tire information is Normal")
            TpmsTireInfo = "0"
        elif self.cmbTireInformationSignal.currentIndex() == 1:
            print("Tire information is not normal")
            TpmsTireInfo = "1"
        # --------------------------------------------------------
        sD0 = TpmsTireInfo + TpmsTireId + "0" + TpmsSystemStatus
        print("D0: ", sD0)
        # --------------------------------------------------------
        # TPMS Tire Leakaging
        if self.cmbTireLeakage.currentIndex() == 0:
            print("Tire Leakage normal")
            TpmsTireLeakage = "00"

        elif self.cmbTireLeakage.currentIndex() == 1:
            print("Tire Quick Leak")
            TpmsTireLeakage = "01"
        # --------------------------------------------------------
        # TPMS Tire Learning Status
        if self.cmbTireLearningStatus.currentIndex() == 0:
            print("Not Learned")
            TpmsLearningStatus = "00"
        elif self.cmbTireLearningStatus.currentIndex() == 1:
            print("Learning")
            TpmsLearningStatus = "01"
        elif self.cmbTireLearningStatus.currentIndex() == 2:
            print("Learning Completed")
            TpmsLearningStatus = "10"
        elif self.cmbTireLearningStatus.currentIndex() == 3:
            print("Learning Failure")
            TpmsLearningStatus = "11"
        # --------------------------------------------------------
        # TPMS Tire Pressure Status
        if self.cmbTirePressureStatus.currentIndex() == 0:
            print("Pressure Normal")
            TpmsTirePressureStatus = "00"
        elif self.cmbTirePressureStatus.currentIndex() == 1:
            print("Over Pressure")
            TpmsTirePressureStatus = "01"
        elif self.cmbTirePressureStatus.currentIndex() == 2:
            print("Under Pressure")
            TpmsTirePressureStatus = "10"
        # --------------------------------------------------------
        # TPMS Tire Temprature Status
        if self.cmbTireTempratureStatus.currentIndex() == 0:
            print("Tire temperature normal")
            TpmsTireTempratureStatus = "00"
        elif self.cmbTireTempratureStatus.currentIndex() == 1:
            print("Tire temperature high")
            TpmsTireTempratureStatus = "10"

        # --------------------------------------------------------
        sD1 = TpmsTireTempratureStatus + TpmsTirePressureStatus + TpmsLearningStatus + TpmsTireLeakage
        # --------------------------------------------------------
        sD2 = TpmsTirePressure
        # --------------------------------------------------------
        sD3 = TpmsTireTemprature
        # --------------------------------------------------------
        sD4 = "00000000"
        # --------------------------------------------------------
        # TPMS Tire Battery Power status
        if self.cmbTireBatteryPowerStatus.currentIndex() == 0:
            print("Tire Battery Power Normal")
            TpmsTireBatteryPowerStatus = "00"
        elif self.cmbTireBatteryPowerStatus.currentIndex() == 1:
            print("Tire Battery Power Low")
            TpmsTireBatteryPowerStatus = "01"

        # --------------------------------------------------------
        sD5 = "000000" + TpmsTireBatteryPowerStatus
        sD6 = "00000000"
        sD7 = "00000000"
        # --------------------------------------------------------
        sHexD0 = format(int(sD0, 2), '02x')
        sHexD1 = format(int(sD1, 2), '02x')
        sHexD2 = format(int(sD2, 2), '02x')
        sHexD3 = format(int(sD3, 2), '02x')
        sHexD4 = format(int(sD4, 2), '02x')
        sHexD5 = format(int(sD5, 2), '02x')
        sHexD6 = format(int(sD6, 2), '02x')
        sHexD7 = format(int(sD7, 2), '02x')

        print("************************************")
        print("D0: ", sD0, int(sD0, 2), sHexD0)
        print("D1: ", sD1, int(sD1, 2), sHexD1)
        print("D2: ", sD2, int(sD2, 2), sHexD2)
        print("D3: ", sD3, int(sD3, 2), sHexD3)
        print("D4: ", sD4, int(sD4, 2), sHexD4)
        print("D5: ", sD5, int(sD5, 2), sHexD5)
        print("D6: ", sD6, int(sD6, 2), sHexD6)
        print("D7: ", sD7, int(sD7, 2), sHexD7)
        print("************************************")

        self.set_tx_slot(str(self.cmbTpmsSlot.currentIndex() + 1),
                         "40F",
                         "6",
                         sHexD0.upper(),
                         sHexD1.upper(),
                         sHexD2.upper(),
                         sHexD3.upper(),
                         sHexD4.upper(),
                         sHexD5.upper(),
                         sHexD6.upper(),
                         sHexD7.upper(),
                         "100")

        if self.chkAutoTransmit.isChecked():
            self.auto_transmit_slot_no = self.cmbTpmsSlot.currentIndex() + 1

    def btn_cbm_ems_info8_click_handler(self):
        sD0 = ""
        sD1 = ""
        sD2 = ""
        sD3 = ""
        sD4 = ""
        sD5 = ""
        sD6 = ""
        sD7 = ""

        sHexD0 = ""
        sHexD1 = ""
        sHexD2 = ""
        sHexD3 = ""
        sHexD4 = ""
        sHexD5 = ""
        sHexD6 = ""
        sHexD7 = ""

        # Fuel Consumption Signal
        sD0 = "00000000"
        sD1 = "00000000"
        sHexD0 = format(int(sD0, 2), '02x')
        sHexD1 = format(int(sD1, 2), '02x')
        print("sHexD0", sHexD0)
        print("sHexD1", sHexD1)
        # --------------------------------------------------------
        # Engine Volume
        if self.leEngineVolume.text() == "":
            self.leEngineVolume.setText("25.5")

        if float(self.leEngineVolume.text()) > 25.5:
            self.leEngineVolume.setText("25.5")

        intEngineVolume = int(float(self.leEngineVolume.text()) * 10)
        sHexEngineVolume = format(intEngineVolume, '02x')

        # print("Int Engine Volume", str(intEngineVolume))
        # print("Hex Engine Volume", sHexEngineVolume)
        sHexD2 = sHexEngineVolume
        print("sHexD2", sHexD2)
        # --------------------------------------------------------
        # Engine Characteristic
        if self.cmbEngineCharacteristic.currentIndex() == 0:  # Gasoline, No ETC
            print("Gasoline, No ETC")
            EngineCharacteristic = "000"
        elif self.cmbEngineCharacteristic.currentIndex() == 1:  # LPG, No ETC
            print("LPG, No ETC")
            EngineCharacteristic = "001"
        elif self.cmbEngineCharacteristic.currentIndex() == 2:  # Diesel, No ETC
            print("Diesel, No ETC")
            EngineCharacteristic = "010"
        elif self.cmbEngineCharacteristic.currentIndex() == 3:  # Gasoline, ETC
            print("Gasoline, ETC")
            EngineCharacteristic = "100"
        elif self.cmbEngineCharacteristic.currentIndex() == 4:  # LPG, ETC
            print("LPG, ETC")
            EngineCharacteristic = "101"
        elif self.cmbEngineCharacteristic.currentIndex() == 5:  # Diesel, ETC
            print("Diesel, ETC")
            EngineCharacteristic = "110"
        # --------------------------------------------------------
        # Transmission Type
        if self.cmbTransmissionType.currentIndex() == 0:  # AT
            print("AT")
            TransmissionType = "00"
        elif self.cmbTransmissionType.currentIndex() == 1:  # MT
            print("MT")
            TransmissionType = "01"
        elif self.cmbTransmissionType.currentIndex() == 2:  # CVT
            print("CVT")
            TransmissionType = "10"
        elif self.cmbTransmissionType.currentIndex() == 3:  # DCT
            print("DCT")
            TransmissionType = "11"
        # --------------------------------------------------------
        sD3 = "000" + TransmissionType + EngineCharacteristic
        sHexD3 = format(int(sD3, 2), '02x')
        print("sHexD3", sHexD3)
        # --------------------------------------------------------
        # Desired Gear Information
        DesiredGearInformation = ""
        if self.cmbDesiredGearInformation.currentIndex() == 0:  # No Action
            print("No Action")
            DesiredGearInformation = "00"
        elif self.cmbDesiredGearInformation.currentIndex() == 1:  # Increase
            print("Increase")
            DesiredGearInformation = "01"
        elif self.cmbDesiredGearInformation.currentIndex() == 2:  # Decrease
            print("Decrease")
            DesiredGearInformation = "10"
        elif self.cmbDesiredGearInformation.currentIndex() == 3:  # Not Available
            print("Not Available")
            DesiredGearInformation = "11"
        # --------------------------------------------------------
        # Engaged Gear Indicator
        EngagedGearIndicator = ""
        if self.cmbEngagedGearIndicator.currentIndex() == 0:  # N
            print("")
            EngagedGearIndicator = "000"
        elif self.cmbEngagedGearIndicator.currentIndex() == 1:  # 1
            print("")
            EngagedGearIndicator = "001"
        elif self.cmbEngagedGearIndicator.currentIndex() == 2:  # 2
            print("")
            EngagedGearIndicator = "010"
        elif self.cmbEngagedGearIndicator.currentIndex() == 3:  # 3
            print("")
            EngagedGearIndicator = "011"
        elif self.cmbEngagedGearIndicator.currentIndex == 4:  # 4
            print("")
            EngagedGearIndicator = "100"
        elif self.cmbEngagedGearIndicator.currentIndex == 5:  # 5
            print("")
            EngagedGearIndicator = "101"
        elif self.cmbEngagedGearIndicator.currentIndex == 6:  # Not Available
            print("")
            EngagedGearIndicator = "110"
        # --------------------------------------------------------
        sD4 = "0" + EngagedGearIndicator + "0" + DesiredGearInformation + "0"
        sHexD4 = format(int(sD4, 2), '02x')
        print("sHexD4", sHexD4)
        # --------------------------------------------------------
        sD5 = "00000000"
        sHexD5 = format(int(sD5, 2), '02x')
        print("sHexD5", sHexD5)
        # --------------------------------------------------------
        sD6 = "00000000"
        sHexD6 = format(int(sD6, 2), '02x')
        print("sHexD6", sHexD6)
        # --------------------------------------------------------
        sD7 = "00000000"
        sHexD7 = format(int(sD7, 2), '02x')
        print("sHexD7", sHexD7)
        # --------------------------------------------------------
        self.set_tx_slot(str(self.cmbCbmEmsInfo8Slot.currentIndex() + 1),
                         "4C3",
                         "8",
                         sHexD0.upper(),
                         sHexD1.upper(),
                         sHexD2.upper(),
                         sHexD3.upper(),
                         sHexD4.upper(),
                         sHexD5.upper(),
                         sHexD6.upper(),
                         sHexD7.upper(),
                         "100")

        if self.chkAutoTransmit.isChecked():
            self.auto_transmit_slot_no = self.cmbCbmEmsInfo8Slot.currentIndex() + 1

    def btn_high_speed_info3_click_handler(self):
        sD0 = ""
        sD1 = ""
        sD2 = ""
        sD3 = ""
        sD4 = ""
        sD5 = ""
        sD6 = ""
        sD7 = ""

        sHexD0 = ""
        sHexD1 = ""
        sHexD2 = ""
        sHexD3 = ""
        sHexD4 = ""
        sHexD5 = ""
        sHexD6 = ""
        sHexD7 = ""
        # --------------------------------------------------------
        LHIndicatorSwitchStatus = "0"
        if self.chkLHIndicatorSwitchStatus.isChecked():  # [0.0]
            LHIndicatorSwitchStatus = "1"
        else:
            LHIndicatorSwitchStatus = "0"
        # --------------------------------------------------------
        RHIndicatorSwitchStatus = "0"
        if self.chkRHIndicatorSwitchStatus.isChecked():  # [0.1]
            RHIndicatorSwitchStatus = "1"
        else:
            RHIndicatorSwitchStatus = "0"
        # --------------------------------------------------------
        SideLampSwitchStatus = "0"
        if self.chkSideLampSwitchStatus.isChecked():  # [0.2]
            SideLampSwitchStatus = "1"
        else:
            SideLampSwitchStatus = "0"
        # --------------------------------------------------------
        DippedLampSwitchStatus = "0"
        if self.chkDippedLampSwitchStatus.isChecked():  # [0.3]
            DippedLampSwitchStatus = "1"
        else:
            DippedLampSwitchStatus = "0"
        # --------------------------------------------------------
        MainLampSwitchStatus = "0"
        if self.chkMainLampSwitchStatus.isChecked():  # [0.4]
            MainLampSwitchStatus = "1"
        else:
            MainLampSwitchStatus = "0"
        # --------------------------------------------------------
        FrontFogLampSwitchStatus = "0"
        if self.chkFrontFogLampSwitchStatus.isChecked():  # [0.5]
            FrontFogLampSwitchStatus = "1"
        else:
            FrontFogLampSwitchStatus = "0"
        # --------------------------------------------------------
        RearFogLampSwitchStatus = "0"
        if self.chkRearFogLampSwitchStatus.isChecked():  # [0.6]
            RearFogLampSwitchStatus = "1"
        else:
            RearFogLampSwitchStatus = "0"
        # --------------------------------------------------------
        HornSwitchStatus = "0"
        if self.chkHornSwitchStatus.isChecked():  # [0.7]
            HornSwitchStatus = "1"
        else:
            HornSwitchStatus = "0"
        # --------------------------------------------------------
        sD0 = (HornSwitchStatus +
               RearFogLampSwitchStatus +
               FrontFogLampSwitchStatus +
               MainLampSwitchStatus +
               DippedLampSwitchStatus +
               SideLampSwitchStatus +
               RHIndicatorSwitchStatus +
               LHIndicatorSwitchStatus)

        print(sD0)
        sHexD0 = format(int(sD0, 2), '02x')
        print("sHexD0", sHexD0)
        # --------------------------------------------------------
        FrontLHDoorSwitchStatus = "0"
        if self.chkFrontLHDoorSwitchStatus.isChecked():  # [1.0]
            FrontLHDoorSwitchStatus = "1"
        else:
            FrontLHDoorSwitchStatus = "0"
        # --------------------------------------------------------
        FrontRHDoorSwitchStatus = "0"
        if self.chkFrontRHDoorSwitchStatus.isChecked():  # [1.1]
            FrontRHDoorSwitchStatus = "1"
        else:
            FrontRHDoorSwitchStatus = "0"
        # --------------------------------------------------------
        RearLHDoorSwitchStatus = "0"
        if self.chkRearLHDoorSwitchStatus.isChecked():  # [1.2]
            RearLHDoorSwitchStatus = "1"
        else:
            RearLHDoorSwitchStatus = "0"
        # --------------------------------------------------------
        RearRHDoorSwitchStatus = "0"
        if self.chkRearRHDoorSwitchStatus.isChecked():  # [1.3]
            RearRHDoorSwitchStatus = "1"
        else:
            RearRHDoorSwitchStatus = "0"
        # --------------------------------------------------------
        TrunkLidSwitchStatus = "0"
        if self.chkTrunkLidSwitchStatus.isChecked():  # [1.4]
            TrunkLidSwitchStatus = "1"
        else:
            TrunkLidSwitchStatus = "0"
        # --------------------------------------------------------
        BonnetSwitchStatus = "0"
        if self.chkBonnetSwitchStatus.isChecked():  # [1.5]
            BonnetSwitchStatus = "1"
        else:
            BonnetSwitchStatus = "0"
        # --------------------------------------------------------
        AutoLockBySpeedStatus = "0"
        if self.chkAutoLockBySpeedStatus.isChecked():  # [1.6]
            AutoLockBySpeedStatus = "1"
        else:
            AutoLockBySpeedStatus = "0"
        # --------------------------------------------------------
        sD1 = ("0" +
               AutoLockBySpeedStatus +
               BonnetSwitchStatus +
               TrunkLidSwitchStatus +
               RearRHDoorSwitchStatus +
               RearLHDoorSwitchStatus +
               FrontRHDoorSwitchStatus +
               FrontLHDoorSwitchStatus)
        print(sD1)
        sHexD1 = format(int(sD1, 2), '02x')
        print("sHexD1", sHexD1)
        # --------------------------------------------------------
        WashPumpSwitchStatus = "0"
        if self.chkWashPumpSwitchStatus.isChecked():  # [2.0]
            WashPumpSwitchStatus = "1"
        else:
            WashPumpSwitchStatus = "0"
        # --------------------------------------------------------
        WiperINTSwitchStatus = "0"
        if self.chkWiperINTSwitchStatus.isChecked():  # [2.1]
            WiperINTSwitchStatus = "1"
        else:
            WiperINTSwitchStatus = "0"
        # --------------------------------------------------------
        LowSpeedSwitchStatus = "0"
        if self.chkLowSpeedSwitchStatus.isChecked():  # [2.2]
            LowSpeedSwitchStatus = "1"
        else:
            LowSpeedSwitchStatus = "0"
        # --------------------------------------------------------
        WiperHighSpeedSwitchStatus = "0"
        if self.chkWiperHighSpeedSwitchStatus.isChecked():  # [2.3]
            WiperHighSpeedSwitchStatus = "1"
        else:
            WiperHighSpeedSwitchStatus = "0"
        # --------------------------------------------------------
        WiperAutoStopSwitchStatus = "0"
        if self.chkWiperAutoStopSwitchStatus.isChecked():  # [2.4]
            WiperAutoStopSwitchStatus = "1"
        else:
            WiperAutoStopSwitchStatus = "0"
        # --------------------------------------------------------
        RearWiperSwitchStatus = "0"
        if self.chkRearWiperSwitchStatus.isChecked():  # [2.5]
            RearWiperSwitchStatus = "1"
        else:
            RearWiperSwitchStatus = "0"
        # --------------------------------------------------------
        RearWashPumpSwitchStatus = "0"
        if self.chkRearWashPumpSwitchStatus.isChecked():  # [2.7]
            RearWashPumpSwitchStatus = "1"
        else:
            RearWashPumpSwitchStatus = "0"
        # --------------------------------------------------------
        sD2 = (RearWashPumpSwitchStatus +
               "0" +
               RearWiperSwitchStatus +
               WiperAutoStopSwitchStatus +
               WiperHighSpeedSwitchStatus +
               LowSpeedSwitchStatus +
               WiperINTSwitchStatus +
               WashPumpSwitchStatus)
        print(sD2)
        sHexD2 = format(int(sD2, 2), '02x')
        print("sHexD2", sHexD2)
        # --------------------------------------------------------
        StartSwitchStatus = ""  # [3.0~3.1]
        if self.cmbStartSwitchStatus.currentIndex() == 0:  # Off
            print("Start Switch Off")
            StartSwitchStatus = "00"
        elif self.cmbStartSwitchStatus.currentIndex() == 1:  # ACC
            print("Start Switch ACC")
            StartSwitchStatus = "01"
        elif self.cmbStartSwitchStatus.currentIndex() == 2:  # IGN
            print("Start Switch IGN")
            StartSwitchStatus = "10"
        elif self.cmbStartSwitchStatus.currentIndex() == 3:  # Start
            print("Start Switch Start")
            StartSwitchStatus = "11"
        # --------------------------------------------------------
        AcSwitchStatus = "0"
        if self.chkAcSwitchStatus.isChecked():  # [3.2]
            AcSwitchStatus = "1"
        else:
            AcSwitchStatus = "0"
        # --------------------------------------------------------
        RoadFinderStatus = "0"
        if self.chkRoadFinderStatus.isChecked():  # [3.3]
            RoadFinderStatus = "1"
        else:
            RoadFinderStatus = "0"
        # --------------------------------------------------------
        ParkPositionStatus = "0"
        if self.chkParkPositionStatus.isChecked():  # [3.4]
            ParkPositionStatus = "1"
        else:
            ParkPositionStatus = "0"
        # --------------------------------------------------------
        AutoLightStatus = "0"
        if self.chkAutoLightStatus.isChecked():  # [3.5]
            AutoLightStatus = "1"
        else:
            AutoLightStatus = "0"
        # --------------------------------------------------------
        AutoWiperStatus = "0"
        if self.chkAutoWiperStatus.isChecked():  # [3.6]
            AutoWiperStatus = "1"
        else:
            AutoWiperStatus = "0"
        # --------------------------------------------------------
        sD3 = ("0" +
               AutoWiperStatus +
               AutoLightStatus +
               ParkPositionStatus +
               RoadFinderStatus +
               AcSwitchStatus +
               StartSwitchStatus)
        print(sD3)
        sHexD3 = format(int(sD3, 2), '02x')
        print("sHexD3", sHexD3)
        # --------------------------------------------------------
        ScreenHeaterSwitchStatus = "0"
        if self.chkScreenHeaterSwitchStatus.isChecked():  # [4.0]
            ScreenHeaterSwitchStatus = "1"
        else:
            ScreenHeaterSwitchStatus = "0"
        # --------------------------------------------------------
        SeatBeltSwitchstatus = "0"
        if self.chkSeatBeltSwitchstatus.isChecked():  # [4.1]
            SeatBeltSwitchstatus = "1"
        else:
            SeatBeltSwitchstatus = "0"
        # --------------------------------------------------------
        BrakePedalSwitchStatus = "0"
        if self.chkBrakePedalSwitchStatus.isChecked():  # [4.2]
            BrakePedalSwitchStatus = "1"
        else:
            BrakePedalSwitchStatus = "0"
        # --------------------------------------------------------
        HandBrakeSwitchStatus = "0"
        if self.chkHandBrakeSwitchStatus.isChecked():  # [4.3]
            HandBrakeSwitchStatus = "1"
        else:
            HandBrakeSwitchStatus = "0"
        # --------------------------------------------------------
        ReverseSwitchStatus = "0"
        if self.chkReverseSwitchStatus.isChecked():  # [4.4]
            ReverseSwitchStatus = "1"
        else:
            ReverseSwitchStatus = "0"
        # --------------------------------------------------------
        sD4 = ("000" +
               ReverseSwitchStatus +
               HandBrakeSwitchStatus +
               BrakePedalSwitchStatus +
               SeatBeltSwitchstatus +
               ScreenHeaterSwitchStatus)
        print(sD4)
        sHexD4 = format(int(sD4, 2), '02x')
        print("sHexD4", sHexD4)
        # --------------------------------------------------------
        RemoteStatus = ""  # [5.0~5.1]
        if self.cmbRemoteStatus.currentIndex() == 0:  # Lock
            print("Remote Status Lock")
            RemoteStatus = "00"
        elif self.cmbRemoteStatus.currentIndex() == 1:  # Unlock
            print("Remote Status Unlock")
            RemoteStatus = "01"
        elif self.cmbRemoteStatus.currentIndex() == 2:  # No Action
            print("Remote Status No Action")
            RemoteStatus = "10"
        elif self.cmbRemoteStatus.currentIndex() == 3:  # Trunk Lid
            print("Remote status Trunk Lid")
            RemoteStatus = "11"
        # --------------------------------------------------------
        GlobalLockUnlockStatus = ""  # [5.2~5.3]
        if self.cmbGlobalLockUnlockStatus.currentIndex() == 0:  # Lock
            print("Global Lock Status: Lock")
            GlobalLockUnlockStatus = "00"
        elif self.cmbGlobalLockUnlockStatus.currentIndex() == 1:  # Unlock
            print("Global Lock Status: Unlock")
            GlobalLockUnlockStatus = "01"
        elif self.cmbGlobalLockUnlockStatus.currentIndex() == 2:  # No Action
            print("Global Lock Status: No Action")
            GlobalLockUnlockStatus = "10"
        # --------------------------------------------------------
        FLHActuatorSwitchStatus = "0"
        if self.chkFLHActuatorSwitchStatus.isChecked():  # [5.4]
            FLHActuatorSwitchStatus = "1"
        else:
            FLHActuatorSwitchStatus = "0"
        # --------------------------------------------------------
        FRHActuatorSwitchStatus = "0"
        if self.chkFRHActuatorSwitchStatus.isChecked():  # [5.5]
            FRHActuatorSwitchStatus = "1"
        else:
            FRHActuatorSwitchStatus = "0"
        # --------------------------------------------------------
        MasterLockSwitchStatus = "0"
        if self.chkMasterLockSwitchStatus.isChecked():  # [5.6]
            MasterLockSwitchStatus = "1"
        else:
            MasterLockSwitchStatus = "0"
        # --------------------------------------------------------
        VaccumPumpFailure = "0"
        if self.chkVaccumPumpFailure.isChecked():  # [5.7]
            VaccumPumpFailure = "1"
        else:
            VaccumPumpFailure = "0"
        # --------------------------------------------------------
        sD5 = (VaccumPumpFailure +
               MasterLockSwitchStatus +
               FRHActuatorSwitchStatus +
               FLHActuatorSwitchStatus +
               GlobalLockUnlockStatus +
               RemoteStatus)
        print(sD5)
        sHexD5 = format(int(sD5, 2), '02x')
        print("sHexD5", sHexD5)
        # --------------------------------------------------------
        LHWindowSwitchStatus = ""  # [6.0~6.1]
        if self.cmbLHWindowSwitchStatus.currentIndex() == 0:  # Off
            print("LH Window Switch Status: Off")
            LHWindowSwitchStatus = "00"
        elif self.cmbLHWindowSwitchStatus.currentIndex() == 1:  # Up
            print("LH Window Switch Status: Up")
            LHWindowSwitchStatus = "01"
        elif self.cmbLHWindowSwitchStatus.currentIndex() == 2:  # Down
            print("LH Window Switch Status: Down")
            LHWindowSwitchStatus = "10"
        elif self.cmbLHWindowSwitchStatus.currentIndex() == 3:  # Error
            print("LH Window Switch Status: Error")
            LHWindowSwitchStatus = "11"
        # --------------------------------------------------------
        RHWindowSwitchStatus = ""  # [6.2~6.3]
        if self.cmbRHWindowSwitchStatus.currentIndex() == 0:  # Off
            print("RH Window Switch Status: Off")
            RHWindowSwitchStatus = "00"
        elif self.cmbRHWindowSwitchStatus.currentIndex() == 1:  # Up
            print("RH Window Switch Status: Up")
            RHWindowSwitchStatus = "01"
        elif self.cmbRHWindowSwitchStatus.currentIndex() == 2:  # Down
            print("RH Window Switch Status: Down")
            RHWindowSwitchStatus = "10"
        elif self.cmbRHWindowSwitchStatus.currentIndex() == 3:  # Error
            print("RH Window Switch Status: Error")
            RHWindowSwitchStatus = "11"
        # --------------------------------------------------------
        sD6 = ("0000" + RHWindowSwitchStatus + LHWindowSwitchStatus)
        print(sD6)
        sHexD6 = format(int(sD6, 2), '02x')
        print("sHexD6", sHexD6)
        # --------------------------------------------------------
        HazardSwitchStatus = "0"
        if self.chkHazardSwitchStatus.isChecked():  # [7.0]
            HazardSwitchStatus = "1"
        else:
            HazardSwitchStatus = "0"
        # --------------------------------------------------------
        TrunkLidCommandSwitchStatus = "0"
        if self.chkTrunkLidCommandSwitchStatus.isChecked():  # [7.1]
            TrunkLidCommandSwitchStatus = "1"
        else:
            TrunkLidCommandSwitchStatus = "0"
        # --------------------------------------------------------
        IndicatorLampCommand = ""  # [7.2~7.3]
        if self.cmbIndicatorLampCommand.currentIndex() == 0:  # Off
            print("Indicator Lamp command: Off")
            IndicatorLampCommand = "00"
        elif self.cmbIndicatorLampCommand.currentIndex() == 1:  # LH ON
            print("Indicator Lamp command: LH ON")
            IndicatorLampCommand = "10"
        elif self.cmbIndicatorLampCommand.currentIndex() == 2:  # RH ON
            print("Indicator Lamp command: RH ON")
            IndicatorLampCommand = "01"
        elif self.cmbIndicatorLampCommand.currentIndex() == 3:  # LH & RH ON
            print("Indicator Lamp command: LH & RH ON")
            IndicatorLampCommand = "11"
        # --------------------------------------------------------
        ShockSensorCommand = "0"
        if self.chkShockSensorCommand.isChecked():  # [7.4]
            ShockSensorCommand = "1"
        else:
            ShockSensorCommand = "0"
        # --------------------------------------------------------
        AntiTheftstatus = ""  # [7.5~7.6]
        if self.cmbAntiTheftstatus.currentIndex() == 0:  # Inactive
            AntiTheftstatus = "00"
        elif self.cmbAntiTheftstatus.currentIndex() == 1:  # Active
            AntiTheftstatus = "01"
        elif self.cmbAntiTheftstatus.currentIndex() == 2:  # Alarm
            AntiTheftstatus = "10"
        elif self.cmbAntiTheftstatus.currentIndex() == 3:  # Pause Alarm
            AntiTheftstatus = "11"
        # --------------------------------------------------------
        sD7 = ("0" +
               AntiTheftstatus +
               ShockSensorCommand +
               IndicatorLampCommand +
               TrunkLidCommandSwitchStatus +
               HazardSwitchStatus)
        print(sD7)
        sHexD7 = format(int(sD7, 2), '02x')
        print("sHexD7", sHexD7)
        # --------------------------------------------------------
        self.set_tx_slot(str(self.cmbCbmHighSpeedInfo3Slot.currentIndex() + 1),
                         "241",
                         "8",
                         sHexD0.upper(),
                         sHexD1.upper(),
                         sHexD2.upper(),
                         sHexD3.upper(),
                         sHexD4.upper(),
                         sHexD5.upper(),
                         sHexD6.upper(),
                         sHexD7.upper(),
                         "100")

        if self.chkAutoTransmit.isChecked():
            self.auto_transmit_slot_no = self.cmbCbmHighSpeedInfo3Slot.currentIndex() + 1

    def btn_cbm_body_network_click_handler(self):
        sD0 = ""
        sD1 = ""
        sD2 = ""
        sD3 = ""
        sD4 = ""
        sD5 = ""
        sD6 = ""
        sD7 = ""

        sHexD0 = ""
        sHexD1 = ""
        sHexD2 = ""
        sHexD3 = ""
        sHexD4 = ""
        sHexD5 = ""
        sHexD6 = ""
        sHexD7 = ""

        # --------------------------------------------------------
        BodyNetworkManagement = ""  # [0.0~0.2]
        if self.cmbBodyNetworkManagement.currentIndex() == 0:  # Sleep
            BodyNetworkManagement = "000"
        elif self.cmbBodyNetworkManagement.currentIndex() == 1:  # Normal
            BodyNetworkManagement = "001"
        elif self.cmbBodyNetworkManagement.currentIndex() == 2:  # Go To Sleep
            BodyNetworkManagement = "010"
        elif self.cmbBodyNetworkManagement.currentIndex() == 3:  # Wakeup
            BodyNetworkManagement = "011"
        elif self.cmbBodyNetworkManagement.currentIndex() == 4:  # COM OFF
            BodyNetworkManagement = "100"
        elif self.cmbBodyNetworkManagement.currentIndex() == 5:  # Not Available
            BodyNetworkManagement = "111"

        SupervisionState = ""  # [0.3]
        if self.cmbSupervisionState.currentIndex() == 0:  # Off
            SupervisionState = "0"
        elif self.cmbSupervisionState.currentIndex() == 1:  # Ready
            SupervisionState = "1"
        # --------------------------------------------------------
        sD0 = ("0000" +
               SupervisionState +
               BodyNetworkManagement)

        print(sD0)
        sHexD0 = format(int(sD0, 2), '02x')
        print("sHexD0", sHexD0)
        # --------------------------------------------------------
        ABSIsAbsent = ""
        if self.chkAbsIsAbsent.isChecked():  # [1.0]
            ABSIsAbsent = "1"
        else:
            ABSIsAbsent = "0"
        # --------------------------------------------------------
        CBMIsAbsent = ""  # [1.1]
        if self.chkCBMIsAbsent.isChecked():
            CBMIsAbsent = "1"
        else:
            CBMIsAbsent = "0"
        # --------------------------------------------------------
        EMSIsAbsent = ""  # [1.2]
        if self.chkEMSIsAbsent.isChecked():
            EMSIsAbsent = "1"
        else:
            EMSIsAbsent = "0"
        # --------------------------------------------------------
        EPASIsAbsent = ""  # [1.3]
        if self.chkEPASIsAbsent.isChecked():
            EPASIsAbsent = "1"
        else:
            EPASIsAbsent = "0"
        # --------------------------------------------------------
        SASIsAbsent = ""  # [1.4]
        if self.chkSASIsAbsent.isChecked():
            SASIsAbsent = "1"
        else:
            SASIsAbsent = "0"
        # --------------------------------------------------------
        TCUIsAbsent = ""  # [1.5]
        if self.chkTCUIsAbsent.isChecked():
            TCUIsAbsent = "1"
        else:
            TCUIsAbsent = "0"
        # --------------------------------------------------------
        ClusterIsAbsent = ""  # [1.6]
        if self.chkClusterIsAbsent.isChecked():
            ClusterIsAbsent = "1"
        else:
            ClusterIsAbsent = "0"
        # --------------------------------------------------------
        ICUIsAbsent = ""  # [1.7]
        if self.chkICUIsAbsent.isChecked():
            ICUIsAbsent = "1"
        else:
            ICUIsAbsent = "0"
        # --------------------------------------------------------
        sD1 = (ICUIsAbsent +
               ClusterIsAbsent +
               TCUIsAbsent +
               SASIsAbsent +
               EPASIsAbsent +
               EMSIsAbsent +
               CBMIsAbsent +
               ABSIsAbsent)

        print(sD1)
        sHexD1 = format(int(sD1, 2), '02x')
        print("sHexD1", sHexD1)
        # --------------------------------------------------------
        sD2 = "00000000"
        sHexD2 = format(int(sD2, 2), '02x')
        print("sHexD2", sHexD2)
        # --------------------------------------------------------
        sD3 = "00000000"
        sHexD3 = format(int(sD3, 2), '02x')
        print("sHexD3", sHexD3)
        # --------------------------------------------------------
        sD4 = "00000000"
        sHexD4 = format(int(sD4, 2), '02x')
        print("sHexD4", sHexD4)
        # --------------------------------------------------------
        sD5 = "00000000"
        sHexD5 = format(int(sD5, 2), '02x')
        print("sHexD5", sHexD5)
        # --------------------------------------------------------
        sD6 = "00000000"
        sHexD6 = format(int(sD6, 2), '02x')
        print("sHexD6", sHexD6)
        # --------------------------------------------------------
        sD7 = "00000000"
        sHexD7 = format(int(sD7, 2), '02x')
        print("sHexD7", sHexD7)
        # --------------------------------------------------------
        self.set_tx_slot(str(self.cmbBodyNetworkManagementSlot.currentIndex() + 1),
                         "181",
                         "4",
                         sHexD0.upper(),
                         sHexD1.upper(),
                         sHexD2.upper(),
                         sHexD3.upper(),
                         sHexD4.upper(),
                         sHexD5.upper(),
                         sHexD6.upper(),
                         sHexD7.upper(),
                         "100")
        if self.chkAutoTransmit.isChecked():
            self.auto_transmit_slot_no = self.cmbBodyNetworkManagementSlot.currentIndex() + 1

    def btn_fam_info_click_handler(self):
        BatteryChargeWarning = ""
        if self.chkBatteryChargeWarning.isChecked():  # [0.0]
            BatteryChargeWarning = "1"
        else:
            BatteryChargeWarning = "0"
        # --------------------------------------------------------
        EngineOilPressure = ""
        if self.chkEngineOilPressureWarning.isChecked():  # [0.2]
            EngineOilPressure = "1"
        else:
            EngineOilPressure = "0"
        # --------------------------------------------------------
        BrakePadWarning = ""
        if self.BrakePadWarning.isChecked():  # [0.5]
            BrakePadWarning = "1"
        else:
            BrakePadWarning = "0"
        # --------------------------------------------------------
        BrakeOilLevelWarning = ""
        if self.chkBrakeOilLevelWarning.isChecked():  # [0.6]
            BrakeOilLevelWarning = "1"
        else:
            BrakeOilLevelWarning = "0"
        # --------------------------------------------------------
        sD0 = ("0" +
               BrakeOilLevelWarning +
               BrakePadWarning +
               "00" +
               EngineOilPressure +
               "0" +
               BatteryChargeWarning)

        print(sD0)
        sHexD0 = format(int(sD0, 2), '02x')
        print("sHexD0", sHexD0)
        # --------------------------------------------------------
        ReverseGearSwitchStatus = ""
        if self.chkReverseGearSwitchStatus.isChecked():  # [1.0]
            ReverseGearSwitchStatus = "1"
        else:
            ReverseGearSwitchStatus = "0"
        # --------------------------------------------------------
        WiperZeroPositionSwitchStatus = ""
        if self.chkWiperZeroPositionStatus.isChecked():  # [1.1]
            WiperZeroPositionSwitchStatus = "1"
        else:
            WiperZeroPositionSwitchStatus = "0"
        # --------------------------------------------------------
        AcCompressorClutchStatus = ""
        if self.chkAcCompressorClutchStatus.isChecked():  # [1.2]
            AcCompressorClutchStatus = "1"
        else:
            AcCompressorClutchStatus = "0"
        # --------------------------------------------------------
        sD1 = ("00000" +
               AcCompressorClutchStatus +
               WiperZeroPositionSwitchStatus +
               ReverseGearSwitchStatus)

        print(sD1)
        sHexD1 = format(int(sD1, 2), '02x')
        print("sHexD1", sHexD1)
        # --------------------------------------------------------
        sD2 = "00000000"
        sHexD2 = format(int(sD2, 2), '02x')
        print("sHexD2", sHexD2)
        # --------------------------------------------------------
        sD3 = "00000000"
        sHexD3 = format(int(sD3, 2), '02x')
        print("sHexD3", sHexD3)
        # --------------------------------------------------------
        sD4 = "00000000"
        sHexD4 = format(int(sD4, 2), '02x')
        print("sHexD4", sHexD4)
        # --------------------------------------------------------
        sD5 = "00000000"
        sHexD5 = format(int(sD5, 2), '02x')
        print("sHexD5", sHexD5)
        # --------------------------------------------------------
        sD6 = "00000000"
        sHexD6 = format(int(sD6, 2), '02x')
        print("sHexD6", sHexD6)
        # --------------------------------------------------------
        sD7 = "00000000"
        sHexD7 = format(int(sD7, 2), '02x')
        print("sHexD7", sHexD7)
        # --------------------------------------------------------
        self.set_tx_slot(str(self.cmbFAMInformation.currentIndex() + 1),
                         "2C2",
                         "2",
                         sHexD0.upper(),
                         sHexD1.upper(),
                         sHexD2.upper(),
                         sHexD3.upper(),
                         sHexD4.upper(),
                         sHexD5.upper(),
                         sHexD6.upper(),
                         sHexD7.upper(),
                         "100")

        if self.chkAutoTransmit.isChecked():
            self.auto_transmit_slot_no = self.cmbFAMInformation.currentIndex() + 1

    def dial_speed_wheel_value_change_handler(self):
        getValue = self.dialWheelSpeed.value()
        self.leWheelSpeed.setText(str(getValue))

    def btn_ABS_information_click_handler(self):
        sD0 = ""
        sD1 = ""
        sD2 = ""
        sD3 = ""
        sD4 = ""
        sD5 = ""
        sD6 = ""
        sD7 = ""

        sHexD0 = ""
        sHexD1 = ""
        sHexD2 = ""
        sHexD3 = ""
        sHexD4 = ""
        sHexD5 = ""
        sHexD6 = ""
        sHexD7 = ""
        # --------------------------------------------------------
        ABSError = ""
        if self.chkABSError.isChecked():  # [0.0]
            ABSError = "1"
        else:
            ABSError = "0"
        # --------------------------------------------------------
        EBDError = ""
        if self.chkEBDError.isChecked():  # [0.1]
            EBDError = "1"
        else:
            EBDError = "0"
        # --------------------------------------------------------
        ABSActive = ""
        if self.chkABSActive.isChecked():  # [0.2]
            ABSActive = "1"
        else:
            ABSActive = "0"
        # --------------------------------------------------------
        ABSWarning = ""
        if self.chkABSWarning.isChecked():  # [0.3]
            ABSWarning = "1"
        else:
            ABSWarning = "0"
        # --------------------------------------------------------
        EBDWarning = ""
        if self.chkEBDWarning.isChecked():  # [0.4]
            EBDWarning = "1"
        else:
            EBDWarning = "0"
        # --------------------------------------------------------
        ABSDiag = ""
        if self.chkABSDiag.isChecked():  # [0.5]
            ABSDiag = "1"
        else:
            ABSDiag = "0"
        # --------------------------------------------------------
        EBDActive = ""
        if self.chkEBDActive.isChecked():  # [0.6]
            EBDActive = "1"
        else:
            EBDActive = "0"
        # --------------------------------------------------------
        sD0 = ("0" +
               EBDActive +
               ABSDiag +
               EBDWarning +
               ABSWarning +
               ABSActive +
               EBDError +
               ABSError)

        print(sD0)
        sHexD0 = format(int(sD0, 2), '02x')
        print("sHexD0", sHexD0)
        # --------------------------------------------------------
        ESPSwitch = ""
        if self.chkESPSwitch.isChecked():  # [1.0]
            ESPSwitch = "1"
        else:
            ESPSwitch = "0"
        # --------------------------------------------------------
        ESPWarning = ""  # [1.1~1.2]
        if self.cmbESPWarning.currentIndex() == 0:  # No Warning
            ESPWarning = "00"
        elif self.cmbESPWarning.currentIndex() == 1:  # Warning
            ESPWarning = "01"
        elif self.cmbESPWarning.currentIndex() == 2:  # Active
            ESPWarning = "10"
        # --------------------------------------------------------
        sD1 = ("00000" +
               ESPWarning +
               ESPSwitch)

        print(sD1)
        sHexD1 = format(int(sD1, 2), '02x')
        print("sHexD1", sHexD1)
        # --------------------------------------------------------
        SpeedWheelDec = self.dialWheelSpeed.value() * 11
        SpeedWheelHex = ""
        if SpeedWheelDec == 0:
            SpeedWheelHex = "00"
        else:
            SpeedWheelHex = str(SpeedWheelDec)

        print("SpeedWheelHex", SpeedWheelHex)
        sHexD2 = SpeedWheelHex
        sHexD3 = SpeedWheelHex
        sHexD4 = SpeedWheelHex
        sHexD5 = SpeedWheelHex
        sHexD6 = SpeedWheelHex
        sHexD7 = SpeedWheelHex
        # --------------------------------------------------------
        self.set_tx_slot(str(self.cmbABSInformation.currentIndex() + 1),
                         "405",
                         "8",
                         sHexD0.upper(),
                         sHexD1.upper(),
                         sHexD2.upper(),
                         sHexD3.upper(),
                         sHexD4.upper(),
                         sHexD5.upper(),
                         sHexD6.upper(),
                         sHexD7.upper(),
                         "100")
        if self.chkAutoTransmit.isChecked():
            self.auto_transmit_slot_no = self.cmbABSInformation.currentIndex() + 1

    def dial_engine_speed_value_changed_handler(self):
        getValue = self.dialEngineSpeed.value()
        self.leEngineSpeed.setText(str(getValue))

    def dial_tco_value_changed_handler(self):
        getValue = self.dialTCO.value()
        self.leTCO.setText(str(getValue))

    def dial_vehicle_speed_value_changed_handler(self):
        getValue = self.dialVehicleSpeed.value()
        self.leVehicleSpeed.setText(str(getValue))

    def btn_cbm_engine_info6_click_handler(self):
        sD0 = ""
        sD1 = ""
        sD2 = ""
        sD3 = ""
        sD4 = ""
        sD5 = ""
        sD6 = ""
        sD7 = ""

        sHexD0 = ""
        sHexD1 = ""
        sHexD2 = ""
        sHexD3 = ""
        sHexD4 = ""
        sHexD5 = ""
        sHexD6 = ""
        sHexD7 = ""
        # --------------------------------------------------------
        CheckEngine = ""  # [0.0]
        if self.chkCheckEngine.isChecked():
            CheckEngine = "1"
        else:
            CheckEngine = "0"
        # --------------------------------------------------------
        HotLampWarning = ""  # [0.1]
        if self.chkHotLampWarning.isChecked():
            HotLampWarning = "1"
        else:
            HotLampWarning = "0"
        # --------------------------------------------------------
        VehicleSpeedError = ""  # [0.2]
        if self.chkVehicleSpeedError.isChecked():
            VehicleSpeedError = "1"
        else:
            VehicleSpeedError = "0"
        # --------------------------------------------------------
        AirConditionrequest = ""  # [0.3]
        if self.chkAirConditionrequest.isChecked():
            AirConditionrequest = "1"
        else:
            AirConditionrequest = "0"
        # --------------------------------------------------------
        AirConditionPressureSwitch1 = ""  # [0.4]
        if self.chkAirConditionPressureSwitch1.isChecked():
            AirConditionPressureSwitch1 = "1"
        else:
            AirConditionPressureSwitch1 = "0"
        # --------------------------------------------------------
        AirConditionPressureSwitch2 = ""  # [0.5]
        if self.chkAirConditionPressureSwitch2.isChecked():
            AirConditionPressureSwitch2 = "1"
        else:
            AirConditionPressureSwitch2 = "0"
        # --------------------------------------------------------
        AirConditionCommand = ""  # [0.6]
        if self.chkAirConditionCommand.isChecked():
            AirConditionCommand = "1"
        else:
            AirConditionCommand = "0"
        # --------------------------------------------------------
        EOBDWarning = ""  # [0.7]
        if self.chkEOBDWarnning.isChecked():
            EOBDWarning = "1"
        else:
            EOBDWarning = "0"
        # --------------------------------------------------------
        sD0 = (EOBDWarning +
               AirConditionCommand +
               AirConditionPressureSwitch2 +
               AirConditionPressureSwitch1 +
               AirConditionrequest +
               VehicleSpeedError +
               HotLampWarning +
               CheckEngine)

        print(sD0)
        sHexD0 = format(int(sD0, 2), '02x')
        print("sHexD0", sHexD0)
        # --------------------------------------------------------
        RpmB1 = self.dialEngineSpeed.value() // 256
        RpmB2 = self.dialEngineSpeed.value() % 256
        print("RpmB1: ", RpmB1, " - RpmB1: ", RpmB2)
        RpmB1Hex = hex(RpmB1)
        RpmB1Hex = RpmB1Hex.upper()
        RpmB2Hex = hex(RpmB2)
        RpmB2Hex = RpmB2Hex.upper()
        RpmB1Hex = RpmB1Hex[2:]
        RpmB2Hex = RpmB2Hex[2:]
        if len(RpmB1Hex) < 2:
            RpmB1Hex = "0" + RpmB1Hex

        if len(RpmB2Hex) < 2:
            RpmB2Hex = "0" + RpmB2Hex

        print("RpmB1Hex: ", RpmB1Hex)
        print("RpmB2Hex: ", RpmB2Hex)

        sHexD1 = RpmB2Hex
        sHexD2 = RpmB1Hex
        # --------------------------------------------------------
        sHexD3 = "00"
        sHexD4 = "00"
        # --------------------------------------------------------
        Tco = self.dialTCO.value()
        TcoHex = hex(Tco)
        TcoHex = TcoHex.upper()
        TcoHex = TcoHex[2:]
        if len(TcoHex) < 2:
            TcoHex = "0" + TcoHex

        print("TcoHex: ", TcoHex)
        sHexD5 = TcoHex
        # --------------------------------------------------------
        VehicleSpeed = self.dialVehicleSpeed.value()
        VehicleSpeedHex = hex(VehicleSpeed)
        VehicleSpeedHex = VehicleSpeedHex.upper()
        VehicleSpeedHex = VehicleSpeedHex[2:]
        if len(VehicleSpeedHex) < 2:
            VehicleSpeedHex = "0" + VehicleSpeedHex

        print("VehicleSpeedHex: ", VehicleSpeedHex)
        sHexD6 = VehicleSpeedHex
        # --------------------------------------------------------
        sHexD7 = "00"
        # --------------------------------------------------------
        self.set_tx_slot(str(self.cmbCbmEngineInfo6.currentIndex() + 1),
                         "443",
                         "8",
                         sHexD0.upper(),
                         sHexD1.upper(),
                         sHexD2.upper(),
                         sHexD3.upper(),
                         sHexD4.upper(),
                         sHexD5.upper(),
                         sHexD6.upper(),
                         sHexD7.upper(),
                         "100")
        if self.chkAutoTransmit.isChecked():
            self.auto_transmit_slot_no = self.cmbCbmEngineInfo6.currentIndex() + 1

    def btn_reload_click_handler(self):
        self.config.read('ecu.ini')
        print(self.config.sections())
        self.leTxId01.setText(self.config['Transmitter']['ID01'])
        self.leTxId03.setText(self.config['Transmitter']['ID02'])
        self.leTxId02.setText(self.config['Transmitter']['ID03'])
        self.leTxId04.setText(self.config['Transmitter']['ID04'])
        self.leTxId05.setText(self.config['Transmitter']['ID05'])
        self.leTxId06.setText(self.config['Transmitter']['ID06'])
        self.leTxId07.setText(self.config['Transmitter']['ID07'])
        self.leTxId08.setText(self.config['Transmitter']['ID08'])
        self.leTxId09.setText(self.config['Transmitter']['ID09'])
        self.leTxId10.setText(self.config['Transmitter']['ID10'])
        self.leTxId11.setText(self.config['Transmitter']['ID11'])
        self.leTxId12.setText(self.config['Transmitter']['ID12'])
        self.leTxId13.setText(self.config['Transmitter']['ID13'])
        self.leTxId14.setText(self.config['Transmitter']['ID14'])
        self.leTxId15.setText(self.config['Transmitter']['ID15'])
        self.leTxId16.setText(self.config['Transmitter']['ID16'])
        self.leTxId17.setText(self.config['Transmitter']['ID17'])
        self.leTxId18.setText(self.config['Transmitter']['ID18'])
        self.leTxId19.setText(self.config['Transmitter']['ID19'])
        self.leTxId20.setText(self.config['Transmitter']['ID20'])
        # -------------------------------------------------------
        self.leTxDlc01.setText(self.config['Transmitter']['DLC01'])
        self.leTxDlc02.setText(self.config['Transmitter']['DLC02'])
        self.leTxDlc03.setText(self.config['Transmitter']['DLC03'])
        self.leTxDlc04.setText(self.config['Transmitter']['DLC04'])
        self.leTxDlc05.setText(self.config['Transmitter']['DLC05'])
        self.leTxDlc06.setText(self.config['Transmitter']['DLC06'])
        self.leTxDlc07.setText(self.config['Transmitter']['DLC07'])
        self.leTxDlc08.setText(self.config['Transmitter']['DLC08'])
        self.leTxDlc09.setText(self.config['Transmitter']['DLC09'])
        self.leTxDlc10.setText(self.config['Transmitter']['DLC10'])
        self.leTxDlc11.setText(self.config['Transmitter']['DLC11'])
        self.leTxDlc12.setText(self.config['Transmitter']['DLC12'])
        self.leTxDlc13.setText(self.config['Transmitter']['DLC13'])
        self.leTxDlc14.setText(self.config['Transmitter']['DLC14'])
        self.leTxDlc15.setText(self.config['Transmitter']['DLC15'])
        self.leTxDlc16.setText(self.config['Transmitter']['DLC16'])
        self.leTxDlc17.setText(self.config['Transmitter']['DLC17'])
        self.leTxDlc18.setText(self.config['Transmitter']['DLC18'])
        self.leTxDlc19.setText(self.config['Transmitter']['DLC19'])
        self.leTxDlc20.setText(self.config['Transmitter']['DLC20'])
        # ---------------------------------------------------------
        self.leTxD0_01.setText(self.config['Transmitter']['D0_01'])
        self.leTxD0_02.setText(self.config['Transmitter']['D0_02'])
        self.leTxD0_03.setText(self.config['Transmitter']['D0_03'])
        self.leTxD0_04.setText(self.config['Transmitter']['D0_04'])
        self.leTxD0_05.setText(self.config['Transmitter']['D0_05'])
        self.leTxD0_06.setText(self.config['Transmitter']['D0_06'])
        self.leTxD0_07.setText(self.config['Transmitter']['D0_07'])
        self.leTxD0_08.setText(self.config['Transmitter']['D0_08'])
        self.leTxD0_09.setText(self.config['Transmitter']['D0_09'])
        self.leTxD0_10.setText(self.config['Transmitter']['D0_10'])
        self.leTxD0_11.setText(self.config['Transmitter']['D0_11'])
        self.leTxD0_12.setText(self.config['Transmitter']['D0_12'])
        self.leTxD0_13.setText(self.config['Transmitter']['D0_13'])
        self.leTxD0_14.setText(self.config['Transmitter']['D0_14'])
        self.leTxD0_15.setText(self.config['Transmitter']['D0_15'])
        self.leTxD0_16.setText(self.config['Transmitter']['D0_16'])
        self.leTxD0_17.setText(self.config['Transmitter']['D0_17'])
        self.leTxD0_18.setText(self.config['Transmitter']['D0_18'])
        self.leTxD0_19.setText(self.config['Transmitter']['D0_19'])
        self.leTxD0_20.setText(self.config['Transmitter']['D0_20'])
        # ---------------------------------------------------------
        self.leTxD1_01.setText(self.config['Transmitter']['D1_01'])
        self.leTxD1_02.setText(self.config['Transmitter']['D1_02'])
        self.leTxD1_03.setText(self.config['Transmitter']['D1_03'])
        self.leTxD1_04.setText(self.config['Transmitter']['D1_04'])
        self.leTxD1_05.setText(self.config['Transmitter']['D1_05'])
        self.leTxD1_06.setText(self.config['Transmitter']['D1_06'])
        self.leTxD1_07.setText(self.config['Transmitter']['D1_07'])
        self.leTxD1_08.setText(self.config['Transmitter']['D1_08'])
        self.leTxD1_09.setText(self.config['Transmitter']['D1_09'])
        self.leTxD1_10.setText(self.config['Transmitter']['D1_10'])
        self.leTxD1_11.setText(self.config['Transmitter']['D1_11'])
        self.leTxD1_12.setText(self.config['Transmitter']['D1_12'])
        self.leTxD1_13.setText(self.config['Transmitter']['D1_13'])
        self.leTxD1_14.setText(self.config['Transmitter']['D1_14'])
        self.leTxD1_15.setText(self.config['Transmitter']['D1_15'])
        self.leTxD1_16.setText(self.config['Transmitter']['D1_16'])
        self.leTxD1_17.setText(self.config['Transmitter']['D1_17'])
        self.leTxD1_18.setText(self.config['Transmitter']['D1_18'])
        self.leTxD1_19.setText(self.config['Transmitter']['D1_19'])
        self.leTxD1_20.setText(self.config['Transmitter']['D1_20'])
        # ---------------------------------------------------------
        self.leTxD2_01.setText(self.config['Transmitter']['D2_01'])
        self.leTxD2_02.setText(self.config['Transmitter']['D2_02'])
        self.leTxD2_03.setText(self.config['Transmitter']['D2_03'])
        self.leTxD2_04.setText(self.config['Transmitter']['D2_04'])
        self.leTxD2_05.setText(self.config['Transmitter']['D2_05'])
        self.leTxD2_06.setText(self.config['Transmitter']['D2_06'])
        self.leTxD2_07.setText(self.config['Transmitter']['D2_07'])
        self.leTxD2_08.setText(self.config['Transmitter']['D2_08'])
        self.leTxD2_09.setText(self.config['Transmitter']['D2_09'])
        self.leTxD2_10.setText(self.config['Transmitter']['D2_10'])
        self.leTxD2_11.setText(self.config['Transmitter']['D2_11'])
        self.leTxD2_12.setText(self.config['Transmitter']['D2_12'])
        self.leTxD2_13.setText(self.config['Transmitter']['D2_13'])
        self.leTxD2_14.setText(self.config['Transmitter']['D2_14'])
        self.leTxD2_15.setText(self.config['Transmitter']['D2_15'])
        self.leTxD2_16.setText(self.config['Transmitter']['D2_16'])
        self.leTxD2_17.setText(self.config['Transmitter']['D2_17'])
        self.leTxD2_18.setText(self.config['Transmitter']['D2_18'])
        self.leTxD2_19.setText(self.config['Transmitter']['D2_19'])
        self.leTxD2_20.setText(self.config['Transmitter']['D2_20'])
        # ---------------------------------------------------------
        self.leTxD3_01.setText(self.config['Transmitter']['D3_01'])
        self.leTxD3_02.setText(self.config['Transmitter']['D3_02'])
        self.leTxD3_03.setText(self.config['Transmitter']['D3_03'])
        self.leTxD3_04.setText(self.config['Transmitter']['D3_04'])
        self.leTxD3_05.setText(self.config['Transmitter']['D3_05'])
        self.leTxD3_06.setText(self.config['Transmitter']['D3_06'])
        self.leTxD3_07.setText(self.config['Transmitter']['D3_07'])
        self.leTxD3_08.setText(self.config['Transmitter']['D3_08'])
        self.leTxD3_09.setText(self.config['Transmitter']['D3_09'])
        self.leTxD3_10.setText(self.config['Transmitter']['D3_10'])
        self.leTxD3_11.setText(self.config['Transmitter']['D3_11'])
        self.leTxD3_12.setText(self.config['Transmitter']['D3_12'])
        self.leTxD3_13.setText(self.config['Transmitter']['D3_13'])
        self.leTxD3_14.setText(self.config['Transmitter']['D3_14'])
        self.leTxD3_15.setText(self.config['Transmitter']['D3_15'])
        self.leTxD3_16.setText(self.config['Transmitter']['D3_16'])
        self.leTxD3_17.setText(self.config['Transmitter']['D3_17'])
        self.leTxD3_18.setText(self.config['Transmitter']['D3_18'])
        self.leTxD3_19.setText(self.config['Transmitter']['D3_19'])
        self.leTxD3_20.setText(self.config['Transmitter']['D3_20'])
        # ---------------------------------------------------------
        self.leTxD4_01.setText(self.config['Transmitter']['D4_01'])
        self.leTxD4_02.setText(self.config['Transmitter']['D4_02'])
        self.leTxD4_03.setText(self.config['Transmitter']['D4_03'])
        self.leTxD4_04.setText(self.config['Transmitter']['D4_04'])
        self.leTxD4_05.setText(self.config['Transmitter']['D4_05'])
        self.leTxD4_06.setText(self.config['Transmitter']['D4_06'])
        self.leTxD4_07.setText(self.config['Transmitter']['D4_07'])
        self.leTxD4_08.setText(self.config['Transmitter']['D4_08'])
        self.leTxD4_09.setText(self.config['Transmitter']['D4_09'])
        self.leTxD4_10.setText(self.config['Transmitter']['D4_10'])
        self.leTxD4_11.setText(self.config['Transmitter']['D4_11'])
        self.leTxD4_12.setText(self.config['Transmitter']['D4_12'])
        self.leTxD4_13.setText(self.config['Transmitter']['D4_13'])
        self.leTxD4_14.setText(self.config['Transmitter']['D4_14'])
        self.leTxD4_15.setText(self.config['Transmitter']['D4_15'])
        self.leTxD4_16.setText(self.config['Transmitter']['D4_16'])
        self.leTxD4_17.setText(self.config['Transmitter']['D4_17'])
        self.leTxD4_18.setText(self.config['Transmitter']['D4_18'])
        self.leTxD4_19.setText(self.config['Transmitter']['D4_19'])
        self.leTxD4_20.setText(self.config['Transmitter']['D4_20'])
        # ---------------------------------------------------------
        self.leTxD5_01.setText(self.config['Transmitter']['D5_01'])
        self.leTxD5_02.setText(self.config['Transmitter']['D5_02'])
        self.leTxD5_03.setText(self.config['Transmitter']['D5_03'])
        self.leTxD5_04.setText(self.config['Transmitter']['D5_04'])
        self.leTxD5_05.setText(self.config['Transmitter']['D5_05'])
        self.leTxD5_06.setText(self.config['Transmitter']['D5_06'])
        self.leTxD5_07.setText(self.config['Transmitter']['D5_07'])
        self.leTxD5_08.setText(self.config['Transmitter']['D5_08'])
        self.leTxD5_09.setText(self.config['Transmitter']['D5_09'])
        self.leTxD5_10.setText(self.config['Transmitter']['D5_10'])
        self.leTxD5_11.setText(self.config['Transmitter']['D5_11'])
        self.leTxD5_12.setText(self.config['Transmitter']['D5_12'])
        self.leTxD5_13.setText(self.config['Transmitter']['D5_13'])
        self.leTxD5_14.setText(self.config['Transmitter']['D5_14'])
        self.leTxD5_15.setText(self.config['Transmitter']['D5_15'])
        self.leTxD5_16.setText(self.config['Transmitter']['D5_16'])
        self.leTxD5_17.setText(self.config['Transmitter']['D5_17'])
        self.leTxD5_18.setText(self.config['Transmitter']['D5_18'])
        self.leTxD5_19.setText(self.config['Transmitter']['D5_19'])
        self.leTxD5_20.setText(self.config['Transmitter']['D5_20'])
        # ---------------------------------------------------------
        self.leTxD6_01.setText(self.config['Transmitter']['D6_01'])
        self.leTxD6_02.setText(self.config['Transmitter']['D6_02'])
        self.leTxD6_03.setText(self.config['Transmitter']['D6_03'])
        self.leTxD6_04.setText(self.config['Transmitter']['D6_04'])
        self.leTxD6_05.setText(self.config['Transmitter']['D6_05'])
        self.leTxD6_06.setText(self.config['Transmitter']['D6_06'])
        self.leTxD6_07.setText(self.config['Transmitter']['D6_07'])
        self.leTxD6_08.setText(self.config['Transmitter']['D6_08'])
        self.leTxD6_09.setText(self.config['Transmitter']['D6_09'])
        self.leTxD6_10.setText(self.config['Transmitter']['D6_10'])
        self.leTxD6_11.setText(self.config['Transmitter']['D6_11'])
        self.leTxD6_12.setText(self.config['Transmitter']['D6_12'])
        self.leTxD6_13.setText(self.config['Transmitter']['D6_13'])
        self.leTxD6_14.setText(self.config['Transmitter']['D6_14'])
        self.leTxD6_15.setText(self.config['Transmitter']['D6_15'])
        self.leTxD6_16.setText(self.config['Transmitter']['D6_16'])
        self.leTxD6_17.setText(self.config['Transmitter']['D6_17'])
        self.leTxD6_18.setText(self.config['Transmitter']['D6_18'])
        self.leTxD6_19.setText(self.config['Transmitter']['D6_19'])
        self.leTxD6_20.setText(self.config['Transmitter']['D6_20'])
        # ---------------------------------------------------------
        self.leTxD7_01.setText(self.config['Transmitter']['D7_01'])
        self.leTxD7_02.setText(self.config['Transmitter']['D7_02'])
        self.leTxD7_03.setText(self.config['Transmitter']['D7_03'])
        self.leTxD7_04.setText(self.config['Transmitter']['D7_04'])
        self.leTxD7_05.setText(self.config['Transmitter']['D7_05'])
        self.leTxD7_06.setText(self.config['Transmitter']['D7_06'])
        self.leTxD7_07.setText(self.config['Transmitter']['D7_07'])
        self.leTxD7_08.setText(self.config['Transmitter']['D7_08'])
        self.leTxD7_09.setText(self.config['Transmitter']['D7_09'])
        self.leTxD7_10.setText(self.config['Transmitter']['D7_10'])
        self.leTxD7_11.setText(self.config['Transmitter']['D7_11'])
        self.leTxD7_12.setText(self.config['Transmitter']['D7_12'])
        self.leTxD7_13.setText(self.config['Transmitter']['D7_13'])
        self.leTxD7_14.setText(self.config['Transmitter']['D7_14'])
        self.leTxD7_15.setText(self.config['Transmitter']['D7_15'])
        self.leTxD7_16.setText(self.config['Transmitter']['D7_16'])
        self.leTxD7_17.setText(self.config['Transmitter']['D7_17'])
        self.leTxD7_18.setText(self.config['Transmitter']['D7_18'])
        self.leTxD7_19.setText(self.config['Transmitter']['D7_19'])
        self.leTxD7_20.setText(self.config['Transmitter']['D7_20'])
        # ---------------------------------------------------------
        self.leTxPeriod01.setText(self.config['Transmitter']['PERIOD01'])
        self.leTxPeriod02.setText(self.config['Transmitter']['PERIOD02'])
        self.leTxPeriod03.setText(self.config['Transmitter']['PERIOD03'])
        self.leTxPeriod04.setText(self.config['Transmitter']['PERIOD04'])
        self.leTxPeriod05.setText(self.config['Transmitter']['PERIOD05'])
        self.leTxPeriod06.setText(self.config['Transmitter']['PERIOD06'])
        self.leTxPeriod07.setText(self.config['Transmitter']['PERIOD07'])
        self.leTxPeriod08.setText(self.config['Transmitter']['PERIOD08'])
        self.leTxPeriod09.setText(self.config['Transmitter']['PERIOD09'])
        self.leTxPeriod10.setText(self.config['Transmitter']['PERIOD10'])
        self.leTxPeriod11.setText(self.config['Transmitter']['PERIOD11'])
        self.leTxPeriod12.setText(self.config['Transmitter']['PERIOD12'])
        self.leTxPeriod13.setText(self.config['Transmitter']['PERIOD13'])
        self.leTxPeriod14.setText(self.config['Transmitter']['PERIOD14'])
        self.leTxPeriod15.setText(self.config['Transmitter']['PERIOD15'])
        self.leTxPeriod16.setText(self.config['Transmitter']['PERIOD16'])
        self.leTxPeriod17.setText(self.config['Transmitter']['PERIOD17'])
        self.leTxPeriod18.setText(self.config['Transmitter']['PERIOD18'])
        self.leTxPeriod19.setText(self.config['Transmitter']['PERIOD19'])
        self.leTxPeriod20.setText(self.config['Transmitter']['PERIOD20'])

    def btn_save_click_handler(self):
        self.config['Transmitter']['ID01'] = self.leTxId01.text()
        self.config['Transmitter']['ID02'] = self.leTxId02.text()
        self.config['Transmitter']['ID03'] = self.leTxId03.text()
        self.config['Transmitter']['ID04'] = self.leTxId04.text()
        self.config['Transmitter']['ID05'] = self.leTxId05.text()
        self.config['Transmitter']['ID06'] = self.leTxId06.text()
        self.config['Transmitter']['ID07'] = self.leTxId07.text()
        self.config['Transmitter']['ID08'] = self.leTxId08.text()
        self.config['Transmitter']['ID09'] = self.leTxId09.text()
        self.config['Transmitter']['ID10'] = self.leTxId10.text()
        self.config['Transmitter']['ID11'] = self.leTxId11.text()
        self.config['Transmitter']['ID12'] = self.leTxId12.text()
        self.config['Transmitter']['ID13'] = self.leTxId13.text()
        self.config['Transmitter']['ID14'] = self.leTxId14.text()
        self.config['Transmitter']['ID15'] = self.leTxId15.text()
        self.config['Transmitter']['ID16'] = self.leTxId16.text()
        self.config['Transmitter']['ID17'] = self.leTxId17.text()
        self.config['Transmitter']['ID18'] = self.leTxId18.text()
        self.config['Transmitter']['ID19'] = self.leTxId19.text()
        self.config['Transmitter']['ID20'] = self.leTxId20.text()
        # -------------------------------------------------------
        self.config['Transmitter']['DLC01'] = self.leTxDlc01.text()
        self.config['Transmitter']['DLC02'] = self.leTxDlc02.text()
        self.config['Transmitter']['DLC03'] = self.leTxDlc03.text()
        self.config['Transmitter']['DLC04'] = self.leTxDlc04.text()
        self.config['Transmitter']['DLC05'] = self.leTxDlc05.text()
        self.config['Transmitter']['DLC06'] = self.leTxDlc06.text()
        self.config['Transmitter']['DLC07'] = self.leTxDlc07.text()
        self.config['Transmitter']['DLC08'] = self.leTxDlc08.text()
        self.config['Transmitter']['DLC09'] = self.leTxDlc09.text()
        self.config['Transmitter']['DLC10'] = self.leTxDlc10.text()
        self.config['Transmitter']['DLC11'] = self.leTxDlc11.text()
        self.config['Transmitter']['DLC12'] = self.leTxDlc12.text()
        self.config['Transmitter']['DLC13'] = self.leTxDlc13.text()
        self.config['Transmitter']['DLC14'] = self.leTxDlc14.text()
        self.config['Transmitter']['DLC15'] = self.leTxDlc15.text()
        self.config['Transmitter']['DLC16'] = self.leTxDlc16.text()
        self.config['Transmitter']['DLC17'] = self.leTxDlc17.text()
        self.config['Transmitter']['DLC18'] = self.leTxDlc18.text()
        self.config['Transmitter']['DLC19'] = self.leTxDlc19.text()
        self.config['Transmitter']['DLC20'] = self.leTxDlc20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['D0_01'] = self.leTxD0_01.text()
        self.config['Transmitter']['D0_02'] = self.leTxD0_02.text()
        self.config['Transmitter']['D0_03'] = self.leTxD0_03.text()
        self.config['Transmitter']['D0_04'] = self.leTxD0_04.text()
        self.config['Transmitter']['D0_05'] = self.leTxD0_05.text()
        self.config['Transmitter']['D0_06'] = self.leTxD0_06.text()
        self.config['Transmitter']['D0_07'] = self.leTxD0_07.text()
        self.config['Transmitter']['D0_08'] = self.leTxD0_08.text()
        self.config['Transmitter']['D0_09'] = self.leTxD0_09.text()
        self.config['Transmitter']['D0_10'] = self.leTxD0_10.text()
        self.config['Transmitter']['D0_11'] = self.leTxD0_11.text()
        self.config['Transmitter']['D0_12'] = self.leTxD0_12.text()
        self.config['Transmitter']['D0_13'] = self.leTxD0_13.text()
        self.config['Transmitter']['D0_14'] = self.leTxD0_14.text()
        self.config['Transmitter']['D0_15'] = self.leTxD0_15.text()
        self.config['Transmitter']['D0_16'] = self.leTxD0_16.text()
        self.config['Transmitter']['D0_17'] = self.leTxD0_17.text()
        self.config['Transmitter']['D0_18'] = self.leTxD0_18.text()
        self.config['Transmitter']['D0_19'] = self.leTxD0_19.text()
        self.config['Transmitter']['D0_20'] = self.leTxD0_20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['D1_01'] = self.leTxD1_01.text()
        self.config['Transmitter']['D1_02'] = self.leTxD1_02.text()
        self.config['Transmitter']['D1_03'] = self.leTxD1_03.text()
        self.config['Transmitter']['D1_04'] = self.leTxD1_04.text()
        self.config['Transmitter']['D1_05'] = self.leTxD1_05.text()
        self.config['Transmitter']['D1_06'] = self.leTxD1_06.text()
        self.config['Transmitter']['D1_07'] = self.leTxD1_07.text()
        self.config['Transmitter']['D1_08'] = self.leTxD1_08.text()
        self.config['Transmitter']['D1_09'] = self.leTxD1_09.text()
        self.config['Transmitter']['D1_10'] = self.leTxD1_10.text()
        self.config['Transmitter']['D1_11'] = self.leTxD1_11.text()
        self.config['Transmitter']['D1_12'] = self.leTxD1_12.text()
        self.config['Transmitter']['D1_13'] = self.leTxD1_13.text()
        self.config['Transmitter']['D1_14'] = self.leTxD1_14.text()
        self.config['Transmitter']['D1_15'] = self.leTxD1_15.text()
        self.config['Transmitter']['D1_16'] = self.leTxD1_16.text()
        self.config['Transmitter']['D1_17'] = self.leTxD1_17.text()
        self.config['Transmitter']['D1_18'] = self.leTxD1_18.text()
        self.config['Transmitter']['D1_19'] = self.leTxD1_19.text()
        self.config['Transmitter']['D1_20'] = self.leTxD1_20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['D2_01'] = self.leTxD2_01.text()
        self.config['Transmitter']['D2_02'] = self.leTxD2_02.text()
        self.config['Transmitter']['D2_03'] = self.leTxD2_03.text()
        self.config['Transmitter']['D2_04'] = self.leTxD2_04.text()
        self.config['Transmitter']['D2_05'] = self.leTxD2_05.text()
        self.config['Transmitter']['D2_06'] = self.leTxD2_06.text()
        self.config['Transmitter']['D2_07'] = self.leTxD2_07.text()
        self.config['Transmitter']['D2_08'] = self.leTxD2_08.text()
        self.config['Transmitter']['D2_09'] = self.leTxD2_09.text()
        self.config['Transmitter']['D2_10'] = self.leTxD2_10.text()
        self.config['Transmitter']['D2_11'] = self.leTxD2_11.text()
        self.config['Transmitter']['D2_12'] = self.leTxD2_12.text()
        self.config['Transmitter']['D2_13'] = self.leTxD2_13.text()
        self.config['Transmitter']['D2_14'] = self.leTxD2_14.text()
        self.config['Transmitter']['D2_15'] = self.leTxD2_15.text()
        self.config['Transmitter']['D2_16'] = self.leTxD2_16.text()
        self.config['Transmitter']['D2_17'] = self.leTxD2_17.text()
        self.config['Transmitter']['D2_18'] = self.leTxD2_18.text()
        self.config['Transmitter']['D2_19'] = self.leTxD2_19.text()
        self.config['Transmitter']['D2_20'] = self.leTxD2_20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['D3_01'] = self.leTxD3_01.text()
        self.config['Transmitter']['D3_02'] = self.leTxD3_02.text()
        self.config['Transmitter']['D3_03'] = self.leTxD3_03.text()
        self.config['Transmitter']['D3_04'] = self.leTxD3_04.text()
        self.config['Transmitter']['D3_05'] = self.leTxD3_05.text()
        self.config['Transmitter']['D3_06'] = self.leTxD3_06.text()
        self.config['Transmitter']['D3_07'] = self.leTxD3_07.text()
        self.config['Transmitter']['D3_08'] = self.leTxD3_08.text()
        self.config['Transmitter']['D3_09'] = self.leTxD3_09.text()
        self.config['Transmitter']['D3_10'] = self.leTxD3_10.text()
        self.config['Transmitter']['D3_11'] = self.leTxD3_11.text()
        self.config['Transmitter']['D3_12'] = self.leTxD3_12.text()
        self.config['Transmitter']['D3_13'] = self.leTxD3_13.text()
        self.config['Transmitter']['D3_14'] = self.leTxD3_14.text()
        self.config['Transmitter']['D3_15'] = self.leTxD3_15.text()
        self.config['Transmitter']['D3_16'] = self.leTxD3_16.text()
        self.config['Transmitter']['D3_17'] = self.leTxD3_17.text()
        self.config['Transmitter']['D3_18'] = self.leTxD3_18.text()
        self.config['Transmitter']['D3_19'] = self.leTxD3_19.text()
        self.config['Transmitter']['D3_20'] = self.leTxD3_20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['D4_01'] = self.leTxD4_01.text()
        self.config['Transmitter']['D4_02'] = self.leTxD4_02.text()
        self.config['Transmitter']['D4_03'] = self.leTxD4_03.text()
        self.config['Transmitter']['D4_04'] = self.leTxD4_04.text()
        self.config['Transmitter']['D4_05'] = self.leTxD4_05.text()
        self.config['Transmitter']['D4_06'] = self.leTxD4_06.text()
        self.config['Transmitter']['D4_07'] = self.leTxD4_07.text()
        self.config['Transmitter']['D4_08'] = self.leTxD4_08.text()
        self.config['Transmitter']['D4_09'] = self.leTxD4_09.text()
        self.config['Transmitter']['D4_10'] = self.leTxD4_10.text()
        self.config['Transmitter']['D4_11'] = self.leTxD4_11.text()
        self.config['Transmitter']['D4_12'] = self.leTxD4_12.text()
        self.config['Transmitter']['D4_13'] = self.leTxD4_13.text()
        self.config['Transmitter']['D4_14'] = self.leTxD4_14.text()
        self.config['Transmitter']['D4_15'] = self.leTxD4_15.text()
        self.config['Transmitter']['D4_16'] = self.leTxD4_16.text()
        self.config['Transmitter']['D4_17'] = self.leTxD4_17.text()
        self.config['Transmitter']['D4_18'] = self.leTxD4_18.text()
        self.config['Transmitter']['D4_19'] = self.leTxD4_19.text()
        self.config['Transmitter']['D4_20'] = self.leTxD4_20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['D5_01'] = self.leTxD5_01.text()
        self.config['Transmitter']['D5_02'] = self.leTxD5_02.text()
        self.config['Transmitter']['D5_03'] = self.leTxD5_03.text()
        self.config['Transmitter']['D5_04'] = self.leTxD5_04.text()
        self.config['Transmitter']['D5_05'] = self.leTxD5_05.text()
        self.config['Transmitter']['D5_06'] = self.leTxD5_06.text()
        self.config['Transmitter']['D5_07'] = self.leTxD5_07.text()
        self.config['Transmitter']['D5_08'] = self.leTxD5_08.text()
        self.config['Transmitter']['D5_09'] = self.leTxD5_09.text()
        self.config['Transmitter']['D5_10'] = self.leTxD5_10.text()
        self.config['Transmitter']['D5_11'] = self.leTxD5_11.text()
        self.config['Transmitter']['D5_12'] = self.leTxD5_12.text()
        self.config['Transmitter']['D5_13'] = self.leTxD5_13.text()
        self.config['Transmitter']['D5_14'] = self.leTxD5_14.text()
        self.config['Transmitter']['D5_15'] = self.leTxD5_15.text()
        self.config['Transmitter']['D5_16'] = self.leTxD5_16.text()
        self.config['Transmitter']['D5_17'] = self.leTxD5_17.text()
        self.config['Transmitter']['D5_18'] = self.leTxD5_18.text()
        self.config['Transmitter']['D5_19'] = self.leTxD5_19.text()
        self.config['Transmitter']['D5_20'] = self.leTxD5_20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['D6_01'] = self.leTxD6_01.text()
        self.config['Transmitter']['D6_02'] = self.leTxD6_02.text()
        self.config['Transmitter']['D6_03'] = self.leTxD6_03.text()
        self.config['Transmitter']['D6_04'] = self.leTxD6_04.text()
        self.config['Transmitter']['D6_05'] = self.leTxD6_05.text()
        self.config['Transmitter']['D6_06'] = self.leTxD6_06.text()
        self.config['Transmitter']['D6_07'] = self.leTxD6_07.text()
        self.config['Transmitter']['D6_08'] = self.leTxD6_08.text()
        self.config['Transmitter']['D6_09'] = self.leTxD6_09.text()
        self.config['Transmitter']['D6_10'] = self.leTxD6_10.text()
        self.config['Transmitter']['D6_11'] = self.leTxD6_11.text()
        self.config['Transmitter']['D6_12'] = self.leTxD6_12.text()
        self.config['Transmitter']['D6_13'] = self.leTxD6_13.text()
        self.config['Transmitter']['D6_14'] = self.leTxD6_14.text()
        self.config['Transmitter']['D6_15'] = self.leTxD6_15.text()
        self.config['Transmitter']['D6_16'] = self.leTxD6_16.text()
        self.config['Transmitter']['D6_17'] = self.leTxD6_17.text()
        self.config['Transmitter']['D6_18'] = self.leTxD6_18.text()
        self.config['Transmitter']['D6_19'] = self.leTxD6_19.text()
        self.config['Transmitter']['D6_20'] = self.leTxD6_20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['D7_01'] = self.leTxD7_01.text()
        self.config['Transmitter']['D7_02'] = self.leTxD7_02.text()
        self.config['Transmitter']['D7_03'] = self.leTxD7_03.text()
        self.config['Transmitter']['D7_04'] = self.leTxD7_04.text()
        self.config['Transmitter']['D7_05'] = self.leTxD7_05.text()
        self.config['Transmitter']['D7_06'] = self.leTxD7_06.text()
        self.config['Transmitter']['D7_07'] = self.leTxD7_07.text()
        self.config['Transmitter']['D7_08'] = self.leTxD7_08.text()
        self.config['Transmitter']['D7_09'] = self.leTxD7_09.text()
        self.config['Transmitter']['D7_10'] = self.leTxD7_10.text()
        self.config['Transmitter']['D7_11'] = self.leTxD7_11.text()
        self.config['Transmitter']['D7_12'] = self.leTxD7_12.text()
        self.config['Transmitter']['D7_13'] = self.leTxD7_13.text()
        self.config['Transmitter']['D7_14'] = self.leTxD7_14.text()
        self.config['Transmitter']['D7_15'] = self.leTxD7_15.text()
        self.config['Transmitter']['D7_16'] = self.leTxD7_16.text()
        self.config['Transmitter']['D7_17'] = self.leTxD7_17.text()
        self.config['Transmitter']['D7_18'] = self.leTxD7_18.text()
        self.config['Transmitter']['D7_19'] = self.leTxD7_19.text()
        self.config['Transmitter']['D7_20'] = self.leTxD7_20.text()
        # ---------------------------------------------------------
        self.config['Transmitter']['PERIOD01'] = self.leTxPeriod01.text()
        self.config['Transmitter']['PERIOD02'] = self.leTxPeriod02.text()
        self.config['Transmitter']['PERIOD03'] = self.leTxPeriod03.text()
        self.config['Transmitter']['PERIOD04'] = self.leTxPeriod04.text()
        self.config['Transmitter']['PERIOD05'] = self.leTxPeriod05.text()
        self.config['Transmitter']['PERIOD06'] = self.leTxPeriod06.text()
        self.config['Transmitter']['PERIOD07'] = self.leTxPeriod07.text()
        self.config['Transmitter']['PERIOD08'] = self.leTxPeriod08.text()
        self.config['Transmitter']['PERIOD09'] = self.leTxPeriod09.text()
        self.config['Transmitter']['PERIOD10'] = self.leTxPeriod10.text()
        self.config['Transmitter']['PERIOD11'] = self.leTxPeriod11.text()
        self.config['Transmitter']['PERIOD12'] = self.leTxPeriod12.text()
        self.config['Transmitter']['PERIOD13'] = self.leTxPeriod13.text()
        self.config['Transmitter']['PERIOD14'] = self.leTxPeriod14.text()
        self.config['Transmitter']['PERIOD15'] = self.leTxPeriod15.text()
        self.config['Transmitter']['PERIOD16'] = self.leTxPeriod16.text()
        self.config['Transmitter']['PERIOD17'] = self.leTxPeriod17.text()
        self.config['Transmitter']['PERIOD18'] = self.leTxPeriod18.text()
        self.config['Transmitter']['PERIOD19'] = self.leTxPeriod19.text()
        self.config['Transmitter']['PERIOD20'] = self.leTxPeriod20.text()

        with open('ecu.ini', 'w') as configfile:
            self.config.write(configfile)

    def load_lookup(self):
        # ID, Description, Start Byte, Start Bit, End Byte, End Bit, Type, Coficient, Operator, Unit, Value, Name
        self.LookUp.append(["40F", "TPMS System Status", "0", "0", "0", "2", "option", "", "", "", "0", "Normal"])
        self.LookUp.append(["40F", "TPMS System Status", "0", "0", "0", "2", "option", "", "", "", "1", "Reserved"])
        self.LookUp.append(["40F", "TPMS System Status", "0", "0", "0", "2", "option", "", "", "", "2", "System Error"])
        self.LookUp.append(["40F", "TPMS System Status", "0", "0", "0", "2", "option", "", "", "", "3", "Reserved"])
        self.LookUp.append(["40F", "TPMS System Status", "0", "0", "0", "2", "option", "", "", "", "4", "Reserved"])
        self.LookUp.append(["40F", "TPMS System Status", "0", "0", "0", "2", "option", "", "", "", "5", "Reserved"])
        self.LookUp.append(["40F", "TPMS System Status", "0", "0", "0", "2", "option", "", "", "", "6", "Reserved"])
        self.LookUp.append(["40F", "TPMS System Status", "0", "0", "0", "2", "option", "", "", "", "7", "Reserved"])

        self.LookUp.append(["40F", "The ID of Tire", "0", "4", "0", "6", "option", "", "", "", "0", "Rear Right"])
        self.LookUp.append(["40F", "The ID of Tire", "0", "4", "0", "6", "option", "", "", "", "1", "Front Right"])
        self.LookUp.append(["40F", "The ID of Tire", "0", "4", "0", "6", "option", "", "", "", "2", "Rear Left"])
        self.LookUp.append(["40F", "The ID of Tire", "0", "4", "0", "6", "option", "", "", "", "3", "Front Left"])
        self.LookUp.append(["40F", "The ID of Tire", "0", "4", "0", "6", "option", "", "", "", "4", "Reserved"])
        self.LookUp.append(["40F", "The ID of Tire", "0", "4", "0", "6", "option", "", "", "", "5", "Reserved"])
        self.LookUp.append(["40F", "The ID of Tire", "0", "4", "0", "6", "option", "", "", "", "6", "Reserved"])
        self.LookUp.append(["40F", "The ID of Tire", "0", "4", "0", "6", "option", "", "", "", "7", "Reserved"])

        self.LookUp.append(["40F", "The Tire Information", "0", "7", "0", "7", "option", "", "", "", "0", "Normal"])
        self.LookUp.append(["40F", "The Tire Information", "0", "7", "0", "7", "option", "", "", "", "1", "Abnormal"])

        self.LookUp.append(["40F", "The Tire Leakage", "1", "0", "1", "1", "option", "", "", "", "0", "Normal"])
        self.LookUp.append(["40F", "The Tire Leakage", "1", "0", "1", "1", "option", "", "", "", "1", "Quick Leak"])
        self.LookUp.append(["40F", "The Tire Leakage", "1", "0", "1", "1", "option", "", "", "", "2", "Reserved"])
        self.LookUp.append(["40F", "The Tire Leakage", "1", "0", "1", "1", "option", "", "", "", "3", "Reserved"])

        self.LookUp.append(["40F", "The Tire Learning Status", "1", "2", "1", "3", "option", "", "", "", "0", "Not Learned"])
        self.LookUp.append(["40F", "The Tire Learning Status", "1", "2", "1", "3", "option", "", "", "", "1", "Learning"])
        self.LookUp.append(["40F", "The Tire Learning Status", "1", "2", "1", "3", "option", "", "", "", "2", "Learn Completed"])
        self.LookUp.append(["40F", "The Tire Learning Status", "1", "2", "1", "3", "option", "", "", "", "3", "Learning Failure"])

        self.LookUp.append(["40F", "The Tire Pressure Status", "1", "4", "1", "5", "option", "", "", "", "0", "Normal"])
        self.LookUp.append(["40F", "The Tire Pressure Status", "1", "4", "1", "5", "option", "", "", "", "1", "Over Pressure"])
        self.LookUp.append(["40F", "The Tire Pressure Status", "1", "4", "1", "5", "option", "", "", "", "2", "Under Pressure"])
        self.LookUp.append(["40F", "The Tire Pressure Status", "1", "4", "1", "5", "option", "", "", "", "3", "Reserved"])

        self.LookUp.append(["40F", "The Tire Temperature Status", "1", "6", "1", "7", "option", "", "", "", "0", "Normal"])
        self.LookUp.append(["40F", "The Tire Temperature Status", "1", "6", "1", "7", "option", "", "", "", "1", "Reserved"])
        self.LookUp.append(["40F", "The Tire Temperature Status", "1", "6", "1", "7", "option", "", "", "", "2", "High Temperature"])
        self.LookUp.append(["40F", "The Tire Temperature Status", "1", "6", "1", "7", "option", "", "", "", "3", "Reserved"])

        self.LookUp.append(["40F", "The Tire Pressure", "2", "0", "2", "7", "scalar", "1.3725", "*", " kPa", "", ""])

        self.LookUp.append(["40F", "The Tire Temperature", "3", "0", "3", "7", "scalar", "40", "-", " C", "", ""])

        self.LookUp.append(["40F", "The Tire Battery Power Status", "4", "0", "4", "7", "option", "", "", "", "0", "Normal"])
        self.LookUp.append(["40F", "The Tire Battery Power Status", "4", "0", "4", "7", "option", "", "", "", "1", "Low Power"])
        self.LookUp.append(["40F", "The Tire Battery Power Status", "4", "0", "4", "7", "option", "", "", "", "2", "Reserved"])
        self.LookUp.append(["40F", "The Tire Battery Power Status", "4", "0", "4", "7", "option", "", "", "", "3", "Reserved"])

        for i in range(int("0" + "7", 8), int("0" + "7", 8) + 1):
            a = str(oct(i))
            a = a[2:]
            if len(a) < 2:
                a = "0" + a
            print(a[0:1], "-", a[1:2])

    def extract_message(self, id, d0, d1, d2, d3, d4, d5, d6, d7):
        D0Bin = (bin(int(d0, 16))[2:]).zfill(8)
        D1Bin = (bin(int(d1, 16))[2:]).zfill(8)
        D2Bin = (bin(int(d2, 16))[2:]).zfill(8)
        D3Bin = (bin(int(d3, 16))[2:]).zfill(8)
        D4Bin = (bin(int(d4, 16))[2:]).zfill(8)
        D5Bin = (bin(int(d5, 16))[2:]).zfill(8)
        D6Bin = (bin(int(d6, 16))[2:]).zfill(8)
        D7Bin = (bin(int(d7, 16))[2:]).zfill(8)

        ConcatenatedBin = D7Bin + D6Bin + D5Bin + D4Bin + D3Bin + D2Bin + D1Bin + D0Bin

        # ConcatenatedBin = "7654321076543210765432107654321076543210765432107654321076543210"
        print(ConcatenatedBin)

        message = [[0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0]]

        j = 0
        k = -1
        l = 0
        for i in range(64, 0, -1):
            j = i - 1
            k = k + 1
            if k > 7:
                k = 0
                l = l + 1

            # print(l, k, j, i)
            message[l][k] = ConcatenatedBin[j:i]  # filling the dataset with received message
            print("D[{}][{}] = {}".format(l, k, message[l][k]))

        print(message)

        j = 0

        print(self.LookUp)

        for row in self.LookUp:
            row_id = row[0]
            if row_id == id:
                description = row[1]
                startByte = row[2]
                startBit = row[3]
                endByte = row[4]
                endBit = row[5]
                row_type = row[6]
                coficient = row[7]
                row_operator = row[8]
                unit = row[9]
                lookupValue = row[10]
                row_name = row[11]


                #print(startByte, startByte, endByte, endBit)

                binValue = ""
                for a in range(int(startByte + startBit, 8), int(endByte + endBit, 8) + 1):
                    b = str(oct(a))
                    b = b[2:]
                    if len(b) < 2:
                        b = "0" + b

                    binValue = binValue + message[int(b[0:1])][int(b[1:2])]

                decValue = int(binValue, 2)

                if row_type == "option":
                    if int(decValue) == int(lookupValue):
                        print("message[{}][{}]= {} - {} - {} - Description= {}: {}".format(b[0:1], b[1:2], binValue, decValue, lookupValue ,  description, row_name))
                        print("==================================================")
                else:
                    pass


