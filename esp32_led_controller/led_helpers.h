 #ifndef LED_HELPERS_H
 #define LED_HELPERS_H
 
 #include <FastLED.h>
 #include "config.h"
 

 struct LightSegment {
   int segmentID;
   int color[4];            // 4 color IDs for control points
   float transparency[4];   // Transparency values for each control point (0.0-1.0)
   int length[3];           // Lengths between color control points
   float moveSpeed;         // Speed of movement (positive = right, negative = left)
   int moveRange[2];        // [min, max] range of movement
   int initialPosition;     // Starting position
   float currentPosition;   // Current position (float for smooth movement)
   bool isEdgeReflect;      // Whether to reflect at edges or wrap around
   int dimmerTime[5];       // [startFadeIn, endFadeIn, startFadeOut, endFadeOut, cycleTime] in ms
   unsigned long startTime; // When this segment was created/started
   int direction;           // Current direction (1 = right, -1 = left)
 };
 

 struct LightEffect {
   int effectID;
   int ledCount;
   int fps;
   LightSegment segments[MAX_SEGMENTS];
   int segmentCount;
 };
 

 void initializeSegment(LightSegment &segment, int segmentID, int initialPosition = 0, int minRange = 0, int maxRange = NUM_LEDS - 1) {
   segment.segmentID = segmentID;
   

   for (int i = 0; i < 4; i++) {
     segment.color[i] = DEFAULT_COLORS[i];
     segment.transparency[i] = DEFAULT_TRANSPARENCY[i];
   }
   

   for (int i = 0; i < 3; i++) {
     segment.length[i] = DEFAULT_LENGTHS[i];
   }
   
   segment.moveSpeed = DEFAULT_MOVE_SPEED;
   segment.moveRange[0] = minRange;
   segment.moveRange[1] = maxRange;
   segment.initialPosition = initialPosition;
   segment.currentPosition = initialPosition;
   segment.isEdgeReflect = false;
   

   for (int i = 0; i < 5; i++) {
     segment.dimmerTime[i] = DEFAULT_DIMMER_TIME[i];
   }
   
   segment.startTime = millis();
   segment.direction = segment.moveSpeed >= 0 ? 1 : -1;
 }
 

 void createRainbowSegment(LightSegment &segment, int segmentID, int initialPosition = 0) {
   initializeSegment(segment, segmentID, initialPosition);
   

   segment.color[0] = 1;  // Red
   segment.color[1] = 3;  // Blue
   segment.color[2] = 2;  // Green
   segment.color[3] = 4;  // Yellow
   
   segment.moveSpeed = 30.0;
   segment.dimmerTime[0] = 0;
   segment.dimmerTime[1] = 100;
   segment.dimmerTime[2] = 4900;
   segment.dimmerTime[3] = 5000;
   segment.dimmerTime[4] = 5000;
 }
 

 void createBreathingSegment(LightSegment &segment, int segmentID, int initialPosition = 0) {
   initializeSegment(segment, segmentID, initialPosition);
   

   segment.color[0] = 7;  // White
   segment.color[1] = 7;  // White
   segment.color[2] = 7;  // White
   segment.color[3] = 7;  // White
   

   segment.moveSpeed = 0.0;
   

   segment.length[0] = 1;
   segment.length[1] = 1;
   segment.length[2] = 1;
   

   segment.dimmerTime[0] = 0;
   segment.dimmerTime[1] = 2000;
   segment.dimmerTime[2] = 2000;
   segment.dimmerTime[3] = 4000;
   segment.dimmerTime[4] = 4000;
 }
 

 void createPoliceLightsSegment(LightSegment &segment, int segmentID, int initialPosition = 0) {
   initializeSegment(segment, segmentID, initialPosition);
   

   segment.color[0] = 1;  // Red
   segment.color[1] = 3;  // Blue
   segment.color[2] = 1;  // Red
   segment.color[3] = 3;  // Blue
   

   segment.moveSpeed = 100.0;
   

   segment.length[0] = 20;
   segment.length[1] = 20;
   segment.length[2] = 20;
   

   segment.dimmerTime[0] = 0;
   segment.dimmerTime[1] = 100;
   segment.dimmerTime[2] = 100;
   segment.dimmerTime[3] = 200;
   segment.dimmerTime[4] = 200;
 }
 

 void createColorWipeSegment(LightSegment &segment, int segmentID, int initialPosition = 0) {
   initializeSegment(segment, segmentID, initialPosition);
   

   segment.color[0] = 0;  // Black
   segment.color[1] = 5;  // Magenta
   segment.color[2] = 0;  // Black
   segment.color[3] = 5;  // Magenta
   

   segment.moveSpeed = 50.0;
   

   segment.length[0] = 50;
   segment.length[1] = 50;
   segment.length[2] = 50;
   

   segment.dimmerTime[0] = 0;
   segment.dimmerTime[1] = 0;
   segment.dimmerTime[2] = 0;
   segment.dimmerTime[3] = 0;
   segment.dimmerTime[4] = 1000;
 }
 

 void createPulseSegment(LightSegment &segment, int segmentID, int initialPosition = 0) {
   initializeSegment(segment, segmentID, initialPosition);
   

   segment.color[0] = 8;  // Orange
   segment.color[1] = 8;  // Orange
   segment.color[2] = 8;  // Orange
   segment.color[3] = 8;  // Orange
   

   segment.moveSpeed = 0.0;
   

   segment.length[0] = 10;
   segment.length[1] = 10;
   segment.length[2] = 10;
   

   segment.dimmerTime[0] = 0;
   segment.dimmerTime[1] = 500;
   segment.dimmerTime[2] = 500;
   segment.dimmerTime[3] = 1000;
   segment.dimmerTime[4] = 1000;
 }
 

 float calculateDimming(const LightSegment &segment) {

   if (segment.dimmerTime[4] <= 0) { // Cycle time
     return 1.0;
   }
   

   unsigned long elapsed = (millis() - segment.startTime) % segment.dimmerTime[4];
   

   if (elapsed < segment.dimmerTime[0]) {

     return 0.0;
   }
   else if (elapsed < segment.dimmerTime[1]) {

     return float(elapsed - segment.dimmerTime[0]) / 
            (segment.dimmerTime[1] - segment.dimmerTime[0]);
   }
   else if (elapsed < segment.dimmerTime[2]) {

     return 1.0;
   }
   else if (elapsed < segment.dimmerTime[3]) {

     return 1.0 - float(elapsed - segment.dimmerTime[2]) / 
            (segment.dimmerTime[3] - segment.dimmerTime[2]);
   }
   else {

     return 0.0;
   }
 }
 

 void processSegment(const LightSegment &segment, CRGB ledBuffer[]) {

   int totalLength = segment.length[0] + segment.length[1] + segment.length[2];
   

   float dimmingFactor = calculateDimming(segment);
   

   int segmentStart = segment.currentPosition;
   int controlPoints[4];
   controlPoints[0] = segmentStart;
   controlPoints[1] = segmentStart + (segment.direction * segment.length[0]);
   controlPoints[2] = controlPoints[1] + (segment.direction * segment.length[1]);
   controlPoints[3] = controlPoints[2] + (segment.direction * segment.length[2]);
   

   for (int ledPos = min(controlPoints[0], controlPoints[3]); 
        ledPos <= max(controlPoints[0], controlPoints[3]); 
        ledPos++) {
     

     if (ledPos < 0 || ledPos >= NUM_LEDS || 
         ledPos < segment.moveRange[0] || ledPos > segment.moveRange[1]) {
       continue;
     }
     

     int sectionIndex = -1;
     for (int i = 0; i < 3; i++) {
       int start = controlPoints[i];
       int end = controlPoints[i+1];
       if ((start <= ledPos && ledPos <= end) || (end <= ledPos && ledPos <= start)) {
         sectionIndex = i;
         break;
       }
     }
     
     if (sectionIndex >= 0) {

       float t;
       int start = controlPoints[sectionIndex];
       int end = controlPoints[sectionIndex + 1];
       
       if (start == end) { // Avoid division by zero
         t = 0;
       } else {
         t = abs(float(ledPos - start) / (end - start));
       }
       

       CRGB color1 = COLOR_MAP[segment.color[sectionIndex]];
       CRGB color2 = COLOR_MAP[segment.color[sectionIndex + 1]];
       

       CRGB blendedColor;
       blendedColor.r = color1.r * (1 - t) + color2.r * t;
       blendedColor.g = color1.g * (1 - t) + color2.g * t;
       blendedColor.b = color1.b * (1 - t) + color2.b * t;
       

       float trans1 = segment.transparency[sectionIndex];
       float trans2 = segment.transparency[sectionIndex + 1];
       float transparency = trans1 * (1 - t) + trans2 * t;
       

       transparency *= dimmingFactor;
       

       if (transparency < 1.0) {

         float blendRatio = 1.0 - transparency;
         

         ledBuffer[ledPos].r = (ledBuffer[ledPos].r * transparency) + (blendedColor.r * blendRatio);
         ledBuffer[ledPos].g = (ledBuffer[ledPos].g * transparency) + (blendedColor.g * blendRatio);
         ledBuffer[ledPos].b = (ledBuffer[ledPos].b * transparency) + (blendedColor.b * blendRatio);
       }
     }
   }
 }
 

 void updateSegmentPosition(LightSegment &segment, float dt) {

   float delta = segment.moveSpeed * dt;
   segment.currentPosition += delta;
   

   if (segment.isEdgeReflect) {
     if (segment.currentPosition < segment.moveRange[0]) {
       float overshoot = segment.moveRange[0] - segment.currentPosition;
       segment.currentPosition = segment.moveRange[0] + overshoot;
       segment.moveSpeed = abs(segment.moveSpeed);
       segment.direction = 1;
     }
     else if (segment.currentPosition > segment.moveRange[1]) {
       float overshoot = segment.currentPosition - segment.moveRange[1];
       segment.currentPosition = segment.moveRange[1] - overshoot;
       segment.moveSpeed = -abs(segment.moveSpeed);
       segment.direction = -1;
     }
   }
   else {

     if (segment.currentPosition < segment.moveRange[0]) {
       segment.currentPosition = segment.moveRange[1] - 
         fmod(segment.moveRange[0] - segment.currentPosition, 
             segment.moveRange[1] - segment.moveRange[0] + 1);
     }
     else if (segment.currentPosition > segment.moveRange[1]) {
       segment.currentPosition = segment.moveRange[0] + 
         fmod(segment.currentPosition - segment.moveRange[1], 
             segment.moveRange[1] - segment.moveRange[0] + 1);
     }
   }
 }
 

 LightSegment* findSegmentById(LightEffect &effect, int segmentID) {
   for (int i = 0; i < effect.segmentCount; i++) {
     if (effect.segments[i].segmentID == segmentID) {
       return &effect.segments[i];
     }
   }
   return NULL;
 }
 

 bool addSegmentToEffect(LightEffect &effect, const LightSegment &segment) {
   if (effect.segmentCount >= MAX_SEGMENTS) {
     return false;
   }
   
   effect.segments[effect.segmentCount] = segment;
   effect.segmentCount++;
   return true;
 }
 

 bool removeSegmentFromEffect(LightEffect &effect, int segmentID) {

   int index = -1;
   for (int i = 0; i < effect.segmentCount; i++) {
     if (effect.segments[i].segmentID == segmentID) {
       index = i;
       break;
     }
   }
   
   if (index == -1) {
     return false;
   }
   

   for (int i = index; i < effect.segmentCount - 1; i++) {
     effect.segments[i] = effect.segments[i + 1];
   }
   
   effect.segmentCount--;
   return true;
 }
 

 void updateAllSegments(LightEffect &effect) {
   float dt = 1.0 / effect.fps;
   
   for (int i = 0; i < effect.segmentCount; i++) {
     updateSegmentPosition(effect.segments[i], dt);
   }
 }
 

 void applyEffectToLEDs(const LightEffect &effect, CRGB ledBuffer[]) {

   for (int i = 0; i < effect.ledCount; i++) {
     ledBuffer[i] = CRGB::Black;
   }
   

   for (int i = 0; i < effect.segmentCount; i++) {
     processSegment(effect.segments[i], ledBuffer);
   }
 }
 
 #endif 