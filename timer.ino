/* interrupts - https://gist.github.com/nonsintetic/ad13e70f164801325f5f552f84306d6f */

// the radiohead library uses TC3 for reading from the radios
// we use TC5 to read from GPS

void TC5_Handler(void) {
  // YOUR CODE HERE; keep this fast

  // check GPS for data. do this here so that a slow framerate doesn't slow reading from GPS
  GPS.read();

  // END OF YOUR CODE

  TC5->COUNT16.INTFLAG.bit.MC0 = 1;
}

/*
 *  TIMER SPECIFIC FUNCTIONS FOLLOW
 *  you shouldn't change these unless you know what you're doing
 */

// Configures the TC to generate output events at the sample frequency.
// Configures the TC in Frequency Generation mode, with an event output once
// each time the audio sample frequency period expires.
void tcConfigure(int sampleRate) {
  // Enable GCLK for TCC2 and TC5 (timer counter input clock)
  GCLK->CLKCTRL.reg = (uint16_t)(GCLK_CLKCTRL_CLKEN | GCLK_CLKCTRL_GEN_GCLK0 | GCLK_CLKCTRL_ID(GCM_TC4_TC5));
  while (GCLK->STATUS.bit.SYNCBUSY)
    ;

  tcReset(); // reset TC5

  // Set Timer counter Mode to 16 bits
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_MODE_COUNT16;
  // Set TC5 mode as match frequency
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_WAVEGEN_MFRQ;
  // set prescaler and enable TC5
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV1 | TC_CTRLA_ENABLE;
  // set TC5 timer counter based off of the system clock and the user defined
  // sample rate or waveform
  TC5->COUNT16.CC[0].reg = (uint16_t)(SystemCoreClock / sampleRate - 1);
  while (tcIsSyncing())
    ;

  // Configure interrupt request
  NVIC_DisableIRQ(TC5_IRQn);
  NVIC_ClearPendingIRQ(TC5_IRQn);
  NVIC_SetPriority(TC5_IRQn, 0);
  NVIC_EnableIRQ(TC5_IRQn);

  // Enable the TC5 interrupt request
  TC5->COUNT16.INTENSET.bit.MC0 = 1;
  while (tcIsSyncing())
    ; // wait until TC5 is done syncing
}

// Function that is used to check if TC5 is done syncing
// returns true when it is done syncing
bool tcIsSyncing() { return TC5->COUNT16.STATUS.reg & TC_STATUS_SYNCBUSY; }

// This function enables TC5 and waits for it to be ready
void tcStartCounter() {
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_ENABLE; // set the CTRLA register
  while (tcIsSyncing())
    ; // wait until snyc'd
}

// Reset TC5
void tcReset() {
  TC5->COUNT16.CTRLA.reg = TC_CTRLA_SWRST;
  while (tcIsSyncing())
    ;
  while (TC5->COUNT16.CTRLA.bit.SWRST)
    ;
}

// disable TC5
void tcDisable() {
  TC5->COUNT16.CTRLA.reg &= ~TC_CTRLA_ENABLE;
  while (tcIsSyncing())
    ;
}
