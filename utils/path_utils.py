import os
import sys

def _search_roots():
    if getattr(sys, 'frozen', False):

        roots = [os.path.dirname(os.path.abspath(sys.executable))]
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            roots.append(meipass)
        return roots

    return [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]

def user_data_dir():
    'Return the writable application data folder for the current platform.'
    if os.name == 'nt':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
    elif sys.platform == 'darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME') or os.path.join(
            os.path.expanduser('~'), '.local', 'share')
    return os.path.join(base, 'ReelsMakerPro')

def resource_path(relative_path):
    roots = _search_roots()
    for root in roots:
        candidate = os.path.join(root, relative_path)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(roots[0], relative_path)
