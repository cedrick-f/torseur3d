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
long int tares[CHANNEL_COUNT];

HX711 scales[CHANNEL_COUNT] = {HX711(DOUT1, CLK),
                               HX711(DOUT2, CLK),
                               HX711(DOUT3, CLK),
                               HX711(DOUT4, CLK),
                               HX711(DOUT5, CLK),
                               HX711(DOUT6, CLK)
                             };

byte requete = 0;

void setup() {
  Serial.begin(115200);
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
  printRawData();
  //while (!Serial.available()) {} // wait for data to arrive
  
  if (Serial.available() > 0) {
    requete = Serial.read();
    delay(10);
    
    //power_up();   // Allumage
    
    if (requete == 'T') {   // Tarage
      tare();
      }
      
    Serial.flush();
    //while (Serial.available()) {
    //  Serial.read();
    //  }
    }
}

void printRawData() {
  int N = 2;
  long int V = 0;
  for (int i=0; i<CHANNEL_COUNT; ++i) {
    for (int j=0; j<N; ++j) {
      V += scales[i].read() - tares[i];
    }
    results[i] = V/N;
    V = 0;
    Serial.print( -results[i]);  
    Serial.print( (i!=CHANNEL_COUNT-1)?"\t":"\n");
  }  
  
}


void tare() {
  Serial.println("Tarage...");
  int N = 20;
  long int V = 0;
  for (int i=0; i<CHANNEL_COUNT; ++i) {
    for (int j=0; j<N; ++j) {
      V += scales[i].read();
      //delay(1);
    }
    tares[i] = V/N;
    V = 0;
  }
}

