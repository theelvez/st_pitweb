import os
import time
import paramiko
import sys
#from time import ctime

identity_file_path = "C:\\repos\\identity\\svtdf_results_id_ed25519"
local_path_to_results = "C:\\repos\\st_pitweb\\ops-service\\results\\results.html"
remote_path_to_results = "./files/results.html"
polling_interval_in_sec = 3
username = "sunvalleytourdeforce"
host = "52.34.167.20"
port = 22

def upload_new_results(local_path, remote_path):
    print(f"[{time.ctime(time.time())}] Uploading {local_path} to {remote_path}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, username=username, key_filename=identity_file_path)

    #transport = paramiko.Transport((host, port))
    #transport.connect(username = username, key_filename)

    sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    sftp.put(local_path, remote_path)
    sftp.close()

    ssh.close()
    print(f".... success")
    return
    

def watch_file(local_path, remote_path, interval_in_sec=1):
    last_modified = os.path.getmtime(local_path)
    while True:
        new_modified = os.path.getmtime(local_path)
        #print("polling...")
        if new_modified != last_modified:
            last_modified = new_modified
            upload_new_results(local_path, remote_path)
        time.sleep(interval_in_sec)

upload_new_results(local_path_to_results, remote_path_to_results)
watch_file(local_path_to_results, remote_path_to_results, polling_interval_in_sec)