---
title: 'Microharp: A Harp protocol and device application framework MicroPython package'
tags:
  - MicroPython
  - Raspberry Pi Pico
  - Harp protocol
  - Bonsai
authors:
  - name: Gordon L. Mills
    corresponding: true
    affiliation: 1
affiliations:
 - name: Sainsbury Wellcome Centre, UK
   index: 1
date: 20 December 2022
bibliography: paper.bib
---

# Summary

Experimental science often requires the acquisition of sensor data and control of stimulus, using various devices. In general, these devices are coordinated using a platform on which the experiment is built. Typically, the platform hardware is a PC and the platform software is a graphical or text-based high-level programming language. Common to all such systems is the requirement to transact data between the platform and one or more, possibly custom hardware devices.


# Statement of need

The ubiquity of single board microcomputers has reduced the hardware development effort required to realise custom devices. However, a significant amount of software development is still required. `Microharp` is a MicroPython package for creating custom devices which implement the Harp data and timing protocols [@harp]. These protocols are designed with the requirements of experimental science in mind and are supported by the Bonsai platform [@bonsai]. `Microharp` targets the Raspberry Pi Pico, a versatile low-cost microcontroller board, which supports the MicroPython programming language. `MicroHarp` has been designed to be used by researchers and students wishing to create devices for their experiments. The package handles all communication with the platform data and synchronisation interfaces. Its class-based framework implements common device features whilst providing an intuitive interface for device customisation. The package has been used to develop a number of custom devices which are currently in experimental neuroscience research use. The combination of low-cost target hardware, use of a programming language familiar to many researchers and students, and the simplicity of device customisation afforded by `Microharp` will continue to accelerate the realisation of custom experimental apparatus.


# Acknowledgements

Thanks to Andre Almeida and Bruno Cruz for creation of Bonsai test workflows and performance benchmarking of the package.


# References
