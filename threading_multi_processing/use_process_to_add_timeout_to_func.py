import socket
from multiprocessing import Process, Queue


def reslove(hostname, timeout=500):
    exitcode, ip = resolve_host(hostname, timeout)
    if exitcode == 0:
        return ip
    else:
        return hostname


def resolve_host(hostname, timeout):
    queue = Queue()
    proc = Process(target=gethostbyname, args=(hostname, queue))
    proc.start()
    proc.join(timeout=timeout)

    if queue.empty():
        proc.terminate()
        ip = None
    else:
        ip = queue.get()
    return proc.exitcode, ip


def gethostbyname(hostname, queue):
    ip = socket.gethostbyname(hostname)
    queue.put(ip)


print('GO')
resolved = reslove('abv.bg', 0.1)
print(resolved)