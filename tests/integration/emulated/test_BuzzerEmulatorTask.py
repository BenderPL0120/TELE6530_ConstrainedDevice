#####
#
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
#
# Copyright (c) 2020 - 2025 by Andrew D. King
#

import logging
import unittest

from time import sleep

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.data.ActuatorData import ActuatorData
from programmingtheiot.cda.emulated.BuzzerEmulatorTask import BuzzerEmulatorTask


class BuzzerEmulatorTaskTest(unittest.TestCase):
	"""
	This test case class contains very basic unit tests for
	BuzzerEmulatorTask. It should not be considered complete,
	but serve as a starting point for the student implementing
	additional functionality within their Programming the IoT
	environment.

	NOTE: This test requires pygame to be installed and audio
	drivers to be functioning to hear the output.

	"""

	@classmethod
	def setUpClass(self):
		logging.basicConfig(format='%(asctime)s:%(module)s:%(levelname)s:%(message)s', level=logging.DEBUG)
		logging.info("Testing BuzzerEmulatorTask class...")
		self.bSimTask = BuzzerEmulatorTask()

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def testUpdateEmulator(self):
		# Test ON (Activation - Should play 'Open' sound)
		ad = ActuatorData(typeID=ConfigConst.BUZZER_ACTUATOR_TYPE)
		ad.setCommand(ConfigConst.COMMAND_ON)
		ad.setValue(1.0)

		logging.info("Sending COMMAND_ON to Buzzer...")
		adr = self.bSimTask.updateActuator(ad)

		if adr:
			self.assertEqual(adr.getCommand(), ConfigConst.COMMAND_ON)
			self.assertEqual(adr.getStatusCode(), 0)
			logging.info("ActuatorData: " + str(adr))

			# wait 5 seconds to let the sound play
			sleep(5)
		else:
			logging.warning("ActuatorData is None.")

		# Test OFF (Deactivation - Should play 'Close' sound)
		ad.setCommand(ConfigConst.COMMAND_OFF)

		logging.info("Sending COMMAND_OFF to Buzzer...")
		adr = self.bSimTask.updateActuator(ad)

		if adr:
			self.assertEqual(adr.getCommand(), ConfigConst.COMMAND_OFF)
			self.assertEqual(adr.getStatusCode(), 0)
			logging.info("ActuatorData: " + str(adr))

			# wait 5 seconds to let the sound play
			sleep(5)
		else:
			logging.warning("ActuatorData is None.")


if __name__ == "__main__":
	unittest.main()