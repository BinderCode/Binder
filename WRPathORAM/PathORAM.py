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

class PathORAM:
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

    def _get_random_leaf(self):
        leaf_start = 2 ** self.depth - 1
        leaf_end = self.tree_size - 1
        leaf = random.randint(leaf_start, leaf_end)
        print(f"Random leaf chosen: {leaf}")
        return leaf

    def access(self, block_id, new_data):
        if block_id not in self.position_map:
            self.position_map[block_id] = (self._get_random_leaf(), random.randint(1, 4))

        leaf, block_idx = self.position_map[block_id]
        print(f"Position map: {self.position_map}")
        path = self._get_path(leaf)
        chosen_node_idx = random.choice(path)
        chosen_block_idx = random.randint(1, 4)
        for node_idx in path:
            node_path = os.path.join(self.storage_dir, str(node_idx))
            for idx in range(1, 5):
                block_path = os.path.join(node_path, str(idx), f'real_data_block_{block_id}' if node_idx == chosen_node_idx and idx == chosen_block_idx else f'fake_data_block_{block_id}')
                data_to_write = new_data if node_idx == chosen_node_idx and idx == chosen_block_idx else os.urandom(len(new_data))
                with open(block_path, 'wb') as f:
                    f.write(data_to_write)

        for node_idx in path:
            node_path = os.path.join(self.storage_dir, str(node_idx))
            for idx in range(1, 5):
                block_path = os.path.join(node_path, str(idx), f'real_data_block_{block_id}' if node_idx == leaf and idx == block_idx else f'fake_data_block_{block_id}')
                if os.path.exists(block_path):
                    with open(block_path, 'rb') as f:
                        data = f.read()

        return self.position_map, data

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
    csv_file_path = 'PathORAM_times.csv'

    times = []
    total_elapsed_time = 0
    try:
        with open(model_file_path, 'rb') as file:
            model_data = file.read()
            print("Model data read from file.")

        encrypted_model_data = encrypt_data(model_data, key)

        for i in range(100):
            oram = PathORAM(depth=3, storage_dir=storage_directory)

            start_time = time.time()
            position_map, data = oram.access(1, encrypted_model_data)
            end_time = time.time()

            elapsed_time = end_time - start_time
            total_elapsed_time += elapsed_time
            times.append(total_elapsed_time)

            print(f"Iteration {i + 1}: Storage time: {elapsed_time:.3f} seconds")
            print(f"Position map: {position_map}")

        with open(csv_file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Iteration', 'Time (seconds)'])
            for i, t in enumerate(times, 1):
                csv_writer.writerow([i, t])

        print(f"Storage times saved to {csv_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
