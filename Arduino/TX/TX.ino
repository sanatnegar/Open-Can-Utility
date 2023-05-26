#include <SPI.h>
#include <mcp2515.h>

int post_transmit_delay = 1;
struct can_frame canMsg[20];
MCP2515 mcp2515(10);
uint32_t offsetTime[20];
uint32_t timeNow;
uint32_t timeDelay[20];
uint32_t timeMsg[20];
bool bFirst[20];
String strMyData[8];
byte bMyData[8];

String strSlot, strCanId, strDlc, strPeriod;
byte slot, dlc;
int canId;
uint32_t period;
String strD0, strD1, strD2, strD3, strD4, strD5, strD6, strD7;
byte d0, d1, d2, d3, d4, d5, d6, d7;
String inputString = "";         // a String to hold incoming data
bool stringComplete = false;  // whether the string is complete
int index1, index2, index3, index4, index5, index6, index7, index8, index9, index10, index11, index12;



void setup()
{
  // 50 mS Message
  canMsg[0].can_id  = 0x01;
  canMsg[0].can_dlc = 8;
  canMsg[0].data[0] = 0x01;
  canMsg[0].data[1] = 0x01;
  canMsg[0].data[2] = 0x01;
  canMsg[0].data[3] = 0x01;
  canMsg[0].data[4] = 0x01;
  canMsg[0].data[5] = 0x01;
  canMsg[0].data[6] = 0x01;
  canMsg[0].data[7] = 0x01;

  // 100 mS Messages
  canMsg[1].can_id  = 0x20F;
  canMsg[1].can_dlc = 8;
  canMsg[1].data[0] = 0x02;
  canMsg[1].data[1] = 0x02;
  canMsg[1].data[2] = 0x02;
  canMsg[1].data[3] = 0x02;
  canMsg[1].data[4] = 0x02;
  canMsg[1].data[5] = 0x02;
  canMsg[1].data[6] = 0x02;
  canMsg[1].data[7] = 0x02;

  canMsg[2].can_id  = 0x308;
  canMsg[2].can_dlc = 8;
  canMsg[2].data[0] = 0x03;
  canMsg[2].data[1] = 0x03;
  canMsg[2].data[2] = 0x03;
  canMsg[2].data[3] = 0x03;
  canMsg[2].data[4] = 0x03;
  canMsg[2].data[5] = 0x03;
  canMsg[2].data[6] = 0x03;
  canMsg[2].data[7] = 0x03;

  canMsg[3].can_id  = 0x139;
  canMsg[3].can_dlc = 8;
  canMsg[3].data[0] = 0x04;
  canMsg[3].data[1] = 0x04;
  canMsg[3].data[2] = 0x04;
  canMsg[3].data[3] = 0x04;
  canMsg[3].data[4] = 0x04;
  canMsg[3].data[5] = 0x04;
  canMsg[3].data[6] = 0x04;
  canMsg[3].data[7] = 0x04;

  // 200 mS Messages
  canMsg[4].can_id  = 0x08F;
  canMsg[4].can_dlc = 8;
  canMsg[4].data[0] = 0x05;
  canMsg[4].data[1] = 0x05;
  canMsg[4].data[2] = 0x05;
  canMsg[4].data[3] = 0x05;
  canMsg[4].data[4] = 0x05;
  canMsg[4].data[5] = 0x05;
  canMsg[4].data[6] = 0x05;
  canMsg[4].data[7] = 0x05;

  canMsg[5].can_id  = 0x10F;
  canMsg[5].can_dlc = 8;
  canMsg[5].data[0] = 0x06;
  canMsg[5].data[1] = 0x06;
  canMsg[5].data[2] = 0x06;
  canMsg[5].data[3] = 0x06;
  canMsg[5].data[4] = 0x06;
  canMsg[5].data[5] = 0x06;
  canMsg[5].data[6] = 0x06;
  canMsg[5].data[7] = 0x06;

  canMsg[6].can_id  = 0x11B;
  canMsg[6].can_dlc = 8;
  canMsg[6].data[0] = 0x07;
  canMsg[6].data[1] = 0x07;
  canMsg[6].data[2] = 0x07;
  canMsg[6].data[3] = 0x07;
  canMsg[6].data[4] = 0x07;
  canMsg[6].data[5] = 0x07;
  canMsg[6].data[6] = 0x07;
  canMsg[6].data[7] = 0x07;

  canMsg[7].can_id  = 0x18F;
  canMsg[7].can_dlc = 8;
  canMsg[7].data[0] = 0x08;
  canMsg[7].data[1] = 0x08;
  canMsg[7].data[2] = 0x08;
  canMsg[7].data[3] = 0x08;
  canMsg[7].data[4] = 0x08;
  canMsg[7].data[5] = 0x08;
  canMsg[7].data[6] = 0x08;
  canMsg[7].data[7] = 0x08;

  canMsg[8].can_id  = 0x280;
  canMsg[8].can_dlc = 8;
  canMsg[8].data[0] = 0x09;
  canMsg[8].data[1] = 0x09;
  canMsg[8].data[2] = 0x09;
  canMsg[8].data[3] = 0x09;
  canMsg[8].data[4] = 0x09;
  canMsg[8].data[5] = 0x09;
  canMsg[8].data[6] = 0x09;
  canMsg[8].data[7] = 0x09;

  canMsg[9].can_id  = 0x31A;
  canMsg[9].can_dlc = 8;
  canMsg[9].data[0] = 0x10;
  canMsg[9].data[1] = 0x10;
  canMsg[9].data[2] = 0x10;
  canMsg[9].data[3] = 0x10;
  canMsg[9].data[4] = 0x10;
  canMsg[9].data[5] = 0x10;
  canMsg[9].data[6] = 0x10;
  canMsg[9].data[7] = 0x10;

  // 1000 mS Message
  canMsg[10].can_id  = 0x28F;
  canMsg[10].can_dlc = 8;
  canMsg[10].data[0] = 0x11;
  canMsg[10].data[1] = 0x11;
  canMsg[10].data[2] = 0x11;
  canMsg[10].data[3] = 0x11;
  canMsg[10].data[4] = 0x11;
  canMsg[10].data[5] = 0x11;
  canMsg[10].data[6] = 0x11;
  canMsg[10].data[7] = 0x11;

  // 2000 mS Messages
  canMsg[11].can_id  = 0x108;
  canMsg[11].can_dlc = 8;
  canMsg[11].data[0] = 0x12;
  canMsg[11].data[1] = 0x12;
  canMsg[11].data[2] = 0x12;
  canMsg[11].data[3] = 0x12;
  canMsg[11].data[4] = 0x12;
  canMsg[11].data[5] = 0x12;
  canMsg[11].data[6] = 0x12;
  canMsg[11].data[7] = 0x12;

  canMsg[12].can_id  = 0x198;
  canMsg[12].can_dlc = 8;
  canMsg[12].data[0] = 0x13;
  canMsg[12].data[1] = 0x13;
  canMsg[12].data[2] = 0x13;
  canMsg[12].data[3] = 0x13;
  canMsg[12].data[4] = 0x13;
  canMsg[12].data[5] = 0x13;
  canMsg[12].data[6] = 0x13;
  canMsg[12].data[7] = 0x13;

  // 5000 mS Messages
  canMsg[13].can_id  = 0x218;
  canMsg[13].can_dlc = 8;
  canMsg[13].data[0] = 0x14;
  canMsg[13].data[1] = 0x14;
  canMsg[13].data[2] = 0x14;
  canMsg[13].data[3] = 0x14;
  canMsg[13].data[4] = 0x14;
  canMsg[13].data[5] = 0x14;
  canMsg[13].data[6] = 0x14;
  canMsg[13].data[7] = 0x14;

  canMsg[14].can_id  = 0x384;
  canMsg[14].can_dlc = 8;
  canMsg[14].data[0] = 0x15;
  canMsg[14].data[1] = 0x15;
  canMsg[14].data[2] = 0x15;
  canMsg[14].data[3] = 0x15;
  canMsg[14].data[4] = 0x15;
  canMsg[14].data[5] = 0x15;
  canMsg[14].data[6] = 0x15;
  canMsg[14].data[7] = 0x15;

  canMsg[15].can_id  = 0x388;
  canMsg[15].can_dlc = 8;
  canMsg[15].data[0] = 0x16;
  canMsg[15].data[1] = 0x16;
  canMsg[15].data[2] = 0x16;
  canMsg[15].data[3] = 0x16;
  canMsg[15].data[4] = 0x16;
  canMsg[15].data[5] = 0x16;
  canMsg[15].data[6] = 0x16;
  canMsg[15].data[7] = 0x16;

  // Event Baes Messages (10000 mS)
  canMsg[16].can_id  = 0x748;
  canMsg[16].can_dlc = 8;
  canMsg[16].data[0] = 0x17;
  canMsg[16].data[1] = 0x17;
  canMsg[16].data[2] = 0x17;
  canMsg[16].data[3] = 0x17;
  canMsg[16].data[4] = 0x17;
  canMsg[16].data[5] = 0x17;
  canMsg[16].data[6] = 0x17;
  canMsg[16].data[7] = 0x17;

  canMsg[17].can_id  = 0x62C;
  canMsg[17].can_dlc = 8;
  canMsg[17].data[0] = 0x18;
  canMsg[17].data[1] = 0x18;
  canMsg[17].data[2] = 0x18;
  canMsg[17].data[3] = 0x18;
  canMsg[17].data[4] = 0x18;
  canMsg[17].data[5] = 0x18;
  canMsg[17].data[6] = 0x18;
  canMsg[17].data[7] = 0x18;

  canMsg[18].can_id  = 0x0AA;
  canMsg[18].can_dlc = 8;
  canMsg[18].data[0] = 0x19;
  canMsg[18].data[1] = 0x19;
  canMsg[18].data[2] = 0x19;
  canMsg[18].data[3] = 0x19;
  canMsg[18].data[4] = 0x19;
  canMsg[18].data[5] = 0x19;
  canMsg[18].data[6] = 0x19;
  canMsg[18].data[7] = 0x19;

  canMsg[19].can_id  = 0x0BB;
  canMsg[19].can_dlc = 8;
  canMsg[19].data[0] = 0x20;
  canMsg[19].data[1] = 0x20;
  canMsg[19].data[2] = 0x20;
  canMsg[19].data[3] = 0x20;
  canMsg[19].data[4] = 0x20;
  canMsg[19].data[5] = 0x20;
  canMsg[19].data[6] = 0x20;
  canMsg[19].data[7] = 0x20;


  while (!Serial);
  Serial.begin(115200);

  mcp2515.reset();
  mcp2515.setBitrate(CAN_125KBPS, MCP_8MHZ);
  mcp2515.setNormalMode();

  Serial.println("Example: Write to CAN");

  timeNow = micros();

  for (int i = 0; i <= 19; i++)
  {
    timeMsg[i] = timeNow;
  }


  timeDelay[0] = 100000ul;
  timeDelay[1] = 0ul;
  timeDelay[2] = 0ul;
  timeDelay[3] = 0ul;
  timeDelay[4] = 0ul;
  timeDelay[5] = 0ul;
  timeDelay[6] = 0ul;
  timeDelay[7] = 0ul;
  timeDelay[8] = 0ul;
  timeDelay[9] = 0ul;
  timeDelay[10] = 0ul;
  timeDelay[11] = 0ul;
  timeDelay[12] = 0ul;
  timeDelay[13] = 0ul;
  timeDelay[14] = 0ul;
  timeDelay[15] = 0ul;
  timeDelay[16] = 0ul;
  timeDelay[17] = 0ul;
  timeDelay[18] = 0ul;
  timeDelay[19] = 0ul;


  offsetTime[0] = 1000ul;
  for (int i = 1; i <= 19; i++)
  {
    offsetTime[i] = offsetTime[i - 1] + 5000ul;
  }

  for (int i = 0; i <= 19; i++)
  {
    bFirst[i] = false;
  }

}

