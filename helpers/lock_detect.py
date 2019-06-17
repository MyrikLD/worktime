import psutil


def is_locked(pids_data={'lock_pid': None, 'last_pids': set()}):
    pids = set(psutil.pids())
    if pids_data.get('lock_pid'):
        if pids_data['lock_pid'] in pids:
            return True
        else:
            pids_data['lock_pid'] = None
            pids_data['last_pids'] = pids
            return False

    for pid in pids - pids_data['last_pids']:
        try:
            path = f'/proc/{pid}/cmdline'
            with open(path, 'rb') as f:
                data = f.read().replace(b'\x00', b' ').decode()
            if 'i3lock' in data:
                pids_data['lock_pid'] = pid
                pids_data['last_pids'] = pids
                return True
        except IOError: # proc has already terminated
            continue

    pids_data['last_pids'] = pids
    return False