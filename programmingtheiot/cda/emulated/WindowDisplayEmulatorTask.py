#####
#
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
#

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseActuatorSimTask import BaseActuatorSimTask

from pisense import SenseHAT, array
from colorzero import Color


class WindowDisplayEmulatorTask(BaseActuatorSimTask):
  """
  Window actuator emulator that displays window state on SenseHAT LED matrix.

  Visual indicators (UPDATED):
  - Window OPEN:   Vertical line (|) in GREEN
  - Window CLOSED: Diagonal line (/) in RED
  """

  def __init__(self):
    super(
      WindowDisplayEmulatorTask, self).__init__(
      name=ConfigConst.WINDOW_ACTUATOR_NAME,
      typeID=ConfigConst.WINDOW_ACTUATOR_TYPE,
      simpleName="WINDOW")

    enableEmulation = \
      ConfigUtil().getBoolean(
        ConfigConst.CONSTRAINED_DEVICE, ConfigConst.ENABLE_EMULATOR_KEY)

    self.sh = SenseHAT(emulate=enableEmulation)

    # Define colors
    self.colorOpen = Color('green')
    self.colorClosed = Color('red')
    self.colorOff = Color('black')

    # Track current state for refresh capability
    self.isWindowOpen = False

  def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
    """
    Activate actuator - Open the window.
    Displays a vertical line (|) pattern in green.
    """
    if self.sh.screen:
      self.isWindowOpen = True
      self._drawOpenPattern()
      return 0
    else:
      return -1

  def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
    """
    Deactivate actuator - Close the window.
    Displays a diagonal line (/) pattern in red.
    """
    if self.sh.screen:
      self.isWindowOpen = False
      self._drawClosedPattern()
      return 0
    else:
      return -1

  def _drawOpenPattern(self):
    """
    Draw vertical line (|) pattern representing open window.
    """
    # Create 8x8 black background
    pixels = array(self.colorOff)

    # Draw vertical line in the center (column 3 and 4) using Green
    for i in range(8):
      pixels[i, 3] = self.colorOpen
      pixels[i, 4] = self.colorOpen

    self.sh.screen.array = pixels

  def _drawClosedPattern(self):
    """
    Draw diagonal line (/) pattern representing closed window.
    """
    # Create 8x8 black background
    pixels = array(self.colorOff)

    # Draw diagonal line from bottom-left to top-right using Red
    for i in range(8):
      pixels[i, 7 - i] = self.colorClosed

    self.sh.screen.array = pixels

  def refreshDisplay(self):
    """
    Refresh the window state display.
    Call this after other actuators finish their scroll_text animations
    to restore the window status icon.
    """
    if self.sh.screen:
      if self.isWindowOpen:
        self._drawOpenPattern()
      else:
        self._drawClosedPattern()

  def clearDisplay(self):
    """
    Clear the LED display.
    """
    if self.sh.screen:
      self.sh.screen.clear()