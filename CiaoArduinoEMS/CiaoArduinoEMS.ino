/*
  Arduino Ciao example
  
 This sketch uses ciao xmpp connector. It sends back “hello world” message to the xmpp client when receives “ciao” from it. 
  
 Be sure to set the xmpp client in the "USER" field used to receive the response by MCU.

 Possible commands to send from the xmpp client:
 * "ciao"               -> random answers in 5 different languages
 
 created September 2015
 by andrea[at]arduino[dot]org
 
 
  NOTE: be sure to activate and configure xmpp connector on Linino OS
       http://labs.arduino.org/Ciao
   
 */
 
#include <Ciao.h>

String USER="user@domain";
String mess[5]={"Hi, I am MCU :-P","hallo , ik ben MCU :-P","bonjour, je suis MCU :-P","Ciao, io sono MCU :-P","Kon'nichiwa, watashi wa MCU yo :-P" };

void setup() {
  SERIAL_PORT_USBVIRTUAL.begin(57600);
  SERIAL_PORT_USBVIRTUAL.println("MONKEY");
  Ciao.begin(); 
}

void loop() {
  CiaoData data = Ciao.read("ems");  
  
  if(!data.isEmpty()){
    String id = data.get(0);
    SERIAL_PORT_USBVIRTUAL.println("id: " + id);
    String sender = data.get(1);
    SERIAL_PORT_USBVIRTUAL.println("sender: " + sender);
    String message = data.get(2);
    SERIAL_PORT_USBVIRTUAL.println("message: " + message);
    
    message.toLowerCase();
    if(message == "ciao" )
      Ciao.write("xmpp", USER,mess[random(0,5)]);
  }
}

