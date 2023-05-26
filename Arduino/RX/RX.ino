#include <SPI.h>
#include <mcp2515.h>

MCP2515 mcp2515(49);

struct can_frame canMsg1;
struct can_frame canMsg2;
byte bEmptyData;


void setup() {

  //  canMsg1.can_id  = 0x0AA;
  //  canMsg1.can_dlc = 8;
  //  canMsg1.data[0] = 0x8E;
  //  canMsg1.data[1] = 0x87;
  //  canMsg1.data[2] = 0x32;
  //  canMsg1.data[3] = 0xFA;
  //  canMsg1.data[4] = 0x26;
  //  canMsg1.data[5] = 0x8E;
  //  canMsg1.data[6] = 0xBE;
  //  canMsg1.data[7] = 0x86;
  //
  //  canMsg2.can_id  = 0x0BB;
  //  canMsg2.can_dlc = 8;
  //  canMsg2.data[0] = 0x1E;
  //  canMsg2.data[1] = 0x12;
  //  canMsg2.data[2] = 0x23;
  //  canMsg2.data[3] = 0x34;
  //  canMsg2.data[4] = 0x45;
  //  canMsg2.data[5] = 0x56;
  //  canMsg2.data[6] = 0x78;
  //  canMsg2.data[7] = 0xA0;


  Serial.begin(115200);

  mcp2515.reset();
  mcp2515.setBitrate(CAN_125KBPS, MCP_8MHZ);
  mcp2515.setNormalMode();
}

void loop() {

  if (mcp2515.readMessage(&canMsg1) == MCP2515::ERROR_OK)
  {
    Serial.print("#");
    Serial.print(canMsg1.can_id, HEX); // print ID
    Serial.print(",");
    Serial.print(canMsg1.can_dlc, HEX); // print DLC
    Serial.print(",");

    for (int i = 0; i < canMsg1.can_dlc - 1; i++)  { // print the data
      Serial.print(canMsg1.data[i], HEX);
      Serial.print(",");
    }

    
    Serial.print(canMsg1.data[canMsg1.can_dlc - 1], HEX); // Comma after the last data byte is no longer neeeded
    Serial.print(",");

    bEmptyData = 8 - canMsg1.can_dlc;

    if (bEmptyData > 0)
    {
      for (int i = 0; i < bEmptyData; i++)
      {
        Serial.print("0");
        Serial.print(",");
      }
    }
    
    Serial.print(String(micros()));
    Serial.println("|");

  }

}
