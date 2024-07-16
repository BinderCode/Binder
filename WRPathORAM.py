import os
import random
import shutil
import time
import csv
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class TreeNode:
    def __init__(self):
        self.blocks = [None] * 4 

class WRPathORAM:
    def __init__(self, depth, storage_dir):
        self.depth = depth  
        self.tree_size = 2 ** (depth + 1) - 1
        self.tree = [TreeNode() for _ in range(self.tree_size)]
        self.position_map = {}
        self.storage_dir = storage_dir
        self.reset_storage()

    def reset_storage(self):
        shutil.rmtree(self.storage_dir, ignore_errors=True)
        os.makedirs(self.storage_dir, exist_ok=True)
        for i in range(self.tree_size):
            node_path = os.path.join(self.storage_dir, str(i))
            os.makedirs(node_path, exist_ok=True)
            for j in range(1, 5):
                os.makedirs(os.path.join(node_path, str(j)), exist_ok=True)
        print("Storage reset completed.")

    def _get_path(self, leaf):
        path = []
        node_idx = leaf
        while node_idx > 0:
            path.append(node_idx)
            node_idx = (node_idx - 1) // 2
        path.append(0)
        print(f"Path for leaf {leaf}: {path}")
        return path

    def random_leaf(self):
        leaf_start = 2 ** self.depth - 1
        leaf_end = self.tree_size - 1
        leaf = random.randint(leaf_start, leaf_end)
        print(f"Random leaf chosen: {leaf}")
        return leaf

    def accesswrite(self, new_data, filename):
        self.reset_storage()
        chosen_block_idx = random.randint(1, 4)
        if filename not in self.position_map:
            self.position_map[filename] = (self.random_leaf(), chosen_block_idx)
        leaf, block_idx = self.position_map[filename]
        print(f"Position map: {self.position_map}")
        path = self._get_path(leaf)
        chosen_node_idx = random.choice(path)
        self.position_map[filename] = (chosen_node_idx, chosen_block_idx)
        for node_idx in path:
            node_path = os.path.join(self.storage_dir, str(node_idx))
            for idx in range(1, 5):
                if node_idx == chosen_node_idx and idx == chosen_block_idx:
                    block_path = os.path.join(node_path, str(idx), filename)
                    data_to_write = new_data
                    print(f"Writing real data to {block_path}")
                else:
                    block_path = os.path.join(node_path, str(idx), f'fake_data_block_{filename}')
                    data_to_write = os.urandom(len(new_data))
                    print(f"Writing fake data to {block_path}")
                with open(block_path, 'wb') as f:
                    f.write(data_to_write)
        return self.position_map

    def accessread(self, position_map, filename):
        if filename not in position_map:
            raise Exception("File name not found in position map")
        leaf, block_idx = position_map[filename]
        path = self._get_path(leaf)
        data_block = None
        for node_idx in path:
            node_path = os.path.join(self.storage_dir, str(node_idx))
            for idx in range(1, 5):
                block_path = os.path.join(node_path, str(idx), filename if idx == block_idx and node_idx == leaf else f'fake_data_block_{filename}')
                if os.path.exists(block_path):
                    with open(block_path, 'rb') as f:
                        data = f.read()
                        if idx == block_idx and node_idx == leaf:
                            data_block = data
                else:
                    fake_block_path = os.path.join(node_path, str(idx), f'fake_data_block_{filename}')
                    if os.path.exists(fake_block_path):
                        with open(fake_block_path, 'rb') as f:
                            data = f.read()
        if data_block is None:
            raise Exception("Data block not found")
        return data_block

def encrypt_data(data, key):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(data) + encryptor.finalize()
    print("Data encrypted.")
    return iv + encrypted_data

def decrypt_data(encrypted_data, key):
    iv = encrypted_data[:16]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data[16:]) + decryptor.finalize()
    print("Data decrypted.")
    return decrypted_data

def main():
    storage_directory = 'home1'
    key = os.urandom(16)
    model_file_path = 'federated_model.pt'
    csv_file_path = 'WRPathORAM_times.csv'
    write_times = []
    read_times = []
    try:
        with open(model_file_path, 'rb') as file:
            model_data = file.read()
            print("Model data read from file.")
        encrypted_model_data = encrypt_data(model_data, key)
        cumulative_write_time = 0
        cumulative_read_time = 0
        for i in range(100):
            oram = WRPathORAM(depth=3, storage_dir=storage_directory)
            start_time = time.time()
            position_map = oram.accesswrite(encrypted_model_data, 'Fi')
            end_time = time.time()
            write_time = end_time - start_time
            cumulative_write_time += write_time
            write_times.append(cumulative_write_time)
            print(f"Iteration {i+1}: Cumulative Write time: {cumulative_write_time:.2f} seconds")
            start_time = time.time()
            data_block = oram.accessread(position_map, 'Fi')
            end_time = time.time()
            read_time = end_time - start_time
            cumulative_read_time += read_time
            read_times.append(cumulative_read_time)
            print(f"Iteration {i+1}: Cumulative Read time: {cumulative_read_time:.2f} seconds")
        with open(csv_file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Iteration', 'Cumulative Write Time (seconds)', 'Cumulative Read Time (seconds)'])
            for i in range(100):
                csv_writer.writerow([i + 1, f"{write_times[i]:.2f}", f"{read_times[i]:.2f}"])
        print(f"Operation times saved to {csv_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
