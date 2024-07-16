# Binder
Binder_WRPathORAM

**Install**

`pip install cryptography`

The **pathoram.py** file is the PathORAM program, which records the time required to read and write the model 100 times, saving the time in PathORAM_times.csv.

The **WRPathORAM.py** file is a WPathORAM+WPathORAM algorithm. The program records the time required to read and write the model 100 times, and saves the time in WRPathORAM_times.csv.



storage_directory = 'home1'   is the path for saving the  federated learning encryption model (Fi).

model_file_path = 'federated_model.pt'   is the name of  the encryption Fi.

csv_file_path = 'WRPathORAM_times.csv' is the runtime saving path.



