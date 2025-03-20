 #ifndef OSC_HANDLERS_H
 #define OSC_HANDLERS_H
 
 #include <ArduinoOSC.h>
 #include "led_helpers.h"
 

 void setupOscHandlers(OscWiFi &osc, LightEffect &effect) {

   osc.subscribe("/effect/*/segment/*/color",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/color", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL && msg.size() >= 4) {
             for (int c = 0; c < 4; c++) {
               int colorValue = msg.arg<int>(c);

               segment->color[c] = constrain(colorValue, 0, 10);
             }
             Serial.printf("Updated segment %d colors\n", segmentID);
           }
         }
       }
     });
   
   osc.subscribe("/effect/*/segment/*/transparency",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/transparency", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL && msg.size() >= 4) {
             for (int c = 0; c < 4; c++) {
               float transValue = msg.arg<float>(c);
               segment->transparency[c] = constrain(transValue, 0.0, 1.0);
             }
             Serial.printf("Updated segment %d transparency\n", segmentID);
           }
         }
       }
     });
   
   osc.subscribe("/effect/*/segment/*/length",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/length", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL && msg.size() >= 3) {
             for (int c = 0; c < 3; c++) {
               int lengthValue = msg.arg<int>(c);
               segment->length[c] = max(1, lengthValue); 
             }
             Serial.printf("Updated segment %d lengths\n", segmentID);
           }
         }
       }
     });
   
   osc.subscribe("/effect/*/segment/*/move_speed",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/move_speed", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL && msg.size() >= 1) {
             float speedValue = msg.arg<float>(0);

             if ((speedValue > 0 && segment->moveSpeed < 0) ||
                 (speedValue < 0 && segment->moveSpeed > 0)) {
               segment->direction *= -1;
             }
             segment->moveSpeed = speedValue;
             Serial.printf("Updated segment %d speed to %.2f\n", segmentID, segment->moveSpeed);
           }
         }
       }
     });
   
   osc.subscribe("/effect/*/segment/*/move_range",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/move_range", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL && msg.size() >= 2) {
             int minRange = msg.arg<int>(0);
             int maxRange = msg.arg<int>(1);
             

             minRange = constrain(minRange, 0, effect.ledCount - 1);
             maxRange = constrain(maxRange, 0, effect.ledCount - 1);
             
             if (minRange > maxRange) {

               int temp = minRange;
               minRange = maxRange;
               maxRange = temp;
             }
             
             segment->moveRange[0] = minRange;
             segment->moveRange[1] = maxRange;
             Serial.printf("Updated segment %d range to [%d, %d]\n", 
                         segmentID, segment->moveRange[0], segment->moveRange[1]);
           }
         }
       }
     });
   
   osc.subscribe("/effect/*/segment/*/initial_position",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/initial_position", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL && msg.size() >= 1) {
             int posValue = msg.arg<int>(0);
             segment->initialPosition = posValue;
             segment->currentPosition = float(posValue);
             Serial.printf("Updated segment %d position to %d\n", segmentID, segment->initialPosition);
           }
         }
       }
     });
   
   osc.subscribe("/effect/*/segment/*/is_edge_reflect",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/is_edge_reflect", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL && msg.size() >= 1) {
             bool reflectValue = msg.arg<int>(0) != 0;
             segment->isEdgeReflect = reflectValue;
             Serial.printf("Updated segment %d reflection to %d\n", segmentID, segment->isEdgeReflect);
           }
         }
       }
     });
   
   osc.subscribe("/effect/*/segment/*/dimmer_time",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/dimmer_time", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL && msg.size() >= 5) {
             for (int t = 0; t < 5; t++) {
               int timeValue = msg.arg<int>(t);
               segment->dimmerTime[t] = max(0, timeValue);
             }
             

             if (segment->dimmerTime[0] >= segment->dimmerTime[1]) {
               segment->dimmerTime[1] = segment->dimmerTime[0] + 1;
             }
             if (segment->dimmerTime[2] >= segment->dimmerTime[3]) {
               segment->dimmerTime[3] = segment->dimmerTime[2] + 1;
             }
             if (segment->dimmerTime[4] <= 0) {
               segment->dimmerTime[4] = 1000; // Default cycle time
             }
             Serial.printf("Updated segment %d dimmer times\n", segmentID);
           }
         }
       }
     });
   

   osc.subscribe("/effect/*/segment/create",
     [&effect](const OscMessage& msg) {
       int effectID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/create", &effectID) == 1) {
         if (effectID == effect.effectID && effect.segmentCount < MAX_SEGMENTS) {
           int segmentID = msg.arg<int>(0);
           int initialPosition = msg.size() >= 2 ? msg.arg<int>(1) : 0;
           int minRange = msg.size() >= 3 ? msg.arg<int>(2) : 0;
           int maxRange = msg.size() >= 4 ? msg.arg<int>(3) : effect.ledCount - 1;
           

           if (findSegmentById(effect, segmentID) != NULL) {
             Serial.printf("Segment ID %d already exists\n", segmentID);
             return;
           }
           

           LightSegment newSegment;
           initializeSegment(newSegment, segmentID, initialPosition, minRange, maxRange);
           

           if (addSegmentToEffect(effect, newSegment)) {
             Serial.printf("Created new segment with ID %d\n", segmentID);
           } else {
             Serial.println("Failed to add segment (max reached)");
           }
         }
       }
     });
   

   osc.subscribe("/effect/*/segment/delete",
     [&effect](const OscMessage& msg) {
       int effectID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/delete", &effectID) == 1) {
         if (effectID == effect.effectID && msg.size() >= 1) {
           int segmentID = msg.arg<int>(0);
           

           if (removeSegmentFromEffect(effect, segmentID)) {
             Serial.printf("Deleted segment with ID %d\n", segmentID);
           } else {
             Serial.printf("Segment ID %d not found\n", segmentID);
           }
         }
       }
     });
   

   osc.subscribe("/effect/*/segment/*/preset",
     [&effect](const OscMessage& msg) {
       int effectID, segmentID;
       if (sscanf(msg.address().c_str(), "/effect/%d/segment/%d/preset", &effectID, &segmentID) == 2) {
         if (effectID == effect.effectID && msg.size() >= 1) {
           LightSegment* segment = findSegmentById(effect, segmentID);
           if (segment != NULL) {
             int presetID = msg.arg<int>(0);
             

             switch (presetID) {
               case 1: // Rainbow Flow
                 segment->color[0] = 1;  // Red
                 segment->color[1] = 3;  // Blue
                 segment->color[2] = 4;  // Yellow
                 segment->color[3] = 2;  // Green
                 segment->moveSpeed = 20.0;
                 segment->isEdgeReflect = false;
                 segment->dimmerTime[0] = 0;
                 segment->dimmerTime[1] = 500;
                 segment->dimmerTime[2] = 4500;
                 segment->dimmerTime[3] = 5000;
                 segment->dimmerTime[4] = 5000;
                 break;
                 
               case 2: // Breathing
                 segment->color[0] = 7;  // White
                 segment->color[1] = 7;  // White
                 segment->color[2] = 7;  // White
                 segment->color[3] = 7;  // White
                 segment->moveSpeed = 0;
                 segment->length[0] = 1;
                 segment->length[1] = 1;
                 segment->length[2] = 1;
                 segment->dimmerTime[0] = 0;
                 segment->dimmerTime[1] = 2000;
                 segment->dimmerTime[2] = 2000;
                 segment->dimmerTime[3] = 4000;
                 segment->dimmerTime[4] = 4000;
                 break;
                 
               case 3: // Police Lights
                 segment->color[0] = 1;  // Red
                 segment->color[1] = 3;  // Blue
                 segment->color[2] = 1;  // Red
                 segment->color[3] = 3;  // Blue
                 segment->moveSpeed = 100;
                 segment->length[0] = 20;
                 segment->length[1] = 20;
                 segment->length[2] = 20;
                 segment->dimmerTime[0] = 0;
                 segment->dimmerTime[1] = 100;
                 segment->dimmerTime[2] = 100;
                 segment->dimmerTime[3] = 200;
                 segment->dimmerTime[4] = 200;
                 break;
                 
               case 4: // Color Wipe
                 segment->color[0] = 0;  // Black
                 segment->color[1] = 5;  // Magenta
                 segment->color[2] = 0;  // Black
                 segment->color[3] = 5;  // Magenta
                 segment->moveSpeed = 50;
                 segment->length[0] = 50;
                 segment->length[1] = 50;
                 segment->length[2] = 50;
                 segment->dimmerTime[0] = 0;
                 segment->dimmerTime[1] = 0;
                 segment->dimmerTime[2] = 0;
                 segment->dimmerTime[3] = 0;
                 segment->dimmerTime[4] = 1000;
                 break;
                 
               case 5: // Pulse
                 segment->color[0] = 8;  // Orange
                 segment->color[1] = 8;  // Orange
                 segment->color[2] = 8;  // Orange
                 segment->color[3] = 8;  // Orange
                 segment->moveSpeed = 0;
                 segment->length[0] = 10;
                 segment->length[1] = 10;
                 segment->length[2] = 10;
                 segment->dimmerTime[0] = 0;
                 segment->dimmerTime[1] = 500;
                 segment->dimmerTime[2] = 500;
                 segment->dimmerTime[3] = 1000;
                 segment->dimmerTime[4] = 1000;
                 break;
                 
               default:
                 Serial.printf("Unknown preset ID: %d\n", presetID);
                 return;
             }
             
             Serial.printf("Applied preset %d to segment %d\n", presetID, segmentID);
           }
         }
       }
     });
   

   osc.subscribe("/effect/*/settings",
     [&effect](const OscMessage& msg) {
       int effectID;
       if (sscanf(msg.address().c_str(), "/effect/%d/settings", &effectID) == 1) {
         if (effectID == effect.effectID && msg.size() >= 2) {
           int ledCount = msg.arg<int>(0);
           int fps = msg.arg<int>(1);
           

           effect.ledCount = constrain(ledCount, 1, NUM_LEDS);
           effect.fps = constrain(fps, 1, 120);
           
           Serial.printf("Updated effect settings: LEDs=%d, FPS=%d\n", 
                       effect.ledCount, effect.fps);
         }
       }
     });
 }
 
 #endif