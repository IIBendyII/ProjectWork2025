import multiprocessing

bind = "0.0.0.0:8000" # Da cambiare porta 8000 con la porta 443 a progetto finito
workers = multiprocessing.cpu_count() * 2 + 1 # Per Gunicorn documentation: workers = (2 × CPU cores) + 1.
threads = 2 # Threads aggiunti nel caso il DB Gestionale impieghi tempo a rispondere
worker_tmp_dir = "/tmp"
log_file = "-"
control_socket_disable = True