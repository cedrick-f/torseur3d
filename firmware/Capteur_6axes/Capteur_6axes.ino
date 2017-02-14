#include "HX711.h"

// Pins to the load cell amp
#define CLK A0      // clock pin to the load cell amp
#define DOUT1 A1    // data pin to C1
#define DOUT2 A2    // data pin to C2
#define DOUT3 A3    // data pin to C3
#define DOUT4 A4    // data pin to C4
#define DOUT5 5     // data pin to C5
#define DOUT6 6     // data pin to C6

#define CHANNEL_COUNT 6

long int results[CHANNEL_COUNT];

HX711 scales[CHANNEL_COUNT] = {HX711(DOUT1, CLK),
                               HX711(DOUT2, CLK),
                               HX711(DOUT3, CLK),
                               HX711(DOUT4, CLK),
                               HX711(DOUT5, CLK),
                               HX711(DOUT6, CLK)
                             };

byte requete = 0;

void setup() {
  Serial.begin(9600);
  //Serial.print("3 capteurs");
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
  //printRawData();
  while (!Serial.available()) {} // wait for data to arrive
  
  if (Serial.available() > 0) {
    requete = Serial.read();
    delay(10);
    
    //power_up();   // Allumage
    
    if (requete == 'M') {        // Envoi de données
      sendRawData(); //this is for sending raw data, for where everything else is done in processing
      }
    else if (requete == 'T') {   // Tarage
      tare();
      }
    else {
    //else if (requete == 0x11) {      // Test d'identification
      Serial.write(requete);           // Lettre 'A'
      //Serial.println();
      }
    
    //power_down(); // Extinction
    
    
    Serial.flush();
    //while (Serial.available()) {
    //  Serial.read();
    //  }
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
  byte b[4];
  for (int i=0; i<CHANNEL_COUNT; ++i) {
    results[i] = scales[i].read();
    //Serial.print(results[i]);
  }
  byte *buf;
  buf = (byte *) results;
  Serial.write(buf, 4*CHANNEL_COUNT); 
  //Serial.println();
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
