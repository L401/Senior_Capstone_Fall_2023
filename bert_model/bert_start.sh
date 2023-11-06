#!/bin/bash
bert-serving-start -num_worker=1 -model_dir model/cased_L-12_H-768_A-12/ -port 5555 -port_out 5556