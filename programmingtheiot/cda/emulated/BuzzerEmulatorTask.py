#####
#
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
#

import logging
import os
import pygame
from programmingtheiot.cda.sim.BaseActuatorSimTask import BaseActuatorSimTask
import programmingtheiot.common.ConfigConst as ConfigConst


class BuzzerEmulatorTask(BaseActuatorSimTask):
	"""
	Sound Actuator Emulator
	Plays distinct WAV files for Activation (Open) and Deactivation (Close).
	"""

	def __init__(self):
		super(BuzzerEmulatorTask, self).__init__(
			name=ConfigConst.BUZZER_ACTUATOR_NAME,
			typeID=ConfigConst.BUZZER_ACTUATOR_TYPE,
			simpleName="BUZZER"
		)

		self.has_audio = False
		self.sound_open = None
		self.sound_close = None

		# Initialize pygame
		try:
			pygame.mixer.init()

			# Use absolute paths to ensure files are found correctly
			base_path = os.path.dirname(os.path.abspath(__file__))
			path_open = os.path.join(base_path, "zelda_botw_get_item.wav")
			path_close = os.path.join(base_path, "zelda_puzzle_solved.wav")

			if os.path.exists(path_open) and os.path.exists(path_close):
				self.sound_open = pygame.mixer.Sound(path_open)
				self.sound_close = pygame.mixer.Sound(path_close)
				self.has_audio = True
				logging.info(f"Sound assets loaded: {path_open}")
			else:
				logging.warning(f"Sound files not found at: {base_path}. Audio will be disabled.")

		except Exception as e:
			logging.warning(f"Failed to initialize sound system (Headless mode?): {e}")
			self.has_audio = False

	def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		"""
		Action: Window Open (Closed -> Open)
		"""
		if self.has_audio and self.sound_open:
			logging.info("Playing Open Sound: zelda_botw_get_item.wav")
			self.sound_open.play()
		else:
			logging.info("Simulating Buzzer ON (No Audio Hardware/Files)")

		return 0  # Always return 0 to indicate the command was processed

	def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		"""
		Action: Window Close (Open -> Closed)
		"""
		if self.has_audio and self.sound_close:
			logging.info("Playing Close Sound: zelda_puzzle_solved.wav")
			self.sound_close.play()
		else:
			logging.info("Simulating Buzzer OFF (No Audio Hardware/Files)")

		return 0  # Always return 0 to indicate the command was processed