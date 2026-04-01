#include <Wire.h>
#include <7semi_MAX17048.h>

MAX17048_7semi battery;
unsigned long batteryTimer;
bool debugBattery = false;

bool debugButtons = false;
const int NUM_DEBUG_PINS = 12;
const int DEBUG_PINS[NUM_DEBUG_PINS] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13};
int lastDebugState[NUM_DEBUG_PINS];
unsigned long debugTimer;

const int buttonPins[6] = {13, 12, 11, 10, 9, 8}; // Braille buttons
const int buttonPinToggle = 7;
const int buttonPinClearAll = 6;
const int buttonPinBackspace = 5;
const int buttonPinOriginalSent = 4;
const int buttonPinCorrectedSent = 3;
const int buttonPinOK = 2;

static bool braillePatternStableState[6] = {false, false, false, false, false, false}; // Stable state used for pattern calculation (Updated only when a stable change is detected)
// static int braillePatternButtonsState[6] = {-1, -1, -1, -1, -1, -1}; // Real-time state (Updated during pattern calculation specifically)
static bool lastBraillePatternButtonsState[6] = {false, false, false, false, false, false}; // Previous state (Updated before pattern calculation to track changes)
static unsigned long lastTimeBraillePatternButtonsStateChanged[6] = {0, 0, 0, 0, 0, 0};

enum BrailleMode
{
  LOWERCASE,
  UPPERCASE,
  NUMERIC
};

BrailleMode currentMode = LOWERCASE;

// Debounce timing
const unsigned long DEBOUNCE_MS = 50; // 50ms debounce window for switches

void setup()
{
  Serial.begin(9600);
  Wire.begin();

  batteryTimer = millis();
  debugTimer = millis();

  if (!battery.begin(&Wire))
  {
    Serial.println("MAX17048 not detected. Check wiring.");
    debugBattery = false; // Disable battery monitoring
    // Continue running - braille input still works
  }
  else
  {
    Serial.println("MAX17048 initialized");

    // Set alert voltage range (e.g., 3.2V min, 4.2V max)
    battery.setVoltageLimits(3.2, 4.2);
    // Note: quickStart() not needed if QS/GND already shorted on PCB
  }

  for (int i = 0; i < 6; i++)
  {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }
  pinMode(buttonPinBackspace, INPUT_PULLUP);
  pinMode(buttonPinOK, INPUT_PULLUP);
  pinMode(buttonPinToggle, INPUT_PULLUP);
  pinMode(buttonPinOriginalSent, INPUT_PULLUP);
  pinMode(buttonPinCorrectedSent, INPUT_PULLUP);
  pinMode(buttonPinClearAll, INPUT_PULLUP);

  // Initialize debug pins
  for (int i = 0; i < NUM_DEBUG_PINS; i++)
  {
    pinMode(DEBUG_PINS[i], INPUT_PULLUP);
    lastDebugState[i] = HIGH;
  }
}

// Returns button state only if it has changed since the last check, otherwise returns 0. Also updates the last state and time.
bool getButtonStateIfChanged(int buttonPin, unsigned long &lastTimeButtonStateChanged, bool &lastButtonState)
{
  if (millis() - lastTimeButtonStateChanged >= DEBOUNCE_MS)
  {
    bool buttonState = !digitalRead(buttonPin);
    if (buttonState != lastButtonState)
    {
      lastTimeButtonStateChanged = millis();
      lastButtonState = buttonState;
      return buttonState;
    }
  }
  return false; // No change!
}

// Simply update the button state and its vars without returning anything (used for braille pattern buttons to track their state in real-time)
void updateButtonState(int buttonPin, unsigned long &lastTimeButtonStateChanged, bool &lastButtonState)
{
  bool reading = !digitalRead(buttonPin); // true when pressed

  if (reading != lastButtonState)
  {
    if (millis() - lastTimeButtonStateChanged >= DEBOUNCE_MS)
    {
      lastButtonState = reading;
      lastTimeButtonStateChanged = millis();
    }
  }
}

