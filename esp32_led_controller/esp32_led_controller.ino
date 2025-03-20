#include <WiFi.h>
#include <WiFiUdp.h>
#include <EEPROM.h>
#include <ArduinoOSC.h>
#include <FastLED.h>
#include <ESPAsyncWebServer.h>
#include <DNSServer.h>
#include <AsyncTCP.h>
#include <ArduinoJson.h>

#include "config.h"       
#include "led_helpers.h"   
#include "osc_handlers.h"  
 

 CRGB leds[NUM_LEDS];
 WiFiUDP udp;
 OscWiFi osc;
 DNSServer dnsServer;
 AsyncWebServer server(WEB_SERVER_PORT);
 

 unsigned long btnPressStartTime = 0;
 bool btnPressed = false;
 

 enum OperationMode {
   MODE_CONFIG,   // AP mode for configuration
   MODE_NORMAL    // Normal operation mode
 };
 OperationMode currentMode = MODE_NORMAL;
 

 struct WifiCredentials {
   char ssid[32];
   char password[64];
   bool configured;
 };
 WifiCredentials wifiCreds;
 

 LightEffect currentEffect;
 

 void setupLEDs();
 void setupButton();
 void checkButton();
 bool loadWifiCredentials();
 void saveWifiCredentials();
 void eraseWifiCredentials();
 bool connectToWifi();
 void startConfigPortal();
 void setupOSC();
 void setupWebServer();
 void handleWebRequests();
 void updateLEDs();
 String scanNetworks();
 

 void setup() {
   Serial.begin(115200);
   Serial.println("\n\nLED Controller Starting...");
   

   EEPROM.begin(EEPROM_SIZE);
   

   setupLEDs();
   

   setupButton();
   

   initializeEffect();
   

   if (loadWifiCredentials() && wifiCreds.configured) {

     if (connectToWifi()) {

       currentMode = MODE_NORMAL;
       setupOSC();
       Serial.println("Running in normal mode");
     } else {

       currentMode = MODE_CONFIG;
       startConfigPortal();
       Serial.println("Failed to connect to WiFi, starting config portal");
     }
   } else {

     currentMode = MODE_CONFIG;
     startConfigPortal();
     Serial.println("No WiFi configured, starting config portal");
   }
 }
 

 void loop() {

   checkButton();
   
   if (currentMode == MODE_CONFIG) {

     dnsServer.processNextRequest();
   } else {

     osc.parse();
   }
   

   updateLEDs();
   

   delay(1);
 }
 

 void setupLEDs() {
   FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
   FastLED.setBrightness(MAX_BRIGHTNESS);
   FastLED.clear();
   FastLED.show();
   

   for (int i = 0; i < NUM_LEDS; i++) {
     leds[i] = CRGB::Blue;
     FastLED.show();
     delay(20);
   }
   FastLED.clear();
   FastLED.show();
 }
 

 void setupButton() {
   pinMode(RESET_BTN_PIN, INPUT_PULLUP);
 }
 

 void checkButton() {
   bool currentBtnState = digitalRead(RESET_BTN_PIN) == LOW;
   

   if (currentBtnState && !btnPressed) {
     btnPressed = true;
     btnPressStartTime = millis();
   }

   else if (!currentBtnState && btnPressed) {
     btnPressed = false;
   }
   

   if (btnPressed && (millis() - btnPressStartTime > LONG_PRESS_TIME)) {
     Serial.println("Long press detected, resetting WiFi settings...");
     

     for (int i = 0; i < 5; i++) {
       fill_solid(leds, NUM_LEDS, CRGB::Red);
       FastLED.show();
       delay(200);
       FastLED.clear();
       FastLED.show();
       delay(200);
     }
     

     eraseWifiCredentials();
     

     ESP.restart();
   }
 }
 

 void initializeEffect() {
   currentEffect.effectID = 1;
   currentEffect.ledCount = NUM_LEDS;
   currentEffect.fps = DEFAULT_FPS;
   currentEffect.segmentCount = 0;
   

   LightSegment defaultSegment;
   createRainbowSegment(defaultSegment, 1, 0);
   addSegmentToEffect(currentEffect, defaultSegment);
 }
 

 bool loadWifiCredentials() {
   EEPROM.get(0, wifiCreds);
   

   if (wifiCreds.ssid[0] == 0xFF) {
     wifiCreds.configured = false;
     return false;
   }
   
   Serial.print("Loaded SSID: ");
   Serial.println(wifiCreds.ssid);
   return true;
 }
 

 void saveWifiCredentials() {
   wifiCreds.configured = true;
   EEPROM.put(0, wifiCreds);
   EEPROM.commit();
   Serial.println("WiFi credentials saved");
 }
 

 void eraseWifiCredentials() {
   wifiCreds.configured = false;
   wifiCreds.ssid[0] = 0;
   wifiCreds.password[0] = 0;
   EEPROM.put(0, wifiCreds);
   EEPROM.commit();
   Serial.println("WiFi credentials erased");
 }
 

 bool connectToWifi() {
   if (!wifiCreds.configured) {
     return false;
   }
   
   Serial.print("Connecting to ");
   Serial.println(wifiCreds.ssid);
   

   for (int i = 0; i < NUM_LEDS; i++) {
     leds[i] = CRGB::Blue;
     leds[i].fadeToBlackBy(180);
   }
   FastLED.show();
   
   WiFi.mode(WIFI_STA);
   WiFi.begin(wifiCreds.ssid, wifiCreds.password);
   
   unsigned long startTime = millis();
   while (WiFi.status() != WL_CONNECTED) {

     if (millis() - startTime > WIFI_TIMEOUT) {
       Serial.println("Failed to connect to WiFi");
       return false;
     }
     

     uint8_t brightness = (sin8(millis() / 10) * 128) / 255 + 20;
     fill_solid(leds, NUM_LEDS, CRGB(0, 0, brightness));
     FastLED.show();
     
     delay(100);
   }
   
   Serial.println("Connected to WiFi");
   Serial.print("IP address: ");
   Serial.println(WiFi.localIP());
   

   for (int i = 0; i < 3; i++) {
     fill_solid(leds, NUM_LEDS, CRGB::Green);
     FastLED.show();
     delay(100);
     FastLED.clear();
     FastLED.show();
     delay(100);
   }
   
   return true;
 }
 

 void startConfigPortal() {

   uint8_t mac[6];
   WiFi.macAddress(mac);
   char apName[32];
   sprintf(apName, "%s%02X%02X", AP_NAME, mac[4], mac[5]);
   

   WiFi.mode(WIFI_AP);
   WiFi.softAP(apName, AP_PASSWORD);
   

   IPAddress myIP = WiFi.softAPIP();
   Serial.print("AP IP address: ");
   Serial.println(myIP);
   

   dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
   dnsServer.start(DNS_PORT, "*", myIP);
   

   setupWebServer();
   

   for (int i = 0; i < NUM_LEDS; i += 5) {
     leds[i] = CRGB::Yellow;
   }
   FastLED.show();
   
   Serial.println("Configuration portal started");
 }
 

 void setupOSC() {

   udp.begin(OSC_PORT);
   

   osc.begin(udp, OSC_PORT);
   

   setupOscHandlers(osc, currentEffect);
   
   Serial.print("OSC server listening on port ");
   Serial.println(OSC_PORT);
 }
 

 void setupWebServer() {

   server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
     String html = R"(
     <!DOCTYPE html>
     <html>
     <head>
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>LED Controller WiFi Setup</title>
       <style>
         body {
           font-family: Arial, sans-serif;
           margin: 0;
           padding: 20px;
           background-color: #121212;
           color: #ffffff;
         }
         .container {
           max-width: 500px;
           margin: 0 auto;
           background-color: #1e1e1e;
           padding: 20px;
           border-radius: 8px;
           box-shadow: 0 4px 8px rgba(0,0,0,0.2);
         }
         h1 {
           color: #2196F3;
           text-align: center;
           margin-bottom: 20px;
         }
         .form-group {
           margin-bottom: 15px;
         }
         label {
           display: block;
           margin-bottom: 5px;
           font-weight: bold;
           color: #bbbbbb;
         }
         input[type="text"], input[type="password"] {
           width: 100%;
           padding: 10px;
           border: 1px solid #444;
           border-radius: 4px;
           background-color: #333;
           color: #fff;
           box-sizing: border-box;
         }
         input[type="text"]:focus, input[type="password"]:focus {
           border-color: #2196F3;
           outline: none;
         }
         button {
           background-color: #2196F3;
           color: white;
           border: none;
           padding: 10px 15px;
           text-align: center;
           border-radius: 4px;
           cursor: pointer;
           width: 100%;
           font-size: 16px;
           margin-top: 10px;
         }
         button:hover {
           background-color: #0b7dda;
         }
         .networks {
           margin-top: 20px;
           max-height: 200px;
           overflow-y: auto;
         }
         .network-item {
           padding: 10px;
           background-color: #333;
           margin-bottom: 8px;
           border-radius: 4px;
           cursor: pointer;
         }
         .network-item:hover {
           background-color: #444;
         }
         .signal {
           float: right;
           margin-left: 10px;
         }
         .status {
           text-align: center;
           margin-top: 15px;
           color: #ff9800;
         }
         @media screen and (max-width: 480px) {
           body {
             padding: 10px;
           }
           .container {
             padding: 15px;
           }
         }
       </style>
     </head>
     <body>
       <div class="container">
         <h1>LED Controller Setup</h1>
         <div class="status" id="status">Scan for available networks</div>
         
         <div class="form-group">
           <label for="ssid">WiFi Network:</label>
           <input type="text" id="ssid" name="ssid" placeholder="Enter SSID">
         </div>
         
         <div class="form-group">
           <label for="password">Password:</label>
           <input type="password" id="password" name="password" placeholder="Enter password">
         </div>
         
         <button id="connect">Connect</button>
         <button id="scan" style="background-color: #ff9800; margin-top: 5px;">Scan Networks</button>
         
         <div class="networks" id="networks"></div>
       </div>
       
       <script>

         document.getElementById('connect').addEventListener('click', function() {
           const ssid = document.getElementById('ssid').value;
           const password = document.getElementById('password').value;
           
           if (!ssid) {
             alert('Please enter SSID');
             return;
           }
           
           document.getElementById('status').innerText = 'Connecting...';
           
           fetch('/connect', {
             method: 'POST',
             headers: {
               'Content-Type': 'application/json',
             },
             body: JSON.stringify({ ssid, password }),
           })
           .then(response => response.json())
           .then(data => {
             document.getElementById('status').innerText = data.message;
             if (data.success) {
               document.getElementById('status').style.color = '#4caf50';
               setTimeout(() => {
                 window.location.href = '/success';
               }, 3000);
             } else {
               document.getElementById('status').style.color = '#f44336';
             }
           })
           .catch(error => {
             document.getElementById('status').innerText = 'Connection error';
             document.getElementById('status').style.color = '#f44336';
           });
         });
         

         document.getElementById('scan').addEventListener('click', function() {
           document.getElementById('status').innerText = 'Scanning...';
           document.getElementById('networks').innerHTML = '';
           
           fetch('/scan')
           .then(response => response.json())
           .then(data => {
             if (data.networks && data.networks.length > 0) {
               document.getElementById('status').innerText = 'Select a network';
               const networksDiv = document.getElementById('networks');
               
               data.networks.forEach(network => {
                 const div = document.createElement('div');
                 div.className = 'network-item';
                 div.innerHTML = network.ssid + '<span class="signal">Signal: ' + network.rssi + 'dBm</span>';
                 div.addEventListener('click', function() {
                   document.getElementById('ssid').value = network.ssid;
                 });
                 networksDiv.appendChild(div);
               });
             } else {
               document.getElementById('status').innerText = 'No networks found';
             }
           })
           .catch(error => {
             document.getElementById('status').innerText = 'Scan failed';
           });
         });
         

         window.addEventListener('load', function() {
           document.getElementById('scan').click();
         });
       </script>
     </body>
     </html>
     )";
     
     request->send(200, "text/html", html);
   });
   

   server.on("/scan", HTTP_GET, [](AsyncWebServerRequest *request) {
     String json = scanNetworks();
     request->send(200, "application/json", json);
   });
   

   server.on("/connect", HTTP_POST, [](AsyncWebServerRequest *request) {

     request->send(200, "application/json", "{\"message\":\"Processing request\",\"success\":false}");
   }, NULL, [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {

     DynamicJsonDocument jsonDoc(512);
     deserializeJson(jsonDoc, data, len);
     
     String ssid = jsonDoc["ssid"].as<String>();
     String password = jsonDoc["password"].as<String>();
     

     strncpy(wifiCreds.ssid, ssid.c_str(), sizeof(wifiCreds.ssid) - 1);
     strncpy(wifiCreds.password, password.c_str(), sizeof(wifiCreds.password) - 1);
     wifiCreds.ssid[sizeof(wifiCreds.ssid) - 1] = '\0';
     wifiCreds.password[sizeof(wifiCreds.password) - 1] = '\0';
     

     saveWifiCredentials();
     

     bool connected = connectToWifi();
     

     DynamicJsonDocument responseDoc(256);
     responseDoc["success"] = connected;
     responseDoc["message"] = connected ? "Connected successfully!" : "Failed to connect";
     
     String response;
     serializeJson(responseDoc, response);
     

     if (connected) {
       delay(1000);
       ESP.restart();
     }
   });
   

   server.on("/success", HTTP_GET, [](AsyncWebServerRequest *request) {
     String html = R"(
     <!DOCTYPE html>
     <html>
     <head>
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Connection Successful</title>
       <style>
         body {
           font-family: Arial, sans-serif;
           margin: 0;
           padding: 20px;
           background-color: #121212;
           color: #ffffff;
           text-align: center;
         }
         .container {
           max-width: 500px;
           margin: 0 auto;
           background-color: #1e1e1e;
           padding: 20px;
           border-radius: 8px;
           box-shadow: 0 4px 8px rgba(0,0,0,0.2);
         }
         h1 {
           color: #4caf50;
         }
         p {
           margin: 20px 0;
           line-height: 1.5;
         }
         .ip {
           background-color: #333;
           padding: 10px;
           border-radius: 4px;
           font-family: monospace;
           margin: 20px 0;
         }
       </style>
     </head>
     <body>
       <div class="container">
         <h1>Connected Successfully!</h1>
         <p>Your LED Controller is now connected to the WiFi network.</p>
         <p>The device will restart in a few seconds and connect to your network.</p>
         <p>IP Address:</p>
         <div class="ip">)" + WiFi.localIP().toString() + R"(</div>
         <p>The configuration mode will be disabled until you press the reset button for 10 seconds.</p>
       </div>
     </body>
     </html>
     )";
     
     request->send(200, "text/html", html);
   });
   

   server.on("/status", HTTP_GET, [](AsyncWebServerRequest *request) {
     DynamicJsonDocument doc(256);
     doc["connected"] = (WiFi.status() == WL_CONNECTED);
     doc["ip"] = WiFi.localIP().toString();
     doc["ssid"] = WiFi.SSID();
     
     String response;
     serializeJson(doc, response);
     request->send(200, "application/json", response);
   });
   

   server.onNotFound([](AsyncWebServerRequest *request) {
     request->redirect("/");
   });
   

   server.begin();
   Serial.println("Web server started");
 }
 

 String scanNetworks() {
   Serial.println("Scanning WiFi networks...");
   

   for (int i = 0; i < NUM_LEDS; i++) {
     leds[i] = CRGB::Blue;
     FastLED.show();
     delay(5);
     leds[i] = CRGB::Black;
   }
   
   int numNetworks = WiFi.scanNetworks();
   Serial.print("Found ");
   Serial.print(numNetworks);
   Serial.println(" networks");
   
   DynamicJsonDocument doc(4096);
   JsonArray networksArray = doc.createNestedArray("networks");
   
   for (int i = 0; i < numNetworks; i++) {
     JsonObject network = networksArray.createNestedObject();
     network["ssid"] = WiFi.SSID(i);
     network["rssi"] = WiFi.RSSI(i);
     network["encryption"] = WiFi.encryptionType(i) != WIFI_AUTH_OPEN;
   }
   
   String result;
   serializeJson(doc, result);
   return result;
 }
 

 void updateLEDs() {

   updateAllSegments(currentEffect);
   

   CRGB ledBuffer[NUM_LEDS];
   

   applyEffectToLEDs(currentEffect, ledBuffer);
   

   for (int i = 0; i < NUM_LEDS; i++) {
     leds[i] = ledBuffer[i];
   }
   

   FastLED.show();
 }