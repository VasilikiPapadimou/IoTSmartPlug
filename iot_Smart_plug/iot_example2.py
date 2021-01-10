#All the libraries we need to create tha programm for smartplug.
import paho.mqtt.client as mqtt
import ssl
import sys
import os
import matplotlib.pyplot as plt
#We use from to take something specific from a library
from matplotlib.widgets import Button
from threading import Timer
from datetime import datetime

class IoTExample:
	#Method to start with (Main) 
	def __init__(self):
		self.ax = None
		self._establish_mqtt_connection()
		self._prepare_graph_window() #show the changes on the graph
	
	#When do we need/need not MQTT Client to be blocked 
	def start(self):
		if self.ax:
			#NeedNot->end the program, 
			#We don't need to have control of the programs graphics   
			self.client.loop_start()
			plt.show() #show the changes on the graph
		else:
			#Need-> don't end the program and wait for messages
			#call this method to start client loop (without ending)
			self.client.loop_forever()

	# Disconnecion from MQTT Broker		
	def disconnect(self, args=None):
		self.client.disconnect()

	""" Creation of objects ready to connect to the Broker
		How this method is used: 
		self.client.SOMETHING-> creates an object inside this method
	 	self.METHOD -> goes to the method called and runs it.
	"""
	def _establish_mqtt_connection(self):
		self.client = mqtt.Client()
		#When the installation of connection is complete call _on_connect method
		self.client.on_connect = self._on_connect 
		#Creation of diagnostic messages for the MQTT connection
		self.client.on_log = self._on_log
		#Everytime we take a message _on_message from paho is called
		self.client.on_message = self._on_message
		
		print('Trying to connect to MQTT server...')		
		#Cryptography through ssl for receiving/sending messages
		self.client.tls_set_context(ssl.SSLContext(ssl.PROTOCOL_TLSv1_2))
		#We set the password and username
		self.client.username_pw_set('iotlesson', 'YGK0tx5pbtkK2WkCBvJlJWCg')
		#Connection to ntua MQTT Broker (DNS and port we use)
		self.client.connect('phoenix.medialab.ntua.gr', 8883)
	
	#Runs whenever a new connection is established
	def _on_connect(self, client, userdata, flags, rc):
		print('Connect with result code' +str(rc))
		#It shows the power consumtion at an exact time 
		client.subscribe('hscnl/hscnl02/state/ZWaveNode006_ElectricMeterWatts/state')
		# Commands we have sent to the smartplug
		client.subscribe('hscnl/hscnl02/command/ZWaveNode005_Switch/command')
		# it shows if the smartplug is ON/OFF
		client.subscribe('hscnl/hscnl02/state/ZWaveNode005_Switch/state')
	
	#Runs whenever a new message is received
	#show the changes on the graph (line 75)
	def _on_message(self, client, userdata, msg):
		if msg.topic == 'hscnl/hscnl02/state/ZWaveNode005_ElectricMeterWatts/state':
						self._add_value_to_plot(float(msg.payload))
		print(msg.topic+''+str(msg.payload))

	#Runs whenever a new log event is created
	def _on_log(self, client, userdata, level, buf):
		print('log: ', buf)

	#Creation of the whole plot
	def _prepare_graph_window(self):
		# Plot variables initialization
		#Run and Configure =rcParams
		plt.rcParams['toolbar'] = 'None'
		plt.ylabel('Power (Watt)')  
		plt.xlabel('Time') 
		#Create the subplot with  1 raw, 1 col, 1 index from the top left corner
		self.ax = plt.subplot(111)
		self.dataX = []
		self.dataY = []
		self.first_ts = datetime.now()
		#View of the plot data in both Axes
		self.lineplot, = self.ax.plot(
			self.dataX, self.dataY, linestyle='--', marker='o', color='r')
		#When we pres X at the plot canvas, close the whole event.
		self.ax.figure.canvas.mpl_connect('close_event', self.disconnect)
		
		"""	Where to put the ON/OFF Button and the textfield
			left, bottom, width, height
		"""
		axcut = plt.axes([0.12, 0.9, 0.1, 0.06])
		self.bcut = Button(axcut, 'ON')
		axcut2 = plt.axes([0.22, 0.9, 0.1, 0.06])
		self.bcut2 = Button(axcut2, 'OFF')
		self.state_field = plt.text(0.5, 1.3, 'Power consumed by 2 smartplugs within a TimeStep')
		#What action/method to be performed if ON/OFF
		self.bcut.on_clicked(self._button_on_clicked)
		self.bcut2.on_clicked(self._button_off_clicked)

		self.finishing = False
		self._my_timer()

	#For sending ON message to the MQTTBroker from distance
	def _button_on_clicked(self, event):
		self.client.publish(
			'hscnl/hscnl02/sendcommand/ZWaveNode005_Switch', 'ON')

	#For sending OFF message to the MQTTBroker from distance		
	def _button_off_clicked(self, event):
		self.client.publish(
			'hscnl/hscnl02/sendcommand/ZWaveNode005_Switch', 'OFF')

	#To move the plot right every 4sec
	def _my_timer(self):
		self._refresh_plot()
		if not self.finishing:
			Timer(4.0, self._my_timer).start()#........

	#Refreshing the plot when a new result is created
	def _refresh_plot(self):
		if len(self.dataX) > 0:
			self.ax.set_xlim(min(self.first_ts, min(self.dataX)),
							max(max(self.dataX), datetime.now()))
			self.ax.set_ylim(min(self.dataY) * 0.8, max(self.dataY) * 1.2)
			self.ax.relim()
		else:
			self.ax.set_xlim(self.first_ts, datetime.now())
			self.ax.relim()
		plt.draw()

	#To add new value to the plot
	def _add_value_to_plot(self, value):
		self.dataX.append(datetime.now())
		self.dataY.append(value)
		self.lineplot.set_data(self.dataX, self.dataY)
		self._refresh_plot()

try:
	iot_example = IoTExample()
	iot_example.start()
except KeyboardInterrupt:
	print("Interrupted")
	try:
		iot_example.disconnect()
		sys.exit(0)
	except SystemExit:
		os._exit(0)
