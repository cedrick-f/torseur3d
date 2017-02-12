#include "HX711.h"

// Pins to the load cell amp
#define CLK A0      // clock pin to the load cell amp
#define DOUT1 A1    // data pin to C1
#define DOUT2 A2    // data pin to C2
#define DOUT3 A3    // data pin to C3
#define DOUT4 1     // data pin to C4
#define DOUT5 2     // data pin to C5
#define DOUT6 3     // data pin to C6

#define CHANNEL_COUNT 6

long int results[CHANNEL_COUNT];

HX711 scales[CHANNEL_COUNT] = {HX711(DOUT1, CLK),
                               HX711(DOUT2, CLK),
                               HX711(DOUT3, CLK),
                               HX711(DOUT4, CLK),
                               HX711(DOUT5, CLK),
                               HX711(DOUT6, CLK)};

byte requete = 0;

void setup() {
  Serial.begin(115200);
  
  pinMode(CLK, OUTPUT);
  pinMode(DOUT1, INPUT);
  pinMode(DOUT2, INPUT);
  pinMode(DOUT3, INPUT);
  pinMode(DOUT4, INPUT);
  pinMode(DOUT5, INPUT);
  pinMode(DOUT6, INPUT);

  tare();
}



void loop() {
  if (Serial.available() > 0) {
    requete = Serial.read();
    
    power_up();   // Allumage
    
    if (requete == 0xaa) {        // Envoi de données
      sendRawData(); //this is for sending raw data, for where everything else is done in processing
      }
    else if (requete == 0xbb) {   // Tarage
      tare();
      }
    else if (requete == 0) {   // Test d'identification
      Serial.write(0);
      }
    power_down(); // Extinction
    
    while (Serial.available()) {
      Serial.read();
      }
    }
}



void printRawData() {
  for (int i=0; i<CHANNEL_COUNT; ++i) {
    results[i] = scales[i].read();
    Serial.print( -results[i]);  
    Serial.print( (i!=CHANNEL_COUNT-1)?"\t":"\n");
  }  
  delay(10);
}


void sendRawData() {
  for (int i=0; i<CHANNEL_COUNT; ++i) {
    results[i] = scales[i].read();
    Serial.write(-results[i]);  
  }  
  delay(10);
}


void tare() {
  for (int i=0; i<CHANNEL_COUNT; ++i) {
    scales[i].tare();
  }
}



void power_down() {
  for (int i=0; i<CHANNEL_COUNT; ++i) {
    scales[i].power_down();
  }
}



void power_up() {
  for (int i=0; i<CHANNEL_COUNT; ++i) {
    scales[i].power_up();
  }
}