char brailleToChar(int pattern, BrailleMode mode)
{
  char ch = '?';

  // Letter mappings
  switch (pattern)
  {
  case 0b100000:
    ch = 'A';
    break;
  case 0b101000:
    ch = 'B';
    break;
  case 0b110000:
    ch = 'C';
    break;
  case 0b110100:
    ch = 'D';
    break;
  case 0b100100:
    ch = 'E';
    break;
  case 0b111000:
    ch = 'F';
    break;
  case 0b111100:
    ch = 'G';
    break;
  case 0b101100:
    ch = 'H';
    break;
  case 0b011000:
    ch = 'I';
    break;
  case 0b011100:
    ch = 'J';
    break;
  case 0b100010:
    ch = 'K';
    break;
  case 0b101010:
    ch = 'L';
    break;
  case 0b110010:
    ch = 'M';
    break;
  case 0b110110:
    ch = 'N';
    break;
  case 0b100110:
    ch = 'O';
    break;
  case 0b111010:
    ch = 'P';
    break;
  case 0b111110:
    ch = 'Q';
    break;
  case 0b101110:
    ch = 'R';
    break;
  case 0b011010:
    ch = 'S';
    break;
  case 0b011110:
    ch = 'T';
    break;
  case 0b100011:
    ch = 'U';
    break;
  case 0b101011:
    ch = 'V';
    break;
  case 0b011101:
    ch = 'W';
    break;
  case 0b110011:
    ch = 'X';
    break;
  case 0b110111:
    ch = 'Y';
    break;
  case 0b100111:
    ch = 'Z';
    break;

  // Punctuation
  case 0b000010:
    ch = ',';
    break;
  case 0b000110:
    ch = ';';
    break;
  case 0b001010:
    ch = ':';
    break;
  case 0b001110:
    ch = '.';
    break;
  case 0b001011:
    ch = '!';
    break;
  case 0b001001:
    ch = '?';
    break;
  case 0b000100:
    ch = '\'';
    break;
  case 0b001100:
    ch = '-';
    break;
  case 0b000101:
    ch = '"';
    break;
  case 0b000011:
    ch = '(';
    break;
  case 0b001111:
    ch = ')';
    break;
  case 0b000000:
    ch = ' ';
    break;

  default:
    ch = '\0';
    break;
  }

  // Mode-based transformations
  if (ch >= 'A' && ch <= 'Z')
  {
    if (mode == LOWERCASE)
    {
      return ch + 32; // Convert to lowercase
    }
    else if (mode == NUMERIC && ch <= 'J')
    {
      return (ch == 'J') ? '0' : ('1' + (ch - 'A')); // A-J → 1-0
    }
    // If UPPERCASE, just return ch
  }

  return ch;
}

void checkDebugCommands()
{
  if (Serial.available() > 0)
  {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "debug")
    {
      debugButtons = !debugButtons;
      if (debugButtons)
      {
        Serial.println("Debug Mode Toggled ON!");
      }
      else
      {
        Serial.println("Debug Mode Toggled OFF!");
      }
    }
    else if (command == "battery")
    {
      debugBattery = !debugBattery;
      if (debugBattery)
      {
        Serial.println("Battery Details Toggled ON!");
      }
      else
      {
        Serial.println("Battery Details Toggled OFF!");
      }
    }
  }
}

