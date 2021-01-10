import paho.mqtt.client as mqtt
import ssl
import sys
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from threading import Timer
from datetime import datetime

class IoTExample:
	def __init__(self):
		self.ax = None
		self._establish_mqtt_connection()
		self._prepare_graph_window()
	
	def start(self):
		if self.ax:
			self.client.loop_start()
			plt.show()
		else:
			self.client.loop_forever()
			
	def disconnect(self, args=None):
		self.client.disconnect()

	def _establish_mqtt_connection(self):
		self.client = mqtt.Client()
		self.client.on_connect = self._on_connect
		self.client.on_log = self._on_log
		self.client.on_message = self._on_message

		print('Trying to connect to MQTT server...')
		self.client.tls_set_context(ssl.SSLContext(ssl.PROTOCOL_TLSv1_2))
		self.client.username_pw_set('iotlesson', 'YGK0tx5pbtkK2WkCBvJlJWCg')
		self.client.connect('phoenix.medialab.ntua.gr', 8883)
		

	def _on_connect(self, client, userdata, flags, rc):
		print('Connect with result code' +str(rc))
		client.subscribe('hscnl/hscnl02/state/ZWaveNode006_ElectricMeterWatts/state')
		client.subscribe('hscnl/hscnl02/command/ZWaveNode006_Switch/command')
		client.subscribe('hscnl/hscnl02/state/ZWaveNode006_Switch/state')

	def _on_message(self, client, userdata, msg):
		if msg.topic == 'hscnl/hscnl02/state/ZWaveNode006_ElectricMeterWatts/state':
						self._add_value_to_plot(float(msg.payload))
		print(msg.topic+''+str(msg.payload))

	def _on_log(self, client, userdata, level, buf):
		print('log: ', buf)


	def _prepare_graph_window(self):
# Plot variables
		plt.rcParams['toolbar'] = 'None'
		plt.ylabel('Watts')#......
		plt.xlabel('Timestep')#......
		self.ax = plt.subplot(111)
		self.dataX = []
		self.dataY = []
		self.first_ts = datetime.now()
		self.lineplot, = self.ax.plot(
			self.dataX, self.dataY, linestyle='--', marker='o', color='g')#........
		self.ax.figure.canvas.mpl_connect('close_event', self.disconnect)

		axcut = plt.axes([0.0, 0.0, 0.1, 0.06])
		self.bcut = Button(axcut, 'ON')
		axcut2 = plt.axes([0.1, 0.0, 0.1, 0.06])
		self.bcut2 = Button(axcut2, 'OFF')
		self.state_field = plt.text(1.5, 0.3, 'STATE: -')
		self.bcut.on_clicked(self._button_on_clicked)
		self.bcut2.on_clicked(self._button_off_clicked)

		self.finishing = False
		self._my_timer()


	def _button_on_clicked(self, event):
		self.client.publish(
			'hscnl/hscnl02/sendcommand/ZWaveNode005_Switch', 'ON')
	def _button_off_clicked(self, event):
		self.client.publish(
			'hscnl/hscnl02/sendcommand/ZWaveNode005_Switch', 'OFF')

	def _my_timer(self):
		self._refresh_plot()
		if not self.finishing:
			Timer(1.0, self._my_timer).start()#........

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
