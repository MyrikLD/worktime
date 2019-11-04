import psutil

_pids_data = {'lock_pid': None, 'last_pids': set()}


def is_locked(lock_name='i3lock') -> bool:
    pids = set(psutil.pids())

    if _pids_data['lock_pid']:
        if _pids_data['lock_pid'] in pids:
            return True
        else:
            _pids_data['lock_pid'] = None
            _pids_data['last_pids'] = pids
            return False

    new_pids = pids - _pids_data['last_pids']

    for pid in new_pids:
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                cmdline = f.read().replace(b'\x00', b' ').decode()
            if lock_name in cmdline:
                _pids_data['lock_pid'] = pid
                _pids_data['last_pids'] = pids
                return True
        except IOError:  # proc has already terminated
            continue

    _pids_data['last_pids'] = pids
    return False