void loop()
{
  checkDebugCommands();
  debugFuelGauge();
  debugButtonPins();

  static bool lastBackspaceState = false;
  static bool lastClearAllState = false;
  static bool lastToggleState = false;
  static bool lastOKState = false;
  static bool lastOriginalSentState = false;
  static bool lastCorrectedSentState = false;

  static bool brailleButtonsPressedLast = false; // Whether any braille button was pressed
  static bool brailleCharacterSent = false;      // Prevent duplicate sends

  static int lastPattern = 0;

  static unsigned long lastTimeBackspaceStateChanged = 0;
  static unsigned long lastTimeClearAllStateChanged = 0;
  static unsigned long lastTimeToggleStateChanged = 0;
  static unsigned long lastTimeOKStateChanged = 0;
  static unsigned long lastTimeOriginalSentStateChanged = 0;
  static unsigned long lastTimeCorrectedSentStateChanged = 0;

  unsigned long now = millis();

  // Handle Mode Toggle
  if (getButtonStateIfChanged(buttonPinToggle, lastTimeToggleStateChanged, lastToggleState))
  {
    if (currentMode == LOWERCASE)
    {
      currentMode = UPPERCASE;
    }
    else if (currentMode == UPPERCASE)
    {
      currentMode = NUMERIC;
    }
    else if (currentMode == NUMERIC)
    {
      currentMode = LOWERCASE;
    }
    Serial.print("Mode: ");
    Serial.println(currentMode);
  }

  // Handle Braille Buttons (6 buttons) - with debouncing
  // Read current button state every loop iteration
  int currentReadPattern = 0;
  for (int i = 0; i < 6; i++)
  {
    updateButtonState(buttonPins[i], lastTimeBraillePatternButtonsStateChanged[i], braillePatternStableState[i]);

    if (braillePatternStableState[i]) // If button is currently pressed (stable state)
    {
      currentReadPattern |= (1 << (5 - i)); // MSB is button 1

      if (!lastBraillePatternButtonsState[i]) // If this is the first time we see this button pressed in the current pattern
      {
        lastPattern |= (1 << (5 - i));
        lastBraillePatternButtonsState[i] = true;
      }
    }
  }

  // Track if buttons are physically pressed right now
  bool anyBrailleBeingPressed = (currentReadPattern != 0);

  // Detect when buttons are first pressed -> Start tracking pattern
  if (anyBrailleBeingPressed && !brailleButtonsPressedLast)
  {
    brailleButtonsPressedLast = true;
    brailleCharacterSent = false; // Reset for next character
  }

  // Detect when all buttons are released
  if (!anyBrailleBeingPressed && brailleButtonsPressedLast && !brailleCharacterSent)
  {
    // Process the character
    char c = brailleToChar(lastPattern, currentMode);
    if (c != '\0')
    {
      // Debug: print the pattern
      Serial.print("Pattern: ");
      Serial.print(lastPattern, BIN);
      Serial.print(" -> ");
      Serial.println(c); // Send character immediately to host
    }

    // Reset state for next press
    brailleCharacterSent = true;
    brailleButtonsPressedLast = false;
    lastPattern = 0;
    for (int i = 0; i < 6; i++)
    {
      lastBraillePatternButtonsState[i] = false;
    }
  }

  // Handle Backspace
  if (getButtonStateIfChanged(buttonPinBackspace, lastTimeBackspaceStateChanged, lastBackspaceState))
  {
    Serial.println("BS"); // Backspace command
  }

  // Handle Clear All
  if (getButtonStateIfChanged(buttonPinClearAll, lastTimeClearAllStateChanged, lastClearAllState))
  {
    Serial.println("CLEAR"); // Clear all command
  }

  static bool alreadySent = false; // To prevent multiple sends while buttons are held

  updateButtonState(buttonPinOK, lastTimeOKStateChanged, lastOKState);
  updateButtonState(buttonPinOriginalSent, lastTimeOriginalSentStateChanged, lastOriginalSentState);
  updateButtonState(buttonPinCorrectedSent, lastTimeCorrectedSentStateChanged, lastCorrectedSentState);

  // Check if both buttons AND OK are pressed simultaneously
  if (lastOKState && !alreadySent)
  {
    if (lastOriginalSentState)
    {
      Serial.println("OST"); // Original Sentence Transmission command
    }
    else if (lastCorrectedSentState)
    {
      Serial.println("CST"); // Corrected Sentence Transmission command
    }
    else
    {
      // Add space if neither Original nor Corrected buttons are pressed
      Serial.println("SPACE"); // Space command
    }
    alreadySent = true;
  }

  if (!lastOKState)
  {
    alreadySent = false; // Reset when OK button is released
  }
}

void debugButtonPins()
{
  if (!debugButtons)
    return;

  unsigned long now = millis();

  if (now - debugTimer >= 100)
  {
    debugTimer = now;
  }
  else
  {
    return;
  }

  String pressedPins = "BUTTON ";
  boolean anyPressed = false;

  for (int i = 0; i < NUM_DEBUG_PINS; i++)
  {
    int currentState = !digitalRead(DEBUG_PINS[i]);

    if (currentState == HIGH)
    {
      pressedPins += String(DEBUG_PINS[i]) + " ";
      anyPressed = true;
    }

    lastDebugState[i] = currentState;
  }

  if (anyPressed)
  {
    pressedPins += "PRESSED";
    Serial.println(pressedPins);
  }
}

void debugFuelGauge()
{
  if (!debugBattery)
    return;
  unsigned long now = millis();

  if (now - batteryTimer >= 1000)
  {
    batteryTimer = now;
  }
  else
  {
    return;
  }

  float voltage = battery.cellVoltage();
  float soc = battery.cellPercent();
  float rate = battery.chargeRate();
  bool lowV = battery.alertLowV();
  bool highV = battery.alertHighV();

  Serial.print("Voltage: ");
  Serial.print(voltage, 3);
  Serial.print(" V | SoC: ");
  Serial.print(soc, 1);
  Serial.print(" % | Rate: ");
  Serial.print(rate, 2);
  Serial.println(" %/hr");

  if (lowV)
  {
    Serial.println("Low Voltage Alert!");
  }

  if (highV)
  {
    Serial.println("High Voltage Alert!");
  }
}
