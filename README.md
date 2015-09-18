##Arduino Ciao (CPU/MIPS side)
Simple but effective library in Python to make MCU communicate with "outside World".

###What is Arduino Ciao?

**Arduino Ciao** is a easy-to-use and powerful technology that enables Arduino sketches to communicate intuitively with the "outside World". It aims to simplify interaction between microcontroller and Linino OS allowing a variety of connections with most common protocols, third-party services and social networks.

Arduino Ciao is open-source and distributed under GNU license: feel free to read it, suggest improvements, provide feedbacks and develop new features.

More information about Arduino Ciao project can be found at http://labs.arduino.org/Ciao

###Arduino Ciao (CPU/MIPS side) - Ciao Core

Arduino Ciao is made of two main parts:
 * the [Ciao Library](http://labs.arduino.org/Ciao+MCU) - usable inside *sketches*, it''s written in C (source code available [here](https://github.com/arduino-org/CiaoMCU))
 * the **Ciao Core** - a library developed in python that runs on the CPU/MIPS side of the board.

**Ciao Core** has been developed to be largely configurable and modular: everyone can develop new modules (we call them *connectors*) to allow the MCU to interact with new network protocols, third-party services or platforms. 

To understand better the **Ciao Core** architecture and settings please visit: http://labs.arduino.org/Ciao+CPU