void loop()
{
  if (stringComplete) {

    index1 = inputString.indexOf(',');
    index2 = inputString.indexOf(',', index1 + 1);
    index3 = inputString.indexOf(',', index2 + 1);
    index4 = inputString.indexOf(',', index3 + 1);
    index5 = inputString.indexOf(',', index4 + 1);
    index6 = inputString.indexOf(',', index5 + 1);
    index7 = inputString.indexOf(',', index6 + 1);
    index8 = inputString.indexOf(',', index7 + 1);
    index9 = inputString.indexOf(',', index8 + 1);
    index10 = inputString.indexOf(',', index9 + 1);
    index11 = inputString.indexOf(',', index10 + 1);




    strSlot = inputString.substring(0, index1);
    strCanId = inputString.substring(index1 + 1, index2);
    strDlc = inputString.substring(index2 + 1, index3);
    //    strD0 = inputString.substring(index3 + 1, index4);
    //    strD1 = inputString.substring(index4 + 1, index5);
    //    strD2 = inputString.substring(index5 + 1, index6);
    //    strD3 = inputString.substring(index6 + 1, index7);
    //    strD4 = inputString.substring(index7 + 1, index8);
    //    strD5 = inputString.substring(index8 + 1, index9);
    //    strD6 = inputString.substring(index9 + 1, index10);
    //    strD7 = inputString.substring(index10 + 1, index11);

    strMyData[0] = inputString.substring(index3 + 1, index4);
    strMyData[1] = inputString.substring(index4 + 1, index5);
    strMyData[2] = inputString.substring(index5 + 1, index6);
    strMyData[3] = inputString.substring(index6 + 1, index7);
    strMyData[4] = inputString.substring(index7 + 1, index8);
    strMyData[5] = inputString.substring(index8 + 1, index9);
    strMyData[6] = inputString.substring(index9 + 1, index10);
    strMyData[7] = inputString.substring(index10 + 1, index11);

    strPeriod = inputString.substring(index11 + 1);

    inputString = "";
    stringComplete = false;

    //    Serial.print(strSlot);
    //    Serial.print("-");
    //    Serial.print(strCanId);
    //    Serial.print("-");
    //    Serial.print(strDlc);
    //    Serial.print("-");
    //    Serial.print(strD0);
    //    Serial.print("-");
    //    Serial.print(strD1);
    //    Serial.print("-");
    //    Serial.print(strD2);
    //    Serial.print("-");
    //    Serial.print(strD3);
    //    Serial.print("-");
    //    Serial.print(strD4);
    //    Serial.print("-");
    //    Serial.print(strD5);
    //    Serial.print("-");
    //    Serial.print(strD6);
    //    Serial.print("-");
    //    Serial.print(strD7);
    //    Serial.print("-");
    //    Serial.println(strPeriod);

    slot = strSlot.toInt();
    canId = strCanId.toInt();
    dlc = strDlc.toInt();
    //    d0 = strD0.toInt();
    //    d1 = strD1.toInt();
    //    d2 = strD2.toInt();
    //    d3 = strD3.toInt();
    //    d4 = strD4.toInt();
    //    d5 = strD5.toInt();
    //    d6 = strD6.toInt();
    //    d7 = strD7.toInt();

    for (int i = 0; i < dlc; i++)
    {
      bMyData[i] = strMyData[i].toInt();
    }





    period = strPeriod.toInt();

    canMsg[slot].can_id  = canId;
    canMsg[slot].can_dlc = dlc;
    //    canMsg[slot].data[0] = d0;
    //    canMsg[slot].data[1] = d1;
    //    canMsg[slot].data[2] = d2;
    //    canMsg[slot].data[3] = d3;
    //    canMsg[slot].data[4] = d4;
    //    canMsg[slot].data[5] = d5;
    //    canMsg[slot].data[6] = d6;
    //    canMsg[slot].data[7] = d7;

    for (int i = 0 ; i < 8; i++)
    {
      canMsg[slot].data[i] = 0x00; 
    }

    for (int i = 0 ; i < dlc; i++)
    {
      canMsg[slot].data[i] = bMyData[i];
    }

    timeDelay[slot] = period * 1000;

    // sending one shot messages
    if (timeDelay[slot] == 0)
    {
      mcp2515.sendMessage(&canMsg[slot]);
    }

    Serial.println("Arrays Statues: ");


    for (int j; j <= 19; j++)
    {
      Serial.print(String(j));
      Serial.print("-");
      Serial.print(String(canMsg[j].can_id, HEX));
      Serial.print("-");
      Serial.print(String(canMsg[j].can_dlc));
      Serial.print("-");
      Serial.print(String(canMsg[j].data[0], HEX));
      Serial.print("-");
      Serial.print(String(canMsg[j].data[1], HEX));
      Serial.print("-");
      Serial.print(String(canMsg[j].data[2], HEX));
      Serial.print("-");
      Serial.print(String(canMsg[j].data[3], HEX));
      Serial.print("-");
      Serial.print(String(canMsg[j].data[4], HEX));
      Serial.print("-");
      Serial.print(String(canMsg[j].data[5], HEX));
      Serial.print("-");
      Serial.print(String(canMsg[j].data[6], HEX));
      Serial.print("-");
      Serial.print(String(canMsg[j].data[7], HEX));
      Serial.print("-");
      Serial.println(String(timeDelay[j]));
    }
  }


  // sending messages
  for (int i = 0; i <= 19; i++)
  {
    timeNow = micros();
    if (!bFirst[i])
    {
      if ( (timeNow - timeMsg[i]) >= offsetTime[i] )
      {
        //send message
        if (timeDelay[i] != 0)
        {
          mcp2515.sendMessage(&canMsg[i]);
          delay(post_transmit_delay);
        }
        //save time for next message timing
        timeMsg[i] = timeNow;
        bFirst[i] = true;
      }//if
    } else
    {
      if ( (timeNow - timeMsg[i]) >= timeDelay[i] )
      {
        //send message
        if (timeDelay[i] != 0)
        {
          mcp2515.sendMessage(&canMsg[i]);
          delay(post_transmit_delay);
        }
        //save time for next message timing
        timeMsg[i] = timeNow;
      }//if
    }
  }
  // =========================================================================================
}//loop

void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}
